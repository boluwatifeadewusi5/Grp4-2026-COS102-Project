import csv
import hashlib
import io
import os
import re
import secrets
from typing import Dict, List, Optional

from .db import Database

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PROJECT_STATUSES = ("planning", "active", "paused", "blocked", "completed")

class BackendError(Exception):
    pass

class PermissionError(BackendError):
    pass

class AuthError(BackendError):
    pass

class CivicBackend:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        if os.environ.get("CIVIC_CONNECT_SEED_STARTER_DATA") == "1":
            self.seed()

    # ---------- security / auth ----------
    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return f"{salt}${digest}"

    def verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, digest = stored.split("$", 1)
        except ValueError:
            return False
        return secrets.compare_digest(self.hash_password(password, salt), stored)

    def create_user(self, full_name: str, email: str, password: str, role: str, phone: str = "", organization_name: str = "", location: str = "", bio: str = "") -> int:
        if role not in ("casual", "ngo", "government"):
            raise BackendError("Invalid role.")
        full_name = full_name.strip()
        email = email.lower().strip()
        organization_name = organization_name.strip()
        if not full_name or not EMAIL_RE.match(email) or len(password) < 6:
            raise BackendError("Full name, valid email, and password of at least 6 characters are required.")
        if role in ("ngo", "government") and not organization_name:
            raise BackendError("Organization name is required for NGO and Government accounts.")
        verified = 1 if role in ("ngo", "government") else 0
        try:
            uid = self.db.execute(
                """INSERT INTO users(full_name,email,phone,password_hash,role,organization_name,location,bio,verified)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (full_name, email, phone.strip(), self.hash_password(password), role, organization_name, location.strip(), bio.strip(), verified),
            )
            self.notify(uid, "Welcome to Civic Connect", "Your account has been created successfully.")
            return uid
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise BackendError("That email is already registered.") from exc
            raise

    def login(self, email: str, password: str) -> Dict:
        user = self.db.one("SELECT * FROM users WHERE email=?", (email.lower().strip(),))
        if not user or not self.verify_password(password, user["password_hash"]):
            raise AuthError("Invalid email or password.")
        return user

    def user(self, user_id: int) -> Dict:
        user = self.db.one("SELECT * FROM users WHERE id=?", (user_id,))
        if not user:
            raise BackendError("User not found.")
        return user

    def _count(self, sql: str, params=()) -> int:
        row = self.db.one(sql, params)
        return int(row["c"] if row else 0)

    def _like(self, value: str) -> str:
        return f"%{value.strip()}%"

    def _search_terms(self, value: str) -> List[str]:
        return [term for term in re.split(r"\s+", value.strip()) if term]

    def _search_sql(self, columns: List[str], search: str, params: List, prefix: str = " AND ") -> str:
        terms = self._search_terms(search)
        if not terms:
            return ""
        clauses = []
        column_sql = " OR ".join([f"COALESCE({column}, '') ILIKE ?" for column in columns])
        for term in terms:
            clauses.append(f"({column_sql})")
            params.extend([self._like(term)] * len(columns))
        return f"{prefix}{' AND '.join(clauses)}"

    def _limit_value(self, limit: Optional[int], default: Optional[int] = None, maximum: int = 100) -> Optional[int]:
        if limit is None:
            return default
        try:
            value = int(limit)
        except (TypeError, ValueError):
            value = default or maximum
        return max(1, min(value, maximum))

    def update_profile(self, user_id: int, full_name: str, phone: str, location: str, bio: str):
        if not full_name.strip():
            raise BackendError("Full name is required.")
        self.db.execute("UPDATE users SET full_name=?, phone=?, location=?, bio=? WHERE id=?", (full_name.strip(), phone.strip(), location.strip(), bio.strip(), user_id))
        self.notify(user_id, "Profile updated", "Your profile changes were saved.")

    def users_by_role(self, role: str) -> List[Dict]:
        return self.db.query("SELECT id,full_name,email,role,organization_name,location,bio,verified,created_at FROM users WHERE role=? ORDER BY full_name", (role,))

    def public_stats(self) -> Dict[str, int]:
        row = self.db.one(
            """
            SELECT
                (SELECT COUNT(*) FROM users WHERE role='casual') AS casual_users,
                (SELECT COUNT(*) FROM users WHERE role='ngo') AS ngo_users,
                (SELECT COUNT(*) FROM users WHERE role='government') AS government_users,
                (SELECT COUNT(*) FROM projects) AS projects
            """
        ) or {}
        return {key: int(row.get(key) or 0) for key in ("casual_users", "ngo_users", "government_users", "projects")}

    # ---------- notifications ----------
    def notify(self, user_id: int, title: str, body: str):
        self.db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)", (user_id, title, body))

    def notifications(self, user_id: int, limit: int = 30) -> List[Dict]:
        return self.db.query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, max(1, min(int(limit), 100))))

    def unread_count(self, user_id: int) -> int:
        row = self.db.one("SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
        return int(row["c"] if row else 0)

    def mark_notifications_read(self, user_id: int):
        self.db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))

    # ---------- casual social ----------
    def require_casual(self, user_id: int):
        if self.user(user_id)["role"] != "casual":
            raise PermissionError("Only Casual Users can use this social feature.")

    def create_post(self, author_id: int, body: str, topic: str = "General") -> int:
        self.require_casual(author_id)
        if not body.strip():
            raise BackendError("Post cannot be empty.")
        pid = self.db.execute("INSERT INTO posts(author_id,body,topic) VALUES(?,?,?)", (author_id, body.strip(), topic.strip() or "General"))
        return pid

    def feed(self, viewer_id: int, search: str = "") -> List[Dict]:
        self.require_casual(viewer_id)
        params = []
        where = "WHERE u.role='casual'"
        where += self._search_sql(["p.body", "p.topic", "u.full_name", "u.email"], search, params)
        params.append(viewer_id)
        posts = self.db.query(
            f"""
            WITH visible_posts AS (
                SELECT p.*, u.full_name, u.email
                FROM posts p
                JOIN users u ON u.id=p.author_id
                {where}
                ORDER BY p.created_at DESC, p.id DESC
                LIMIT 40
            )
            SELECT vp.*,
                   COALESCE(lc.like_count, 0) AS like_count,
                   COALESCE(cc.comment_count, 0) AS comment_count,
                   (ml.user_id IS NOT NULL) AS liked_by_me
            FROM visible_posts vp
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS like_count
                FROM likes
                WHERE post_id IN (SELECT id FROM visible_posts)
                GROUP BY post_id
            ) lc ON lc.post_id=vp.id
            LEFT JOIN (
                SELECT post_id, COUNT(*) AS comment_count
                FROM comments
                WHERE post_id IN (SELECT id FROM visible_posts)
                GROUP BY post_id
            ) cc ON cc.post_id=vp.id
            LEFT JOIN likes ml ON ml.post_id=vp.id AND ml.user_id=?
            ORDER BY vp.created_at DESC, vp.id DESC
            """,
            params,
        )
        return posts

    def recent_comments_for_posts(self, post_ids: List[int], per_post: int = 3) -> Dict[int, List[Dict]]:
        if not post_ids:
            return {}
        placeholders = ",".join(["?"] * len(post_ids))
        rows = self.db.query(
            f"""
            SELECT post_id, id, author_id, body, created_at, full_name
            FROM (
                SELECT c.*, u.full_name,
                       ROW_NUMBER() OVER (PARTITION BY c.post_id ORDER BY c.created_at DESC, c.id DESC) AS rn
                FROM comments c
                JOIN users u ON u.id=c.author_id
                WHERE c.post_id IN ({placeholders})
            ) ranked
            WHERE rn <= ?
            ORDER BY post_id, created_at ASC, id ASC
            """,
            (*post_ids, per_post),
        )
        grouped: Dict[int, List[Dict]] = {}
        for row in rows:
            grouped.setdefault(row["post_id"], []).append(row)
        return grouped

    def toggle_like(self, user_id: int, post_id: int) -> bool:
        self.require_casual(user_id)
        post = self.db.one("SELECT p.*, u.role FROM posts p JOIN users u ON u.id=p.author_id WHERE p.id=?", (post_id,))
        if not post or post["role"] != "casual":
            raise PermissionError("Casual Users can only like Casual User posts.")
        existing = self.db.one("SELECT 1 FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        if existing:
            self.db.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (user_id, post_id))
            return False
        self.db.execute("INSERT INTO likes(user_id,post_id) VALUES(?,?)", (user_id, post_id))
        if post["author_id"] != user_id:
            self.notify(post["author_id"], "New like", f"{self.user(user_id)['full_name']} liked your post.")
        return True

    def add_comment(self, user_id: int, post_id: int, body: str) -> int:
        self.require_casual(user_id)
        if not body.strip():
            raise BackendError("Comment cannot be empty.")
        post = self.db.one("SELECT p.*, u.role FROM posts p JOIN users u ON u.id=p.author_id WHERE p.id=?", (post_id,))
        if not post or post["role"] != "casual":
            raise PermissionError("Casual Users can only comment on Casual User posts.")
        cid = self.db.execute("INSERT INTO comments(post_id,author_id,body) VALUES(?,?,?)", (post_id, user_id, body.strip()))
        if post["author_id"] != user_id:
            self.notify(post["author_id"], "New comment", f"{self.user(user_id)['full_name']} commented on your post.")
        return cid

    def comments_for_post(self, post_id: int) -> List[Dict]:
        return self.db.query(
            "SELECT c.*, u.full_name FROM comments c JOIN users u ON u.id=c.author_id WHERE c.post_id=? ORDER BY c.created_at ASC",
            (post_id,),
        )

    def send_friend_request(self, requester_id: int, receiver_id: int) -> int:
        self.require_casual(requester_id); self.require_casual(receiver_id)
        if requester_id == receiver_id:
            raise BackendError("You cannot add yourself.")
        a = self.db.one("SELECT * FROM friendships WHERE (requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)", (requester_id, receiver_id, receiver_id, requester_id))
        if a:
            raise BackendError("A friend request or friendship already exists.")
        request_id = self.db.execute("INSERT INTO friendships(requester_id, receiver_id, status) VALUES(?,?, 'pending')", (requester_id, receiver_id))
        self.notify(receiver_id, "New friend request", f"{self.user(requester_id)['full_name']} sent you a friend request.")
        return request_id

    def respond_friend_request(self, friendship_id: int, receiver_id: int, accept: bool):
        fr = self.db.one("SELECT * FROM friendships WHERE id=?", (friendship_id,))
        if not fr or fr["receiver_id"] != receiver_id:
            raise PermissionError("You can only respond to requests sent to you.")
        if fr["status"] != "pending":
            raise BackendError("This friend request has already been handled.")
        status = "accepted" if accept else "rejected"
        self.db.execute("UPDATE friendships SET status=? WHERE id=?", (status, friendship_id))
        self.notify(fr["requester_id"], "Friend request updated", f"Your friend request was {status}.")

    def friends_and_requests(self, user_id: int, search: str = "", limit: Optional[int] = None) -> Dict[str, List[Dict]]:
        self.require_casual(user_id)
        search_params: List = []
        search_clause = self._search_sql(["u.full_name", "u.email", "u.location", "u.bio"], search, search_params)
        limit_value = self._limit_value(limit)
        limit_sql = " LIMIT ?" if limit_value else ""
        friends_params = [user_id, user_id, user_id, *search_params]
        incoming_params = [user_id, *search_params]
        outgoing_params = [user_id, *search_params]
        if limit_value:
            friends_params.append(limit_value)
            incoming_params.append(limit_value)
            outgoing_params.append(limit_value)
        friends = self.db.query(
            f"""
            SELECT f.*, u.id AS other_id, u.full_name, u.email, u.location, u.bio
            FROM friendships f
            JOIN users u ON u.id = CASE WHEN f.requester_id=? THEN f.receiver_id ELSE f.requester_id END
            WHERE (f.requester_id=? OR f.receiver_id=?) AND f.status='accepted'
            {search_clause}
            ORDER BY u.full_name
            {limit_sql}
            """, friends_params)
        incoming = self.db.query(
            f"SELECT f.*, u.full_name, u.email FROM friendships f JOIN users u ON u.id=f.requester_id WHERE f.receiver_id=? AND f.status='pending' {search_clause} ORDER BY f.created_at DESC{limit_sql}",
            incoming_params)
        outgoing = self.db.query(
            f"SELECT f.*, u.full_name, u.email FROM friendships f JOIN users u ON u.id=f.receiver_id WHERE f.requester_id=? AND f.status='pending' {search_clause} ORDER BY f.created_at DESC{limit_sql}",
            outgoing_params)
        return {"friends": friends, "incoming": incoming, "outgoing": outgoing}

    def suggested_casual_users(self, user_id: int, search: str = "") -> List[Dict]:
        self.require_casual(user_id)
        params = [user_id, user_id, user_id]
        search_filter = self._search_sql(["u.full_name", "u.email", "u.location", "u.bio"], search, params)
        return self.db.query(
            f"""
            SELECT u.id, u.full_name, u.email, u.location, u.bio
            FROM users u
            WHERE u.role='casual' AND u.id<>?
              AND NOT EXISTS (
                  SELECT 1 FROM friendships f
                  WHERE f.receiver_id=? AND f.requester_id=u.id AND f.status IN ('pending','accepted')
              )
              AND NOT EXISTS (
                  SELECT 1 FROM friendships f
                  WHERE f.requester_id=? AND f.receiver_id=u.id AND f.status IN ('pending','accepted')
              )
              {search_filter}
            ORDER BY u.full_name LIMIT 20
            """, params)

    def follow_org(self, follower_id: int, following_id: int) -> int:
        self.require_casual(follower_id)
        target = self.user(following_id)
        if target["role"] not in ("ngo", "government"):
            raise PermissionError("Casual Users can only follow NGO and Government accounts.")
        try:
            follow_id = self.db.execute(
                "INSERT INTO follows(follower_id, following_id) VALUES(?,?)",
                (follower_id, following_id),
            )
            self.notify(following_id, "New follower", f"{self.user(follower_id)['full_name']} followed your public profile.")
            return follow_id
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise BackendError("You already follow that account.") from exc
            raise

    def unfollow_org(self, follower_id: int, following_id: int):
        self.require_casual(follower_id)
        self.db.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?", (follower_id, following_id))

    def connect_accounts(self, user_id: int, search: str = "", limit: Optional[int] = 60) -> Dict[str, List[Dict]]:
        self.require_casual(user_id)
        limit_value = self._limit_value(limit, default=60)
        search_params: List = []
        search_clause = self._search_sql(
            ["u.full_name", "u.email", "u.organization_name", "u.location", "u.bio", "u.role"],
            search,
            search_params,
        )
        following_params = [user_id, *search_params, limit_value]
        discover_params = [user_id, *search_params, limit_value]
        select_sql = """
            SELECT u.id, u.full_name, u.email, u.role, u.organization_name, u.location, u.bio, u.verified,
                   COALESCE(fc.follower_count, 0) AS follower_count
            FROM users u
            LEFT JOIN (
                SELECT following_id, COUNT(*) AS follower_count
                FROM follows
                GROUP BY following_id
            ) fc ON fc.following_id=u.id
        """
        following = self.db.query(
            f"""
            {select_sql}
            JOIN follows f ON f.following_id=u.id
            WHERE f.follower_id=?
              AND u.role IN ('ngo','government')
              {search_clause}
            ORDER BY f.created_at DESC, u.full_name
            LIMIT ?
            """,
            following_params,
        )
        discover = self.db.query(
            f"""
            {select_sql}
            WHERE u.role IN ('ngo','government')
              AND NOT EXISTS (
                  SELECT 1 FROM follows f
                  WHERE f.follower_id=? AND f.following_id=u.id
              )
              {search_clause}
            ORDER BY u.role, u.full_name
            LIMIT ?
            """,
            discover_params,
        )
        return {"following": following, "discover": discover}

    # ---------- conversations ----------
    def _conversation_kind_and_permission(self, a: int, b: int) -> str:
        ua, ub = self.user(a), self.user(b)
        if ua["role"] == ub["role"] == "casual":
            return "casual"
        roles = {ua["role"], ub["role"]}
        if roles == {"ngo", "government"}:
            if not self.has_accepted_partnership(a, b):
                raise PermissionError("Government and NGOs must be connected partners before messaging.")
            return "org"
        raise PermissionError("Casual users cannot interact with Government/NGO accounts, and Government/NGO users cannot message casual users.")

    def get_or_create_conversation(self, a: int, b: int) -> int:
        kind = self._conversation_kind_and_permission(a, b)
        x, y = sorted([a, b])
        row = self.db.one("SELECT * FROM conversations WHERE user_a=? AND user_b=? AND kind=?", (x, y, kind))
        if row:
            return row["id"]
        return self.db.execute("INSERT INTO conversations(user_a,user_b,kind) VALUES(?,?,?)", (x, y, kind))

    def send_message(self, sender_id: int, receiver_id: int, body: str, attachment_name: str = "") -> int:
        if not body.strip() and not attachment_name.strip():
            raise BackendError("Message cannot be empty.")
        cid = self.get_or_create_conversation(sender_id, receiver_id)
        mid = self.db.execute("INSERT INTO messages(conversation_id,sender_id,body,attachment_name) VALUES(?,?,?,?)", (cid, sender_id, body.strip(), attachment_name.strip()))
        self.notify(receiver_id, "New message", f"{self.user(sender_id)['full_name']} sent you a message.")
        return mid

    def conversations_for(self, user_id: int, limit: Optional[int] = None) -> List[Dict]:
        limit_value = self._limit_value(limit)
        limit_sql = "LIMIT ?" if limit_value else ""
        params = [user_id, user_id, user_id]
        if limit_value:
            params.append(limit_value)
        return self.db.query(
            f"""
            SELECT c.*, u.id AS other_id, u.full_name AS other_name, u.role AS other_role, u.organization_name,
                   lm.body AS last_message, lm.created_at AS last_at
            FROM conversations c
            JOIN users u ON u.id = CASE WHEN c.user_a=? THEN c.user_b ELSE c.user_a END
            LEFT JOIN LATERAL (
                SELECT m.body, m.created_at
                FROM messages m
                WHERE m.conversation_id=c.id
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            ) lm ON TRUE
            WHERE c.user_a=? OR c.user_b=?
            ORDER BY COALESCE(lm.created_at, c.created_at) DESC
            {limit_sql}
            """, params)

    def messages(self, conversation_id: int, user_id: int) -> List[Dict]:
        conv = self.db.one("SELECT * FROM conversations WHERE id=? AND (user_a=? OR user_b=?)", (conversation_id, user_id, user_id))
        if not conv:
            raise PermissionError("Conversation not available.")
        return self.db.query(
            """
            SELECT *
            FROM (
                SELECT m.*, u.full_name
                FROM messages m
                JOIN users u ON u.id=m.sender_id
                WHERE conversation_id=?
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT ?
            ) recent
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id, 120),
        )

    # ---------- government / ngo partnerships ----------
    def require_org(self, user_id: int):
        if self.user(user_id)["role"] not in ("ngo", "government"):
            raise PermissionError("Only NGO and Government users can use this feature.")

    def require_gov_ngo_pair(self, a: int, b: int):
        roles = {self.user(a)["role"], self.user(b)["role"]}
        if roles != {"ngo", "government"}:
            raise PermissionError("Partnerships are only between Government Agencies and NGOs.")

    def has_accepted_partnership(self, a: int, b: int) -> bool:
        self.require_gov_ngo_pair(a, b)
        row = self.db.one(
            "SELECT 1 FROM partner_requests WHERE ((requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)) AND status='accepted'",
            (a, b, b, a),
        )
        return bool(row)

    def require_accepted_partnership(self, a: int, b: int):
        if not self.has_accepted_partnership(a, b):
            raise PermissionError("Create and accept a partnership first.")

    def send_partner_request(self, requester_id: int, receiver_id: int, note: str = "") -> int:
        self.require_gov_ngo_pair(requester_id, receiver_id)
        existing = self.db.one("SELECT * FROM partner_requests WHERE (requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)", (requester_id, receiver_id, receiver_id, requester_id))
        if existing:
            raise BackendError("A partner request already exists between these accounts.")
        request_id = self.db.execute("INSERT INTO partner_requests(requester_id, receiver_id, note) VALUES(?,?,?)", (requester_id, receiver_id, note.strip()))
        self.notify(receiver_id, "New partner request", f"{self.user(requester_id)['full_name']} wants to connect.")
        return request_id

    def respond_partner_request(self, request_id: int, receiver_id: int, accept: bool):
        pr = self.db.one("SELECT * FROM partner_requests WHERE id=?", (request_id,))
        if not pr or pr["receiver_id"] != receiver_id:
            raise PermissionError("You can only respond to requests sent to you.")
        if pr["status"] != "pending":
            raise BackendError("This partner request has already been handled.")
        status = "accepted" if accept else "rejected"
        self.db.execute("UPDATE partner_requests SET status=? WHERE id=?", (status, request_id))
        self.notify(pr["requester_id"], "Partner request updated", f"Your partner request was {status}.")
        if accept:
            self.get_or_create_conversation(pr["requester_id"], pr["receiver_id"])

    def partners_and_requests(self, user_id: int, search: str = "", limit: Optional[int] = None) -> Dict[str, List[Dict]]:
        self.require_org(user_id)
        search_params: List = []
        search_clause = self._search_sql(["u.full_name", "u.organization_name", "u.location", "u.bio", "u.email", "u.role"], search, search_params)
        limit_value = self._limit_value(limit)
        limit_sql = " LIMIT ?" if limit_value else ""
        partners_params = [user_id, user_id, user_id, *search_params]
        incoming_params = [user_id, *search_params]
        outgoing_params = [user_id, *search_params]
        if limit_value:
            partners_params.append(limit_value)
            incoming_params.append(limit_value)
            outgoing_params.append(limit_value)
        partners = self.db.query(
            f"""
            SELECT p.*, u.id AS other_id, u.full_name, u.role, u.organization_name, u.location, u.bio
            FROM partner_requests p
            JOIN users u ON u.id = CASE WHEN p.requester_id=? THEN p.receiver_id ELSE p.requester_id END
            WHERE (p.requester_id=? OR p.receiver_id=?) AND p.status='accepted'
            {search_clause}
            ORDER BY u.full_name
            {limit_sql}
            """, partners_params)
        incoming = self.db.query(
            f"""
            SELECT p.*, u.full_name, u.role, u.organization_name
            FROM partner_requests p
            JOIN users u ON u.id=p.requester_id
            WHERE p.receiver_id=? AND p.status='pending'
            {search_clause}
            ORDER BY p.created_at DESC
            {limit_sql}
            """, incoming_params)
        outgoing = self.db.query(
            f"""
            SELECT p.*, u.full_name, u.role, u.organization_name
            FROM partner_requests p
            JOIN users u ON u.id=p.receiver_id
            WHERE p.requester_id=? AND p.status='pending'
            {search_clause}
            ORDER BY p.created_at DESC
            {limit_sql}
            """, outgoing_params)
        return {"partners": partners, "incoming": incoming, "outgoing": outgoing}

    def discover_orgs(self, user_id: int, search: str = "", limit: Optional[int] = 30) -> List[Dict]:
        me = self.user(user_id)
        if me["role"] == "government":
            role = "ngo"
        elif me["role"] == "ngo":
            role = "government"
        else:
            raise PermissionError("Only Government and NGO users can discover partners.")
        params = [role, user_id, user_id]
        search_filter = self._search_sql(["u.full_name", "u.organization_name", "u.location", "u.bio", "u.email", "u.role"], search, params)
        limit_value = self._limit_value(limit, default=30)
        params.append(limit_value)
        return self.db.query(
            f"""
            SELECT u.id,u.full_name,u.email,u.role,u.organization_name,u.location,u.bio,u.verified
            FROM users u
            WHERE u.role=?
              AND NOT EXISTS (
                  SELECT 1 FROM partner_requests p
                  WHERE p.receiver_id=? AND p.requester_id=u.id AND p.status IN ('pending','accepted')
              )
              AND NOT EXISTS (
                  SELECT 1 FROM partner_requests p
                  WHERE p.requester_id=? AND p.receiver_id=u.id AND p.status IN ('pending','accepted')
              )
              {search_filter}
            ORDER BY u.full_name LIMIT ?
            """, params)

    # ---------- agreements ----------
    def create_agreement(self, creator_id: int, partner_id: int, title: str, summary: str, budget: float = 0) -> int:
        self.require_accepted_partnership(creator_id, partner_id)
        uc = self.user(creator_id)
        government_id = creator_id if uc["role"] == "government" else partner_id
        ngo_id = creator_id if uc["role"] == "ngo" else partner_id
        if not title.strip() or not summary.strip():
            raise BackendError("Agreement title and summary are required.")
        aid = self.db.execute("INSERT INTO agreements(title,government_id,ngo_id,summary,budget,status,created_by) VALUES(?,?,?,?,?,'pending',?)", (title.strip(), government_id, ngo_id, summary.strip(), float(budget or 0), creator_id))
        self.db.execute("INSERT INTO agreement_events(agreement_id,actor_id,event_type,note) VALUES(?,?,?,?)", (aid, creator_id, "created", "Agreement created and submitted for review."))
        self.notify(partner_id, "Agreement submitted", f"{uc['full_name']} submitted agreement: {title}.")
        return aid

    def agreements_for(self, user_id: int, search: str = "", status: str = "", limit: Optional[int] = None) -> List[Dict]:
        self.require_org(user_id)
        params = [user_id, user_id]
        filters = ["(a.government_id=? OR a.ngo_id=?)"]
        if status.strip() and status.strip() != "all":
            filters.append("a.status=?")
            params.append(status.strip())
        search_clause = self._search_sql(
            ["a.title", "a.summary", "a.status", "g.full_name", "n.full_name", "g.organization_name", "n.organization_name"],
            search,
            params,
            prefix="",
        )
        if search_clause:
            filters.append(search_clause)
        where = " AND ".join(filters)
        limit_sql = ""
        if limit:
            limit_sql = "LIMIT ?"
            params.append(max(1, min(int(limit), 100)))
        return self.db.query(
            f"""
            SELECT a.*, g.full_name AS government_name, n.full_name AS ngo_name,
                   g.organization_name AS government_org, n.organization_name AS ngo_org
            FROM agreements a
            JOIN users g ON g.id=a.government_id
            JOIN users n ON n.id=a.ngo_id
            WHERE {where}
            ORDER BY a.updated_at DESC, a.id DESC
            {limit_sql}
            """, params)

    def agreement(self, agreement_id: int, user_id: int) -> Dict:
        row = self.db.one(
            """
            SELECT a.*, g.full_name AS government_name, n.full_name AS ngo_name,
                   g.organization_name AS government_org, n.organization_name AS ngo_org
            FROM agreements a
            JOIN users g ON g.id=a.government_id
            JOIN users n ON n.id=a.ngo_id
            WHERE a.id=? AND (a.government_id=? OR a.ngo_id=?)
            """, (agreement_id, user_id, user_id))
        if not row:
            raise PermissionError("Agreement not available.")
        return row

    def update_agreement_status(self, agreement_id: int, actor_id: int, status: str, note: str = ""):
        ag = self.agreement(agreement_id, actor_id)
        actor = self.user(actor_id)
        if status not in ("pending", "changes_requested", "approved", "rejected", "active", "completed"):
            raise BackendError("Invalid status.")
        current = ag["status"]
        if status == current:
            raise BackendError("Agreement is already in that status.")
        if status in ("approved", "rejected", "changes_requested"):
            if actor["role"] != "government":
                raise PermissionError("Only Government users can approve, reject, or request changes.")
            if current not in ("pending", "changes_requested"):
                raise BackendError("Only pending agreements can be reviewed.")
        elif status == "pending" and current != "changes_requested":
            raise BackendError("Only agreements with requested changes can be resubmitted.")
        elif status == "active" and current != "approved":
            raise BackendError("Only approved agreements can become active.")
        elif status == "completed" and current != "active":
            raise BackendError("Only active agreements can be completed.")
        self.db.execute("UPDATE agreements SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, agreement_id))
        self.db.execute("INSERT INTO agreement_events(agreement_id,actor_id,event_type,note) VALUES(?,?,?,?)", (agreement_id, actor_id, status, note.strip()))
        other = ag["ngo_id"] if actor_id == ag["government_id"] else ag["government_id"]
        self.notify(other, "Agreement updated", f"{ag['title']} is now {status.replace('_',' ')}.")

    def agreement_events(self, agreement_id: int, user_id: int) -> List[Dict]:
        self.agreement(agreement_id, user_id)
        return self.db.query("SELECT e.*, u.full_name FROM agreement_events e JOIN users u ON u.id=e.actor_id WHERE agreement_id=? ORDER BY e.created_at DESC, e.id DESC", (agreement_id,))

    def add_document(self, uploader_id: int, name: str, agreement_id: Optional[int] = None, project_id: Optional[int] = None, path: str = "") -> int:
        if not name.strip():
            raise BackendError("Document name required.")
        if bool(agreement_id) == bool(project_id):
            raise BackendError("Attach a document to exactly one agreement or project.")
        if agreement_id:
            self.agreement(agreement_id, uploader_id)
        if project_id:
            self.project(project_id, uploader_id)
        return self.db.execute("INSERT INTO documents(agreement_id,project_id,uploader_id,name,path) VALUES(?,?,?,?,?)", (agreement_id, project_id, uploader_id, name.strip(), path.strip()))

    def documents_for_agreement(self, agreement_id: int, user_id: int) -> List[Dict]:
        self.agreement(agreement_id, user_id)
        return self.db.query("SELECT d.*, u.full_name AS uploader FROM documents d JOIN users u ON u.id=d.uploader_id WHERE agreement_id=? ORDER BY d.created_at DESC", (agreement_id,))

    # ---------- projects and reports ----------
    def project(self, project_id: int, user_id: int) -> Dict:
        row = self.db.one(
            """
            SELECT p.*, u.full_name AS partner_name
            FROM projects p LEFT JOIN users u ON u.id=p.partner_id
            WHERE p.id=? AND (p.owner_id=? OR p.partner_id=?)
            """,
            (project_id, user_id, user_id),
        )
        if not row:
            raise PermissionError("Project not available.")
        return row

    def create_project(self, owner_id: int, title: str, partner_id: Optional[int] = None, focus_area: str = "") -> int:
        self.require_org(owner_id)
        if partner_id:
            self.require_accepted_partnership(owner_id, partner_id)
        if not title.strip():
            raise BackendError("Project title required.")
        pid = self.db.execute("INSERT INTO projects(title,owner_id,partner_id,focus_area) VALUES(?,?,?,?)", (title.strip(), owner_id, partner_id, focus_area.strip()))
        if partner_id:
            self.notify(partner_id, "New project", f"{self.user(owner_id)['full_name']} added you to project: {title}.")
        return pid

    def projects_for(self, user_id: int, search: str = "", status: str = "", limit: Optional[int] = None) -> List[Dict]:
        self.require_org(user_id)
        params = [user_id, user_id]
        filters = ["(p.owner_id=? OR p.partner_id=?)"]
        if status.strip() and status.strip() != "all":
            filters.append("p.status=?")
            params.append(status.strip())
        search_clause = self._search_sql(["p.title", "p.focus_area", "p.status", "u.full_name"], search, params, prefix="")
        if search_clause:
            filters.append(search_clause)
        where = " AND ".join(filters)
        limit_sql = ""
        if limit:
            limit_sql = " LIMIT ?"
            params.append(max(1, min(int(limit), 100)))
        return self.db.query(f"SELECT p.*, u.full_name AS partner_name FROM projects p LEFT JOIN users u ON u.id=p.partner_id WHERE {where} ORDER BY p.created_at DESC{limit_sql}", params)

    def update_project_progress(self, project_id: int, user_id: int, progress: int, status: str):
        row = self.project(project_id, user_id)
        progress = max(0, min(100, int(progress)))
        status = (status.strip() or row["status"]).lower()
        if status not in PROJECT_STATUSES:
            raise BackendError(f"Project status must be one of: {', '.join(PROJECT_STATUSES)}.")
        self.db.execute("UPDATE projects SET progress=?, status=? WHERE id=?", (progress, status, project_id))
        other = row["partner_id"] if user_id == row["owner_id"] else row["owner_id"]
        if other:
            self.notify(other, "Project updated", f"{row['title']} is now {status} at {progress}%.")

    def create_report(self, user_id: int, project_id: int, title: str, body: str):
        row = self.project(project_id, user_id)
        if not title.strip() or not body.strip():
            raise BackendError("Report title and body required.")
        self.db.execute("INSERT INTO reports(project_id,author_id,title,body) VALUES(?,?,?,?)", (project_id, user_id, title.strip(), body.strip()))
        other = row["partner_id"] if user_id == row["owner_id"] else row["owner_id"]
        if other:
            self.notify(other, "New report", f"A report was submitted for {row['title']}.")

    def reports_for(self, user_id: int, search: str = "", limit: Optional[int] = None) -> List[Dict]:
        self.require_org(user_id)
        params = [user_id, user_id]
        search_filter = self._search_sql(["r.title", "r.body", "p.title", "u.full_name"], search, params)
        limit_value = self._limit_value(limit)
        limit_sql = " LIMIT ?" if limit_value else ""
        if limit_value:
            params.append(limit_value)
        return self.db.query(f"SELECT r.*, p.title AS project_title, u.full_name AS author FROM reports r JOIN projects p ON p.id=r.project_id JOIN users u ON u.id=r.author_id WHERE (p.owner_id=? OR p.partner_id=?) {search_filter} ORDER BY r.created_at DESC{limit_sql}", params)

    def documents_for_project(self, project_id: int, user_id: int) -> List[Dict]:
        self.project(project_id, user_id)
        return self.db.query("SELECT d.*, u.full_name AS uploader FROM documents d JOIN users u ON u.id=d.uploader_id WHERE project_id=? ORDER BY d.created_at DESC", (project_id,))

    def documents_for_projects(self, project_ids: List[int], user_id: int, per_project: int = 4) -> Dict[int, List[Dict]]:
        if not project_ids:
            return {}
        placeholders = ",".join(["?"] * len(project_ids))
        rows = self.db.query(
            f"""
            SELECT project_id, id, uploader_id, name, path, created_at, uploader
            FROM (
                SELECT d.*, u.full_name AS uploader,
                       ROW_NUMBER() OVER (PARTITION BY d.project_id ORDER BY d.created_at DESC, d.id DESC) AS rn
                FROM documents d
                JOIN users u ON u.id=d.uploader_id
                JOIN projects p ON p.id=d.project_id
                WHERE d.project_id IN ({placeholders})
                  AND (p.owner_id=? OR p.partner_id=?)
            ) ranked
            WHERE rn <= ?
            ORDER BY project_id, created_at DESC, id DESC
            """,
            (*project_ids, user_id, user_id, per_project),
        )
        grouped: Dict[int, List[Dict]] = {}
        for row in rows:
            grouped.setdefault(row["project_id"], []).append(row)
        return grouped

    # ---------- exports ----------
    def export_summary_csv(self, user_id: int) -> str:
        user = self.user(user_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["section", "title", "detail", "created_at"])
        if user["role"] == "casual":
            for post in self.feed(user_id):
                if post["author_id"] == user_id:
                    writer.writerow(["post", post["topic"], post["body"], post["created_at"]])
            for org in self.connect_accounts(user_id)["following"]:
                writer.writerow(["following", org.get("organization_name") or org["full_name"], org["role"], ""])
            for note in self.notifications(user_id):
                writer.writerow(["notification", note["title"], note["body"], note["created_at"]])
        else:
            for partner in self.partners_and_requests(user_id)["partners"]:
                writer.writerow(["partner", partner.get("organization_name") or partner["full_name"], partner["role"], partner["created_at"]])
            for agreement in self.agreements_for(user_id):
                writer.writerow(["agreement", agreement["title"], agreement["status"], agreement["updated_at"]])
            for project in self.projects_for(user_id):
                writer.writerow(["project", project["title"], f"{project['status']} / {project['progress']}%", project["created_at"]])
            for report in self.reports_for(user_id):
                writer.writerow(["report", report["title"], report["project_title"], report["created_at"]])
        return output.getvalue()

    # ---------- dashboard ----------
    def dashboard_counts(self, user_id: int) -> Dict[str, int]:
        role = self.user(user_id)["role"]
        if role == "casual":
            row = self.db.one(
                """
                SELECT
                    (SELECT COUNT(*) FROM posts WHERE author_id=?) AS posts,
                    (SELECT COUNT(*) FROM friendships WHERE (requester_id=? OR receiver_id=?) AND status='accepted') AS friends,
                    (SELECT COUNT(*) FROM follows WHERE follower_id=?) AS following,
                    (SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0) AS notifications,
                    (SELECT COUNT(*) FROM conversations WHERE user_a=? OR user_b=?) AS messages
                """,
                (user_id, user_id, user_id, user_id, user_id, user_id, user_id),
            ) or {}
            return {key: int(row.get(key) or 0) for key in ("posts", "friends", "following", "notifications", "messages")}
        row = self.db.one(
            """
            SELECT
                (SELECT COUNT(*) FROM partner_requests WHERE (requester_id=? OR receiver_id=?) AND status='accepted') AS partners,
                (SELECT COUNT(*) FROM partner_requests WHERE receiver_id=? AND status='pending') AS pending_requests,
                (SELECT COUNT(*) FROM agreements WHERE government_id=? OR ngo_id=?) AS agreements,
                (SELECT COUNT(*) FROM agreements WHERE (government_id=? OR ngo_id=?) AND status IN ('pending', 'changes_requested')) AS pending_agreements,
                (SELECT COUNT(*) FROM projects WHERE owner_id=? OR partner_id=?) AS projects,
                (SELECT COUNT(*) FROM reports r JOIN projects p ON p.id=r.project_id WHERE p.owner_id=? OR p.partner_id=?) AS reports,
                (SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0) AS notifications
            """,
            (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id),
        ) or {}
        return {key: int(row.get(key) or 0) for key in ("partners", "pending_requests", "agreements", "pending_agreements", "projects", "reports", "notifications")}

    def org_dashboard_snapshot(self, user_id: int) -> Dict[str, object]:
        self.require_org(user_id)
        counts = self.dashboard_counts(user_id)
        return {
            "counts": counts,
            "agreements": self.agreements_for(user_id, limit=6),
            "projects": self.projects_for(user_id, limit=6),
            "notifications": self.notifications(user_id, limit=6),
            "unread": counts["notifications"],
        }

    # ---------- seed data ----------
    def seed(self):
        row = self.db.one("SELECT COUNT(*) AS c FROM users")
        if row and row["c"]:
            return
        seed_password = os.environ.get("CIVIC_CONNECT_SEED_PASSWORD", "").strip()
        if not seed_password:
            raise BackendError("Set CIVIC_CONNECT_SEED_PASSWORD before enabling starter data.")

        casual1 = self.create_user("Alex Johnson", "alex@starter.local", seed_password, "casual", location="Seattle, WA", bio="Community-minded citizen passionate about local issues.")
        casual2 = self.create_user("Sarah Mitchell", "sarah@starter.local", seed_password, "casual", location="Denver, CO", bio="Volunteer and local parks advocate.")
        casual3 = self.create_user("David Lee", "david@starter.local", seed_password, "casual", location="Austin, TX", bio="Education and technology enthusiast.")
        casual4 = self.create_user("Emma Davis", "emma@starter.local", seed_password, "casual", location="Portland, OR", bio="Local art and culture supporter.")
        gov1 = self.create_user("Department of Community Development", "community@gov.starter.local", seed_password, "government", organization_name="Department of Community Development", location="Washington, DC", bio="Public-sector agency for community programs.")
        gov2 = self.create_user("Ministry of Education", "education@gov.starter.local", seed_password, "government", organization_name="Ministry of Education", location="Washington, DC", bio="National education policy and outreach.")
        ngo1 = self.create_user("GreenFuture Initiative", "greenfuture@ngo.starter.local", seed_password, "ngo", organization_name="GreenFuture Initiative", location="Washington, DC", bio="Environment and sustainability NGO.")
        ngo2 = self.create_user("Helping Hands Foundation", "helping@ngo.starter.local", seed_password, "ngo", organization_name="Helping Hands Foundation", location="Baltimore, MD", bio="Community support and education NGO.")
        ngo3 = self.create_user("HealthAid Network", "health@ngo.starter.local", seed_password, "ngo", organization_name="HealthAid Network", location="Chicago, IL", bio="Community health outreach network.")

        post1 = self.create_post(casual2, "Just attended a local park cleanup organized by amazing volunteers! Small actions lead to big changes. #CommunityLove #CleanParks", "Community")
        self.create_post(casual3, "Great discussion on youth education and technology today. Empowering the next generation is key to a better future.", "Education")
        self.create_post(casual4, "Local art festival this weekend! Excited to support talented artists in our community. #SupportLocal", "Events")
        post4 = self.create_post(casual1, "Ideas for improving public transportation: more frequent buses, safer stops, and cleaner schedules. What would help your area most?", "Transportation")
        friend_request = self.send_friend_request(casual2, casual1); self.respond_friend_request(friend_request, casual1, True)
        self.send_friend_request(casual3, casual1)
        self.add_comment(casual2, post4, "More frequent buses during peak hours would be a game changer.")
        self.toggle_like(casual1, post1); self.toggle_like(casual2, post4); self.toggle_like(casual3, post4)

        partner_request_1 = self.send_partner_request(ngo1, gov1, "We would like to collaborate on reforestation and youth climate programs.")
        self.respond_partner_request(partner_request_1, gov1, True)
        partner_request_2 = self.send_partner_request(ngo2, gov1, "Seeking approval for a community education partnership.")
        self.respond_partner_request(partner_request_2, gov1, True)
        self.send_partner_request(ngo3, gov2, "Health education outreach proposal.")
        aid = self.create_agreement(gov1, ngo2, "Community Education & Awareness Program", "Implement education and awareness outreach in underserved communities.", 250000)
        self.add_document(ngo2, "Collaboration Agreement_Draft_v2.pdf", agreement_id=aid)
        self.add_document(ngo2, "Budget Breakdown.xlsx", agreement_id=aid)
        self.add_document(gov1, "Compliance Certificate.pdf", agreement_id=aid)
        p1 = self.create_project(ngo1, "Clean Rivers Initiative", gov1, "Environment")
        self.update_project_progress(p1, ngo1, 45, "active")
        self.create_report(ngo1, p1, "Q2 Impact Report", "River cleanup completed in three districts with 128 volunteers.")
        self.send_message(ngo1, gov1, "Good morning! We're excited to share the latest progress on our reforestation project.", "Reforestation_Q2_Report.pdf")
        self.send_message(gov1, ngo1, "Thank you for the update. Please also share the budget utilization.")
