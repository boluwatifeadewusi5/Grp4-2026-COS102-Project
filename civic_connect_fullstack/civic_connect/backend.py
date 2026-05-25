import hashlib
import secrets
from typing import Dict, List, Optional, Tuple

from .db import Database

class BackendError(Exception):
    pass

class PermissionError(BackendError):
    pass

class AuthError(BackendError):
    pass

class CivicBackend:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
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
        if not full_name.strip() or not email.strip() or len(password) < 4:
            raise BackendError("Full name, valid email, and password of at least 4 characters are required.")
        verified = 1 if role in ("ngo", "government") else 0
        try:
            uid = self.db.execute(
                """INSERT INTO users(full_name,email,phone,password_hash,role,organization_name,location,bio,verified)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (full_name.strip(), email.lower().strip(), phone.strip(), self.hash_password(password), role, organization_name.strip(), location.strip(), bio.strip(), verified),
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

    def update_profile(self, user_id: int, full_name: str, phone: str, location: str, bio: str):
        self.db.execute("UPDATE users SET full_name=?, phone=?, location=?, bio=? WHERE id=?", (full_name, phone, location, bio, user_id))
        self.notify(user_id, "Profile updated", "Your profile changes were saved.")

    def users_by_role(self, role: str) -> List[Dict]:
        return self.db.query("SELECT id,full_name,email,role,organization_name,location,bio,verified,created_at FROM users WHERE role=? ORDER BY full_name", (role,))

    # ---------- notifications ----------
    def notify(self, user_id: int, title: str, body: str):
        self.db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)", (user_id, title, body))

    def notifications(self, user_id: int) -> List[Dict]:
        return self.db.query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 30", (user_id,))

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

    def feed(self, viewer_id: int) -> List[Dict]:
        self.require_casual(viewer_id)
        posts = self.db.query(
            """
            SELECT p.*, u.full_name, u.email,
                (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) AS like_count,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id) AS comment_count,
                EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=?) AS liked_by_me
            FROM posts p JOIN users u ON u.id=p.author_id
            WHERE u.role='casual'
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT 80
            """,
            (viewer_id,),
        )
        return posts

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

    def send_friend_request(self, requester_id: int, receiver_id: int):
        self.require_casual(requester_id); self.require_casual(receiver_id)
        if requester_id == receiver_id:
            raise BackendError("You cannot add yourself.")
        a = self.db.one("SELECT * FROM friendships WHERE (requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)", (requester_id, receiver_id, receiver_id, requester_id))
        if a:
            raise BackendError("A friend request or friendship already exists.")
        self.db.execute("INSERT INTO friendships(requester_id, receiver_id, status) VALUES(?,?, 'pending')", (requester_id, receiver_id))
        self.notify(receiver_id, "New friend request", f"{self.user(requester_id)['full_name']} sent you a friend request.")

    def respond_friend_request(self, friendship_id: int, receiver_id: int, accept: bool):
        fr = self.db.one("SELECT * FROM friendships WHERE id=?", (friendship_id,))
        if not fr or fr["receiver_id"] != receiver_id:
            raise PermissionError("You can only respond to requests sent to you.")
        status = "accepted" if accept else "rejected"
        self.db.execute("UPDATE friendships SET status=? WHERE id=?", (status, friendship_id))
        self.notify(fr["requester_id"], "Friend request updated", f"Your friend request was {status}.")

    def friends_and_requests(self, user_id: int) -> Dict[str, List[Dict]]:
        self.require_casual(user_id)
        friends = self.db.query(
            """
            SELECT f.*, u.id AS other_id, u.full_name, u.email, u.location, u.bio
            FROM friendships f
            JOIN users u ON u.id = CASE WHEN f.requester_id=? THEN f.receiver_id ELSE f.requester_id END
            WHERE (f.requester_id=? OR f.receiver_id=?) AND f.status='accepted'
            ORDER BY u.full_name
            """, (user_id, user_id, user_id))
        incoming = self.db.query(
            "SELECT f.*, u.full_name, u.email FROM friendships f JOIN users u ON u.id=f.requester_id WHERE f.receiver_id=? AND f.status='pending' ORDER BY f.created_at DESC",
            (user_id,))
        outgoing = self.db.query(
            "SELECT f.*, u.full_name, u.email FROM friendships f JOIN users u ON u.id=f.receiver_id WHERE f.requester_id=? AND f.status='pending' ORDER BY f.created_at DESC",
            (user_id,))
        return {"friends": friends, "incoming": incoming, "outgoing": outgoing}

    def suggested_casual_users(self, user_id: int) -> List[Dict]:
        self.require_casual(user_id)
        return self.db.query(
            """
            SELECT id, full_name, email, location, bio FROM users
            WHERE role='casual' AND id<>?
              AND id NOT IN (SELECT requester_id FROM friendships WHERE receiver_id=? AND status IN ('pending','accepted'))
              AND id NOT IN (SELECT receiver_id FROM friendships WHERE requester_id=? AND status IN ('pending','accepted'))
            ORDER BY full_name LIMIT 20
            """, (user_id, user_id, user_id))

    # ---------- conversations ----------
    def _conversation_kind_and_permission(self, a: int, b: int) -> str:
        ua, ub = self.user(a), self.user(b)
        if ua["role"] == ub["role"] == "casual":
            return "casual"
        roles = {ua["role"], ub["role"]}
        if roles == {"ngo", "government"}:
            # must have accepted partnership before messaging
            pr = self.db.one(
                "SELECT * FROM partner_requests WHERE ((requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)) AND status='accepted'",
                (a, b, b, a),
            )
            if not pr:
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

    def conversations_for(self, user_id: int) -> List[Dict]:
        return self.db.query(
            """
            SELECT c.*, u.id AS other_id, u.full_name AS other_name, u.role AS other_role, u.organization_name,
                   (SELECT body FROM messages m WHERE m.conversation_id=c.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_message,
                   (SELECT created_at FROM messages m WHERE m.conversation_id=c.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_at
            FROM conversations c
            JOIN users u ON u.id = CASE WHEN c.user_a=? THEN c.user_b ELSE c.user_a END
            WHERE c.user_a=? OR c.user_b=?
            ORDER BY COALESCE(last_at, c.created_at) DESC
            """, (user_id, user_id, user_id))

    def messages(self, conversation_id: int, user_id: int) -> List[Dict]:
        conv = self.db.one("SELECT * FROM conversations WHERE id=? AND (user_a=? OR user_b=?)", (conversation_id, user_id, user_id))
        if not conv:
            raise PermissionError("Conversation not available.")
        return self.db.query("SELECT m.*, u.full_name FROM messages m JOIN users u ON u.id=m.sender_id WHERE conversation_id=? ORDER BY m.created_at ASC, m.id ASC", (conversation_id,))

    # ---------- government / ngo partnerships ----------
    def require_org(self, user_id: int):
        if self.user(user_id)["role"] not in ("ngo", "government"):
            raise PermissionError("Only NGO and Government users can use this feature.")

    def require_gov_ngo_pair(self, a: int, b: int):
        roles = {self.user(a)["role"], self.user(b)["role"]}
        if roles != {"ngo", "government"}:
            raise PermissionError("Partnerships are only between Government Agencies and NGOs.")

    def send_partner_request(self, requester_id: int, receiver_id: int, note: str = ""):
        self.require_gov_ngo_pair(requester_id, receiver_id)
        existing = self.db.one("SELECT * FROM partner_requests WHERE (requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)", (requester_id, receiver_id, receiver_id, requester_id))
        if existing:
            raise BackendError("A partner request already exists between these accounts.")
        self.db.execute("INSERT INTO partner_requests(requester_id, receiver_id, note) VALUES(?,?,?)", (requester_id, receiver_id, note.strip()))
        self.notify(receiver_id, "New partner request", f"{self.user(requester_id)['full_name']} wants to connect.")

    def respond_partner_request(self, request_id: int, receiver_id: int, accept: bool):
        pr = self.db.one("SELECT * FROM partner_requests WHERE id=?", (request_id,))
        if not pr or pr["receiver_id"] != receiver_id:
            raise PermissionError("You can only respond to requests sent to you.")
        status = "accepted" if accept else "rejected"
        self.db.execute("UPDATE partner_requests SET status=? WHERE id=?", (status, request_id))
        self.notify(pr["requester_id"], "Partner request updated", f"Your partner request was {status}.")
        if accept:
            self.get_or_create_conversation(pr["requester_id"], pr["receiver_id"])

    def partners_and_requests(self, user_id: int) -> Dict[str, List[Dict]]:
        self.require_org(user_id)
        partners = self.db.query(
            """
            SELECT p.*, u.id AS other_id, u.full_name, u.role, u.organization_name, u.location, u.bio
            FROM partner_requests p
            JOIN users u ON u.id = CASE WHEN p.requester_id=? THEN p.receiver_id ELSE p.requester_id END
            WHERE (p.requester_id=? OR p.receiver_id=?) AND p.status='accepted'
            ORDER BY u.full_name
            """, (user_id, user_id, user_id))
        incoming = self.db.query(
            "SELECT p.*, u.full_name, u.role, u.organization_name FROM partner_requests p JOIN users u ON u.id=p.requester_id WHERE p.receiver_id=? AND p.status='pending' ORDER BY p.created_at DESC", (user_id,))
        outgoing = self.db.query(
            "SELECT p.*, u.full_name, u.role, u.organization_name FROM partner_requests p JOIN users u ON u.id=p.receiver_id WHERE p.requester_id=? AND p.status='pending' ORDER BY p.created_at DESC", (user_id,))
        return {"partners": partners, "incoming": incoming, "outgoing": outgoing}

    def discover_orgs(self, user_id: int) -> List[Dict]:
        me = self.user(user_id)
        if me["role"] == "government":
            role = "ngo"
        elif me["role"] == "ngo":
            role = "government"
        else:
            raise PermissionError("Only Government and NGO users can discover partners.")
        return self.db.query(
            """
            SELECT id,full_name,email,role,organization_name,location,bio,verified FROM users
            WHERE role=? AND id NOT IN (SELECT requester_id FROM partner_requests WHERE receiver_id=? AND status IN ('pending','accepted'))
                         AND id NOT IN (SELECT receiver_id FROM partner_requests WHERE requester_id=? AND status IN ('pending','accepted'))
            ORDER BY full_name LIMIT 30
            """, (role, user_id, user_id))

    # ---------- agreements ----------
    def create_agreement(self, creator_id: int, partner_id: int, title: str, summary: str, budget: float = 0) -> int:
        self.require_gov_ngo_pair(creator_id, partner_id)
        uc, up = self.user(creator_id), self.user(partner_id)
        government_id = creator_id if uc["role"] == "government" else partner_id
        ngo_id = creator_id if uc["role"] == "ngo" else partner_id
        # must be partners
        pr = self.db.one("SELECT 1 FROM partner_requests WHERE ((requester_id=? AND receiver_id=?) OR (requester_id=? AND receiver_id=?)) AND status='accepted'", (creator_id, partner_id, partner_id, creator_id))
        if not pr:
            raise PermissionError("Create a partnership before creating agreements.")
        if not title.strip() or not summary.strip():
            raise BackendError("Agreement title and summary are required.")
        aid = self.db.execute("INSERT INTO agreements(title,government_id,ngo_id,summary,budget,status,created_by) VALUES(?,?,?,?,?,'pending',?)", (title.strip(), government_id, ngo_id, summary.strip(), float(budget or 0), creator_id))
        self.db.execute("INSERT INTO agreement_events(agreement_id,actor_id,event_type,note) VALUES(?,?,?,?)", (aid, creator_id, "created", "Agreement created and submitted for review."))
        self.notify(partner_id, "Agreement submitted", f"{uc['full_name']} submitted agreement: {title}.")
        return aid

    def agreements_for(self, user_id: int) -> List[Dict]:
        self.require_org(user_id)
        return self.db.query(
            """
            SELECT a.*, g.full_name AS government_name, n.full_name AS ngo_name,
                   g.organization_name AS government_org, n.organization_name AS ngo_org
            FROM agreements a
            JOIN users g ON g.id=a.government_id
            JOIN users n ON n.id=a.ngo_id
            WHERE a.government_id=? OR a.ngo_id=?
            ORDER BY a.updated_at DESC, a.id DESC
            """, (user_id, user_id))

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
        if status in ("approved", "rejected", "changes_requested") and actor["role"] != "government":
            raise PermissionError("Only Government users can approve, reject, or request changes.")
        if status not in ("pending", "changes_requested", "approved", "rejected", "active", "completed"):
            raise BackendError("Invalid status.")
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
        if agreement_id:
            self.agreement(agreement_id, uploader_id)
        return self.db.execute("INSERT INTO documents(agreement_id,project_id,uploader_id,name,path) VALUES(?,?,?,?,?)", (agreement_id, project_id, uploader_id, name.strip(), path.strip()))

    def documents_for_agreement(self, agreement_id: int, user_id: int) -> List[Dict]:
        self.agreement(agreement_id, user_id)
        return self.db.query("SELECT d.*, u.full_name AS uploader FROM documents d JOIN users u ON u.id=d.uploader_id WHERE agreement_id=? ORDER BY d.created_at DESC", (agreement_id,))

    # ---------- projects and reports ----------
    def create_project(self, owner_id: int, title: str, partner_id: Optional[int] = None, focus_area: str = "") -> int:
        self.require_org(owner_id)
        if partner_id:
            self.require_gov_ngo_pair(owner_id, partner_id)
        if not title.strip():
            raise BackendError("Project title required.")
        pid = self.db.execute("INSERT INTO projects(title,owner_id,partner_id,focus_area) VALUES(?,?,?,?)", (title.strip(), owner_id, partner_id, focus_area.strip()))
        if partner_id:
            self.notify(partner_id, "New project", f"{self.user(owner_id)['full_name']} added you to project: {title}.")
        return pid

    def projects_for(self, user_id: int) -> List[Dict]:
        self.require_org(user_id)
        return self.db.query("SELECT p.*, u.full_name AS partner_name FROM projects p LEFT JOIN users u ON u.id=p.partner_id WHERE p.owner_id=? OR p.partner_id=? ORDER BY p.created_at DESC", (user_id, user_id))

    def update_project_progress(self, project_id: int, user_id: int, progress: int, status: str):
        row = self.db.one("SELECT * FROM projects WHERE id=? AND (owner_id=? OR partner_id=?)", (project_id, user_id, user_id))
        if not row:
            raise PermissionError("Project not available.")
        progress = max(0, min(100, int(progress)))
        self.db.execute("UPDATE projects SET progress=?, status=? WHERE id=?", (progress, status.strip() or row["status"], project_id))

    def create_report(self, user_id: int, project_id: int, title: str, body: str):
        row = self.db.one("SELECT * FROM projects WHERE id=? AND (owner_id=? OR partner_id=?)", (project_id, user_id, user_id))
        if not row:
            raise PermissionError("Project not available.")
        if not title.strip() or not body.strip():
            raise BackendError("Report title and body required.")
        self.db.execute("INSERT INTO reports(project_id,author_id,title,body) VALUES(?,?,?,?)", (project_id, user_id, title.strip(), body.strip()))
        other = row["partner_id"] if user_id == row["owner_id"] else row["owner_id"]
        if other:
            self.notify(other, "New report", f"A report was submitted for {row['title']}.")

    def reports_for(self, user_id: int) -> List[Dict]:
        self.require_org(user_id)
        return self.db.query("SELECT r.*, p.title AS project_title, u.full_name AS author FROM reports r JOIN projects p ON p.id=r.project_id JOIN users u ON u.id=r.author_id WHERE p.owner_id=? OR p.partner_id=? ORDER BY r.created_at DESC", (user_id, user_id))

    # ---------- dashboard ----------
    def dashboard_counts(self, user_id: int) -> Dict[str, int]:
        role = self.user(user_id)["role"]
        if role == "casual":
            return {
                "posts": self.db.one("SELECT COUNT(*) c FROM posts WHERE author_id=?", (user_id,))["c"],
                "friends": len(self.friends_and_requests(user_id)["friends"]),
                "notifications": self.unread_count(user_id),
                "messages": len(self.conversations_for(user_id)),
            }
        pr = self.partners_and_requests(user_id)
        ags = self.agreements_for(user_id)
        projects = self.projects_for(user_id)
        return {
            "partners": len(pr["partners"]),
            "pending_requests": len(pr["incoming"]),
            "agreements": len(ags),
            "pending_agreements": len([a for a in ags if a["status"] in ("pending", "changes_requested")]),
            "projects": len(projects),
            "reports": len(self.reports_for(user_id)),
            "notifications": self.unread_count(user_id),
        }

    # ---------- seed data ----------
    def seed(self):
        row = self.db.one("SELECT COUNT(*) AS c FROM users")
        if row and row["c"]:
            return
        casual1 = self.create_user("Alex Johnson", "alex@demo.com", "password", "casual", location="Seattle, WA", bio="Community-minded citizen passionate about local issues.")
        casual2 = self.create_user("Sarah Mitchell", "sarah@demo.com", "password", "casual", location="Denver, CO", bio="Volunteer and local parks advocate.")
        casual3 = self.create_user("David Lee", "david@demo.com", "password", "casual", location="Austin, TX", bio="Education and technology enthusiast.")
        casual4 = self.create_user("Emma Davis", "emma@demo.com", "password", "casual", location="Portland, OR", bio="Local art and culture supporter.")
        gov1 = self.create_user("Department of Community Development", "gov@demo.com", "password", "government", organization_name="Department of Community Development", location="Washington, DC", bio="Public-sector agency for community programs.")
        gov2 = self.create_user("Ministry of Education", "education@gov.demo", "password", "government", organization_name="Ministry of Education", location="Washington, DC", bio="National education policy and outreach.")
        ngo1 = self.create_user("GreenFuture Initiative", "ngo@demo.com", "password", "ngo", organization_name="GreenFuture Initiative", location="Washington, DC", bio="Environment and sustainability NGO.")
        ngo2 = self.create_user("Helping Hands Foundation", "helping@ngo.demo", "password", "ngo", organization_name="Helping Hands Foundation", location="Baltimore, MD", bio="Community support and education NGO.")
        ngo3 = self.create_user("HealthAid Network", "health@ngo.demo", "password", "ngo", organization_name="HealthAid Network", location="Chicago, IL", bio="Community health outreach network.")

        self.create_post(casual2, "Just attended a local park cleanup organized by amazing volunteers! Small actions lead to big changes. #CommunityLove #CleanParks", "Community")
        self.create_post(casual3, "Great discussion on youth education and technology today. Empowering the next generation is key to a better future.", "Education")
        self.create_post(casual4, "Local art festival this weekend! Excited to support talented artists in our community. #SupportLocal", "Events")
        self.create_post(casual1, "Ideas for improving public transportation: more frequent buses, safer stops, and cleaner schedules. What would help your area most?", "Transportation")
        self.send_friend_request(casual2, casual1); self.respond_friend_request(1, casual1, True)
        self.send_friend_request(casual3, casual1)
        self.add_comment(casual2, 4, "More frequent buses during peak hours would be a game changer.")
        self.toggle_like(casual1, 1); self.toggle_like(casual2, 4); self.toggle_like(casual3, 4)

        self.send_partner_request(ngo1, gov1, "We would like to collaborate on reforestation and youth climate programs.")
        self.respond_partner_request(1, gov1, True)
        self.send_partner_request(ngo2, gov1, "Seeking approval for a community education partnership.")
        self.respond_partner_request(2, gov1, True)
        self.send_partner_request(ngo3, gov2, "Health education outreach proposal.")
        aid = self.create_agreement(gov1, ngo2, "Community Education & Awareness Program", "Implement education and awareness outreach in underserved communities.", 250000)
        self.add_document(ngo2, "Collaboration Agreement_Draft_v2.pdf", agreement_id=aid)
        self.add_document(ngo2, "Budget Breakdown.xlsx", agreement_id=aid)
        self.add_document(gov1, "Compliance Certificate.pdf", agreement_id=aid)
        p1 = self.create_project(ngo1, "Clean Rivers Initiative", gov1, "Environment")
        self.update_project_progress(p1, ngo1, 45, "active")
        self.create_report(ngo1, p1, "Q2 Impact Report", "River cleanup completed in three districts with 128 volunteers.")
        self.send_message(ngo1, gov1, "Good morning! We’re excited to share the latest progress on our reforestation project.", "Reforestation_Q2_Report.pdf")
        self.send_message(gov1, ngo1, "Thank you for the update. Please also share the budget utilization.")
