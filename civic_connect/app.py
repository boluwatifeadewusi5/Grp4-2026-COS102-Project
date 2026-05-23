import gc
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Dict, Optional
from .backend import CivicBackend, BackendError, AuthError, PermissionError
from .theme import T, FONT
from .ui import clear, label, icon_label, button, entry, get_entry, text_box, card, tag, Scroll, Modal, toast, error

APP_NAME = "Civic Connect"
APP_VERSION = "Beta 1.2"

class CivicConnectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - {APP_VERSION}")
        self.geometry("1200x780")
        self.minsize(920, 620)
        self.configure(bg=T.bg)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        gc.set_threshold(900, 15, 15)
        self.backend = CivicBackend()
        self.current_user: Optional[Dict] = None
        self.selected_conversation_id: Optional[int] = None
        self.selected_agreement_id: Optional[int] = None
        self.feed_search = ""
        self.friend_search = ""
        self.partner_search = ""
        self.agreement_search = ""
        self.agreement_status_filter = "all"
        self.project_search = ""
        self.project_status_filter = "all"
        self.report_search = ""
        self.active_view = None
        self.active_view_args = ()
        self.refresh_job = None
        self.refresh_seconds = self.refresh_interval()
        self.refreshing = False
        self.last_refresh_error = ""
        self.last_interaction_at = time.monotonic()
        self.refresh_quiet_seconds = 2.0
        self._reset_count = 0
        self.root = tk.Frame(self, bg=T.bg)
        self.root.pack(fill="both", expand=True)
        for sequence in ("<Button>", "<KeyPress>"):
            self.bind_all(sequence, self.mark_user_activity, add="+")
        self.show_landing()
        self.schedule_refresh()

    # ---------- core layout ----------
    def reset(self):
        clear(self.root)
        self._reset_count += 1
        if self._reset_count >= 5:
            self._reset_count = 0
            self.after_idle(self.collect_garbage)

    def collect_garbage(self):
        try:
            gc.collect()
        except Exception:
            pass

    def mark_user_activity(self, _event=None):
        self.last_interaction_at = time.monotonic()

    def on_close(self):
        if self.refresh_job:
            try:
                self.after_cancel(self.refresh_job)
            except tk.TclError:
                pass
        for sequence in ("<Button>", "<KeyPress>"):
            try:
                self.unbind_all(sequence)
            except tk.TclError:
                pass
        try:
            self.backend.db.close()
        except Exception:
            pass
        self.destroy()

    def start_session(self, user: Dict):
        self.current_user = user
        self.selected_conversation_id = None
        self.selected_agreement_id = None
        self.feed_search = ""
        self.friend_search = ""
        self.partner_search = ""
        self.agreement_search = ""
        self.agreement_status_filter = "all"
        self.project_search = ""
        self.project_status_filter = "all"
        self.report_search = ""

    def set_entry_value(self, widget: tk.Entry, value: str):
        if value:
            widget.delete(0, "end")
            widget.insert(0, value)
            widget.config(fg=T.text)

    def text_value(self, widget: tk.Text, *placeholders: str) -> str:
        value = widget.get("1.0", "end").strip()
        return "" if value in placeholders else value

    def refresh_interval(self) -> int:
        try:
            seconds = int(os.environ.get("CIVIC_CONNECT_REFRESH_SECONDS", "5"))
        except ValueError:
            seconds = 5
        return max(1, min(5, seconds))

    def set_active_view(self, view, *args):
        self.active_view = view
        self.active_view_args = args

    def schedule_refresh(self):
        if self.refresh_job:
            try:
                self.after_cancel(self.refresh_job)
            except tk.TclError:
                pass
        self.refresh_job = self.after(self.refresh_seconds * 1000, self.auto_refresh)

    def should_skip_refresh(self) -> bool:
        if not self.current_user or not self.active_view:
            return True
        if time.monotonic() - self.last_interaction_at < self.refresh_quiet_seconds:
            return True
        focused = self.focus_get()
        if focused and focused.winfo_class() in {"Entry", "Text", "TCombobox"}:
            return True
        return any(isinstance(child, tk.Toplevel) for child in self.winfo_children())

    def auto_refresh(self):
        self.refresh_job = None
        try:
            if not self.refreshing and not self.should_skip_refresh():
                self.refreshing = True
                self.active_view(*self.active_view_args)
        except Exception as exc:
            self.last_refresh_error = str(exc)
        finally:
            self.refreshing = False
            self.schedule_refresh()

    def nav(self, public=True):
        n = tk.Frame(self.root, bg=T.bg, height=58)
        n.pack(fill="x"); n.pack_propagate(False)
        label(n, APP_NAME, 16, T.gold, T.bg, "bold").pack(side="left", padx=26)
        if public:
            for txt, cmd in [("HOME", self.show_landing), ("COMMUNITY", self.show_landing), ("RESOURCES", self.show_landing)]:
                button(n, txt, cmd, "ghost", pady=5, icon=self.icon_for_nav(txt)).pack(side="left", padx=4)
            button(n, "LOG IN", self.show_login, "outline", width=10, pady=6, icon="log-in").pack(side="right", padx=(4, 26))
            button(n, "SIGN UP", self.show_signup, "primary", width=10, pady=6, icon="user-plus").pack(side="right", padx=4)
        else:
            unread = self.backend.unread_count(self.current_user["id"])
            label(n, f"Alerts: {unread} | {self.current_user['full_name']} ({self.current_user['role'].title()})", 10, T.text, T.bg, "bold").pack(side="right", padx=26)
            button(n, "LOG OUT", self.logout, "outline", width=10, pady=6, icon="log-out").pack(side="right", padx=4)
            button(n, "WORKSPACE", self.route_home, "ghost", width=12, pady=6, icon="layout-dashboard").pack(side="right", padx=4)

    def icon_for_nav(self, name: str) -> str:
        return {
            "HOME": "home",
            "COMMUNITY": "users",
            "RESOURCES": "file-check-2",
            "Feed": "rss",
            "Friends": "users",
            "Messages": "message-circle",
            "Profile": "settings",
            "Notifications": "bell",
            "Dashboard": "layout-dashboard",
            "Partners": "handshake",
            "Agreements": "file-check-2",
            "Projects": "folder-kanban",
            "Reports": "bar-chart-3",
        }.get(name, "home")

    def logout(self):
        self.current_user = None
        self.selected_conversation_id = None
        self.selected_agreement_id = None
        self.show_landing()

    def route_home(self):
        if not self.current_user:
            self.show_landing(); return
        role = self.current_user["role"]
        if role == "casual": self.show_casual_home()
        else: self.show_org_home()

    # ---------- public ----------
    def show_landing(self):
        self.set_active_view(None)
        public = self.current_user is None
        self.reset(); self.nav(public=public)
        s = Scroll(self.root); s.pack(fill="both", expand=True)
        compact = 1 < self.winfo_width() < 1050
        main = tk.Frame(s.content, bg=T.bg, padx=34 if compact else 54, pady=32 if compact else 42); main.pack(fill="both", expand=True)
        hero = tk.Frame(main, bg=T.bg); hero.pack(fill="x")
        left = tk.Frame(hero, bg=T.bg)
        right = tk.Frame(hero, bg=T.bg)
        if compact:
            left.pack(fill="x", expand=True)
            right.pack(fill="x", expand=True, pady=(20, 0))
        else:
            left.pack(side="left", fill="both", expand=True)
            right.pack(side="right", fill="both", expand=True)
        label(left, "A PLATFORM FOR POSITIVE CHANGE", 10, T.gold, T.bg, "bold").pack(anchor="w")
        label(left, "CONNECT. COLLABORATE.", 31, T.text, T.bg, "bold").pack(anchor="w", pady=(16,0))
        label(left, "CREATE IMPACT.", 34, T.gold, T.bg, "bold").pack(anchor="w")
        label(left, "Government Agencies and NGOs connect, message, approve agreements, manage projects and reports.\nCasual Users have a separate social space with posts, comments, likes, friends, and private messages.", 12, T.muted, T.bg, wrap=600).pack(anchor="w", pady=18)
        row = tk.Frame(left, bg=T.bg); row.pack(anchor="w")
        if public:
            button(row, "GET STARTED", self.show_signup, "primary", width=18, icon="user-plus").pack(side="left", padx=(0,10))
            button(row, "LOG IN", self.show_login, "outline", width=14, icon="log-in").pack(side="left")
        else:
            button(row, "OPEN WORKSPACE", self.route_home, "primary", width=18, icon="layout-dashboard").pack(side="left", padx=(0,10))
            button(row, "PROFILE", self.show_profile, "outline", width=14, icon="settings").pack(side="left")
        visual = tk.Frame(right, bg=T.bg); visual.pack(anchor="center", fill="x", padx=(26, 0))
        hub_o, hub = card(visual, padx=20, pady=18); hub_o.pack(fill="x", padx=36, pady=(0, 10))
        icon_label(hub, "network", "gold", 42, T.panel).pack(anchor="center")
        label(hub, APP_NAME, 18, T.gold, T.panel, "bold", anchor="center").pack(fill="x", pady=(8, 2))
        label(hub, "Role-aware collaboration, approvals, projects, reports, and messages.", 10, T.muted, T.panel, wrap=360, anchor="center", justify="center").pack(fill="x")
        flow = tk.Frame(visual, bg=T.bg); flow.pack(fill="x")
        for idx, (title, icon, color) in enumerate([
            ("Community", "users", T.blue),
            ("Partners", "handshake", T.red),
            ("Approvals", "file-check-2", T.gold),
            ("Shared Data", "cloud", T.green),
        ]):
            self.workflow_tile(flow, title, icon, color).grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)
        for col in range(2):
            flow.grid_columnconfigure(col, weight=1, uniform="workflow")
        stats = tk.Frame(main,bg=T.bg,pady=24); stats.pack(fill="x")
        for title,val,sub,color,icon in [
            ("Community", "People", "Posts, friends, messages", T.blue, "users"),
            ("NGO Workspace", "Partners", "Agreements and reports", T.red, "handshake"),
            ("Government", "Approvals", "Review and public initiatives", T.green, "landmark"),
            ("Data Access", "Cloud-ready", "Flexible project data", T.gold, "cloud"),
        ]:
            self.stat(stats,title,val,sub,color,icon).pack(side="left",fill="x",expand=True,padx=6)
        cards = tk.Frame(main,bg=T.bg,pady=22); cards.pack(fill="x")
        self.role_card(cards,"CASUAL USER","Posts, comments, likes, friendships, casual-only messaging",T.blue,"users").pack(side="left",fill="x",expand=True,padx=7)
        self.role_card(cards,"NGO","Discover government partners, agreements, messages, projects, reports",T.red,"handshake").pack(side="left",fill="x",expand=True,padx=7)
        self.role_card(cards,"GOVERNMENT","Approve partners, review agreements, manage public initiatives",T.green,"landmark").pack(side="left",fill="x",expand=True,padx=7)

    def workflow_tile(self, parent, title, icon, color):
        o, i = card(parent, padx=12, pady=10)
        icon_label(i, icon, "gold", 24, T.panel).pack(side="left", padx=(0, 10))
        label(i, title, 10, color, T.panel, "bold").pack(side="left")
        return o

    def stat(self,parent,title,value,sub,color,icon=None):
        o,i=card(parent)
        top=tk.Frame(i,bg=T.panel); top.pack(fill="x")
        label(top,value,20,color,T.panel,"bold").pack(side="left",anchor="w")
        if icon:
            icon_label(top,icon,"gold",24,T.panel).pack(side="right")
        label(i,title,10,T.text,T.panel,"bold").pack(anchor="w")
        label(i,sub,9,T.muted,T.panel).pack(anchor="w",pady=(4,0))
        return o

    def stat_grid(self, parent, items, columns=4):
        grid = tk.Frame(parent, bg=T.bg)
        for idx, item in enumerate(items):
            title, value, sub, color = item[:4]
            icon = item[4] if len(item) > 4 else None
            tile = self.stat(grid, title, value, sub, color, icon)
            tile.grid(row=idx // columns, column=idx % columns, sticky="ew", padx=5, pady=5)
        for col in range(columns):
            grid.grid_columnconfigure(col, weight=1, uniform="metric")
        return grid

    def role_card(self,parent,title,body,color,icon):
        o,i=card(parent)
        icon_label(i,icon,"gold",42,T.panel).pack(anchor="center",pady=(4,8))
        label(i,title,14,color,T.panel,"bold",anchor="center").pack(fill="x")
        label(i,body,10,T.muted,T.panel,wrap=300,anchor="center",justify="center").pack(fill="x",pady=10)
        return o

    def show_login(self):
        if self.current_user:
            self.route_home()
            return
        self.set_active_view(None)
        self.reset(); self.nav(public=True)
        main=tk.Frame(self.root,bg=T.bg,padx=40,pady=40); main.pack(fill="both",expand=True)
        o,i=card(main,padx=36,pady=32); o.place(relx=.5,rely=.43,anchor="center",width=500)
        icon_label(i,"network","gold",44,T.panel).pack(anchor="center")
        label(i,"WELCOME BACK",23,T.gold,T.panel,"bold",anchor="center").pack(fill="x",pady=(4,8))
        em=entry(i,"Email"); em.pack(fill="x",ipady=10,pady=7)
        pw=entry(i,"Password",show="*"); pw.pack(fill="x",ipady=10,pady=7)
        def do_login():
            try:
                self.start_session(self.backend.login(get_entry(em),get_entry(pw))); self.route_home()
            except Exception as exc: error(exc)
        button(i,"LOG IN",do_login,"primary",icon="log-in").pack(fill="x",pady=14)
        bottom=tk.Frame(i,bg=T.panel); bottom.pack(pady=10)
        label(bottom,"No account? ",9,T.muted,T.panel).pack(side="left"); button(bottom,"Sign up",self.show_signup,"ghost",pady=2).pack(side="left")

    def show_signup(self):
        if self.current_user:
            self.route_home()
            return
        self.set_active_view(None)
        self.reset(); self.nav(public=True)
        s=Scroll(self.root); s.pack(fill="both",expand=True)
        main=tk.Frame(s.content,bg=T.bg,padx=40,pady=28); main.pack(fill="both",expand=True)
        o,i=card(main,padx=36,pady=28); o.pack(anchor="center",ipadx=40)
        label(i,"CREATE ACCOUNT",22,T.gold,T.panel,"bold",anchor="center").pack(fill="x",pady=(0,12))
        fields={}
        for name,ph in [("full_name","Full name"),("email","Email"),("phone","Phone"),("org","Organization name (required for NGO/Government)"),("location","Location")]:
            e=entry(i,ph); e.pack(fill="x",ipady=9,pady=5); fields[name]=e
        pw=entry(i,"Password",show="*"); pw.pack(fill="x",ipady=9,pady=5)
        role=tk.StringVar(value="casual")
        rr=tk.Frame(i,bg=T.panel); rr.pack(fill="x",pady=8)
        for txt,val in [("Casual User","casual"),("NGO","ngo"),("Government Agency","government")]:
            tk.Radiobutton(rr,text=txt,variable=role,value=val,bg=T.panel,fg=T.text,selectcolor=T.panel2,activebackground=T.panel,activeforeground=T.gold).pack(side="left",padx=8)
        bio=text_box(i,3); bio.pack(fill="x",pady=5); bio.insert("1.0","Short bio")
        def do_signup():
            try:
                uid=self.backend.create_user(get_entry(fields["full_name"]),get_entry(fields["email"]),get_entry(pw),role.get(),get_entry(fields["phone"]),get_entry(fields["org"]),get_entry(fields["location"]),self.text_value(bio,"Short bio"))
                self.start_session(self.backend.user(uid)); self.route_home()
            except Exception as exc: error(exc)
        button(i,"CREATE ACCOUNT",do_signup,"primary",icon="user-plus").pack(fill="x",pady=12)

    # ---------- shell ----------
    def shell(self, active:str):
        self.reset(); self.nav(public=False)
        layout=tk.Frame(self.root,bg=T.bg); layout.pack(fill="both",expand=True)
        side_width = 220 if self.winfo_width() < 1100 else 250
        side=tk.Frame(layout,bg=T.bg2,width=side_width,padx=14,pady=18); side.pack(side="left",fill="y"); side.pack_propagate(False)
        label(side,self.current_user["full_name"],12,T.gold,T.bg2,"bold",wrap=210).pack(anchor="w")
        label(side,self.current_user["role"].upper(),9,T.muted,T.bg2,"bold").pack(anchor="w",pady=(0,14))
        if self.current_user["role"]=="casual":
            items=[("Feed",self.show_casual_home),("Friends",self.show_friends),("Messages",self.show_casual_messages),("Profile",self.show_profile),("Notifications",self.show_notifications)]
        else:
            items=[("Dashboard",self.show_org_home),("Partners",self.show_partners),("Messages",self.show_org_messages),("Agreements",self.show_agreements),("Projects",self.show_projects),("Reports",self.show_reports),("Notifications",self.show_notifications)]
        for name,cmd in items:
            button(side,name,cmd,"primary" if name==active else "ghost",pady=9,icon=self.icon_for_nav(name)).pack(fill="x",pady=3)
        button(side,"About Civic Connect",self.show_landing,"outline",pady=7,icon="home").pack(side="bottom",fill="x")
        content=Scroll(layout,T.bg); content.pack(side="left",fill="both",expand=True)
        body=tk.Frame(content.content,bg=T.bg,padx=26,pady=22); body.pack(fill="both",expand=True)
        return body

    # ---------- casual ----------
    def show_casual_home(self):
        self.set_active_view(self.show_casual_home)
        body=self.shell("Feed"); uid=self.current_user["id"]
        counts=self.backend.dashboard_counts(uid)
        label(body,"Casual Social Feed",22,T.text,T.bg,"bold").pack(anchor="w")
        label(body,"Only Casual Users can post, like, comment, add friends, and message here.",10,T.muted,T.bg).pack(anchor="w",pady=(0,12))
        button(body,"EXPORT CSV",self.export_summary,"outline",width=14,icon="download").pack(anchor="e")
        metric_items=[("Posts",str(counts["posts"]),"current count",T.blue,"rss"),("Friends",str(counts["friends"]),"current count",T.green,"users"),("Messages",str(counts["messages"]),"current count",T.gold,"message-circle"),("Unread",str(counts["notifications"]),"current count",T.warning,"bell")]
        self.stat_grid(body,metric_items,columns=4).pack(fill="x")
        search_row=tk.Frame(body,bg=T.bg); search_row.pack(fill="x",pady=(12,0))
        search=entry(search_row,"Search posts, topics, people"); self.set_entry_value(search,self.feed_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        def apply_search():
            self.feed_search=get_entry(search); self.show_casual_home()
        button(search_row,"SEARCH",apply_search,"outline",width=10,pady=4,icon="search").pack(side="left",padx=6)
        if self.feed_search:
            button(search_row,"CLEAR",lambda:(setattr(self,"feed_search",""),self.show_casual_home()),"ghost",width=8,pady=4,icon="x").pack(side="left")
        comp_o,comp=card(body); comp_o.pack(fill="x",pady=12)
        new=text_box(comp,3); new.pack(fill="x"); new.insert("1.0","What's on your mind?")
        topic=entry(comp,"Topic e.g. Community"); topic.pack(fill="x",ipady=7,pady=6)
        def post():
            try: self.backend.create_post(uid,self.text_value(new,"What's on your mind?"),get_entry(topic) or "General"); self.show_casual_home()
            except Exception as exc: error(exc)
        button(comp,"POST",post,"primary",width=12,icon="plus").pack(anchor="e")
        posts = self.backend.feed(uid,self.feed_search)
        comments = self.backend.recent_comments_for_posts([p["id"] for p in posts])
        for p in posts:
            self.post_widget(body,p,comments.get(p["id"], []))

    def post_widget(self,parent,p,comments):
        o,i=card(parent); o.pack(fill="x",pady=8)
        label(i,f"{p['full_name']} | {p['topic']} | {p['created_at']}",10,T.gold,T.panel,"bold").pack(anchor="w")
        label(i,p["body"],11,T.text,T.panel,wrap=850).pack(anchor="w",pady=8)
        acts=tk.Frame(i,bg=T.panel); acts.pack(fill="x")
        def like():
            try: self.backend.toggle_like(self.current_user["id"],p["id"]); self.show_casual_home()
            except Exception as exc: error(exc)
        like_text = f"{'LIKED' if p['liked_by_me'] else 'LIKE'} {p['like_count']}"
        button(acts,like_text,like,"outline",pady=4,icon="heart").pack(side="left")
        label(acts,f"Comments {p['comment_count']}",10,T.muted,T.panel).pack(side="left",padx=12)
        ce=entry(acts,"Write a comment..."); ce.pack(side="left",fill="x",expand=True,ipady=6,padx=8)
        def comment():
            try: self.backend.add_comment(self.current_user["id"],p["id"],get_entry(ce)); self.show_casual_home()
            except Exception as exc: error(exc)
        button(acts,"COMMENT",comment,"primary",pady=4,icon="message-square").pack(side="left")
        for c in comments:
            label(i,f"   {c['full_name']}: {c['body']}",9,T.muted,T.panel,wrap=800).pack(anchor="w",pady=2)

    def show_friends(self):
        self.set_active_view(self.show_friends)
        body=self.shell("Friends"); uid=self.current_user["id"]
        label(body,"Friends & Requests",22,T.text,T.bg,"bold").pack(anchor="w")
        search_row=tk.Frame(body,bg=T.bg); search_row.pack(fill="x",pady=(8,2))
        search=entry(search_row,"Search suggested users"); self.set_entry_value(search,self.friend_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        def apply_search():
            self.friend_search=get_entry(search); self.show_friends()
        button(search_row,"SEARCH",apply_search,"outline",width=10,pady=4,icon="search").pack(side="left",padx=6)
        if self.friend_search:
            button(search_row,"CLEAR",lambda:(setattr(self,"friend_search",""),self.show_friends()),"ghost",width=8,pady=4,icon="x").pack(side="left")
        data=self.backend.friends_and_requests(uid)
        cols=tk.Frame(body,bg=T.bg); cols.pack(fill="x",pady=10)
        sections=[("Friends",data["friends"]),("Incoming Requests",data["incoming"]),("Sent Requests",data["outgoing"]),("Suggested Users",self.backend.suggested_casual_users(uid,self.friend_search))]
        for idx,(title,items) in enumerate(sections):
            o,i=card(cols); o.grid(row=idx//2,column=idx%2,sticky="nsew",padx=5,pady=5)
            label(i,title,12,T.gold,T.panel,"bold").pack(anchor="w")
            for item in items:
                r=tk.Frame(i,bg=T.panel2,padx=8,pady=6); r.pack(fill="x",pady=4)
                label(r,item["full_name"],9,T.text,T.panel2,"bold").pack(anchor="w")
                if title=="Incoming Requests":
                    button(r,"ACCEPT",lambda fid=item["id"]: self.respond_friend(fid,True),"primary",pady=3,icon="check").pack(side="left",padx=2)
                    button(r,"REJECT",lambda fid=item["id"]: self.respond_friend(fid,False),"danger",pady=3,icon="x").pack(side="left",padx=2)
                elif title=="Suggested Users":
                    button(r,"ADD FRIEND",lambda rid=item["id"]: self.add_friend(rid),"outline",pady=3,icon="user-plus").pack(anchor="e")
                elif title=="Friends":
                    button(r,"MESSAGE",lambda rid=item["other_id"]: self.open_casual_conversation(rid),"outline",pady=3,icon="message-circle").pack(anchor="e")
        for col in range(2):
            cols.grid_columnconfigure(col,weight=1,uniform="friend_section")

    def add_friend(self,rid):
        try: self.backend.send_friend_request(self.current_user["id"],rid); self.show_friends()
        except Exception as exc: error(exc)
    def respond_friend(self,fid,accept):
        try: self.backend.respond_friend_request(fid,self.current_user["id"],accept); self.show_friends()
        except Exception as exc: error(exc)
    def open_casual_conversation(self,other):
        try: self.selected_conversation_id=self.backend.get_or_create_conversation(self.current_user["id"],other); self.show_casual_messages()
        except Exception as exc: error(exc)

    def show_casual_messages(self):
        self.show_messages("Messages")

    def show_profile(self):
        self.set_active_view(self.show_profile)
        body=self.shell("Profile"); u=self.backend.user(self.current_user["id"])
        label(body,"Profile",22,T.text,T.bg,"bold").pack(anchor="w")
        fields={}
        for key,ph,val in [("full_name","Full Name",u["full_name"]),("phone","Phone",u["phone"]),("location","Location",u["location"]),("bio","Bio",u["bio"] or "")]:
            label(body,ph,9,T.gold,T.bg,"bold").pack(anchor="w",pady=(8,2)); e=entry(body,ph); e.delete(0,"end"); e.insert(0,val); e.config(fg=T.text); e.pack(fill="x",ipady=8); fields[key]=e
        def save():
            try:
                self.backend.update_profile(u["id"],get_entry(fields["full_name"]),get_entry(fields["phone"]),get_entry(fields["location"]),get_entry(fields["bio"])); self.current_user=self.backend.user(u["id"]); toast("Saved","Profile updated.")
            except Exception as exc: error(exc)
        button(body,"SAVE PROFILE",save,"primary",width=18,icon="check").pack(anchor="e",pady=12)

    # ---------- org ----------
    def show_org_home(self):
        self.set_active_view(self.show_org_home)
        body=self.shell("Dashboard"); uid=self.current_user["id"]; counts=self.backend.dashboard_counts(uid)
        label(body,f"{self.current_user['role'].title()} Dashboard",22,T.text,T.bg,"bold").pack(anchor="w")
        label(body,"Government and NGO workspaces are separate from Casual Users. Partnerships must be accepted before messages and agreements.",10,T.muted,T.bg,wrap=900).pack(anchor="w",pady=(0,12))
        button(body,"EXPORT CSV",self.export_summary,"outline",width=14,icon="download").pack(anchor="e")
        metric_items=[(k.replace("_"," ").title(),str(counts[k]),"current count",T.gold if "pending" in k else T.green) for k in ["partners","pending_requests","agreements","pending_agreements","projects","reports","notifications"]]
        self.stat_grid(body,metric_items,columns=4).pack(fill="x")
        panels=tk.Frame(body,bg=T.bg,pady=14); panels.pack(fill="x")
        self.org_list_panel(panels,"Recent Agreements",self.backend.agreements_for(uid),"title","status").pack(side="left",fill="both",expand=True,padx=6)
        self.org_list_panel(panels,"Projects",self.backend.projects_for(uid),"title","status").pack(side="left",fill="both",expand=True,padx=6)
        self.org_list_panel(panels,"Notifications",self.backend.notifications(uid),"title","body").pack(side="left",fill="both",expand=True,padx=6)

    def org_list_panel(self,parent,title,items,main_key,sub_key):
        o,i=card(parent); label(i,title,12,T.gold,T.panel,"bold").pack(anchor="w")
        for item in items[:6]:
            r=tk.Frame(i,bg=T.panel2,padx=8,pady=6); r.pack(fill="x",pady=4)
            label(r,str(item.get(main_key,"")),9,T.text,T.panel2,"bold",wrap=240).pack(anchor="w")
            label(r,str(item.get(sub_key,"")),8,T.muted,T.panel2,wrap=240).pack(anchor="w")
        if not items: label(i,"No records yet.",9,T.muted,T.panel).pack(anchor="w",pady=10)
        return o

    def export_summary(self):
        default_name=f"civic_connect_{self.current_user['role']}_summary.csv"
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile=default_name,filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path:
            return
        try:
            Path(path).write_text(self.backend.export_summary_csv(self.current_user["id"]),encoding="utf-8")
            toast("Exported",f"Saved {Path(path).name}.")
        except Exception as exc: error(exc)

    def show_partners(self):
        self.set_active_view(self.show_partners)
        body=self.shell("Partners"); uid=self.current_user["id"]
        label(body,"Partners & Requests",22,T.text,T.bg,"bold").pack(anchor="w")
        search_row=tk.Frame(body,bg=T.bg); search_row.pack(fill="x",pady=(8,2))
        search=entry(search_row,"Search discoverable organizations"); self.set_entry_value(search,self.partner_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        def apply_search():
            self.partner_search=get_entry(search); self.show_partners()
        button(search_row,"SEARCH",apply_search,"outline",width=10,pady=4,icon="search").pack(side="left",padx=6)
        if self.partner_search:
            button(search_row,"CLEAR",lambda:(setattr(self,"partner_search",""),self.show_partners()),"ghost",width=8,pady=4,icon="x").pack(side="left")
        data=self.backend.partners_and_requests(uid,self.partner_search)
        sections=[("Accepted Partners",data["partners"]),("Incoming Requests",data["incoming"]),("Outgoing Requests",data["outgoing"]),("Discover",self.backend.discover_orgs(uid,self.partner_search))]
        for title,items in sections:
            o,i=card(body); o.pack(fill="x",pady=8); label(i,title,13,T.gold,T.panel,"bold").pack(anchor="w")
            for item in items:
                r=tk.Frame(i,bg=T.panel2,padx=10,pady=8); r.pack(fill="x",pady=4)
                nm=item.get("organization_name") or item.get("full_name"); label(r,nm,10,T.text,T.panel2,"bold").pack(side="left")
                if title=="Incoming Requests":
                    button(r,"ACCEPT",lambda rid=item["id"]: self.respond_partner(rid,True),"primary",pady=3,icon="check").pack(side="right",padx=3)
                    button(r,"REJECT",lambda rid=item["id"]: self.respond_partner(rid,False),"danger",pady=3,icon="x").pack(side="right",padx=3)
                elif title=="Discover": button(r,"CONNECT",lambda oid=item["id"]: self.partner_request(oid),"outline",pady=3,icon="handshake").pack(side="right")
                elif title=="Accepted Partners":
                    button(r,"MESSAGE",lambda oid=item["other_id"]: self.open_org_conversation(oid),"outline",pady=3,icon="message-circle").pack(side="right",padx=3)
                    button(r,"NEW AGREEMENT",lambda oid=item["other_id"]: self.new_agreement_modal(oid),"primary",pady=3,icon="file-check-2").pack(side="right",padx=3)

    def partner_request(self,oid):
        try: self.backend.send_partner_request(self.current_user["id"],oid,"Requesting partnership through Civic Connect."); self.show_partners()
        except Exception as exc: error(exc)
    def respond_partner(self,rid,accept):
        try: self.backend.respond_partner_request(rid,self.current_user["id"],accept); self.show_partners()
        except Exception as exc: error(exc)
    def open_org_conversation(self,other):
        try: self.selected_conversation_id=self.backend.get_or_create_conversation(self.current_user["id"],other); self.show_org_messages()
        except Exception as exc: error(exc)

    # ---------- shared messages ----------
    def show_org_messages(self): self.show_messages("Messages")
    def show_messages(self, active):
        self.set_active_view(self.show_messages, active)
        body=self.shell(active); uid=self.current_user["id"]
        label(body,"Messages",22,T.text,T.bg,"bold").pack(anchor="w")
        layout=tk.Frame(body,bg=T.bg); layout.pack(fill="both",expand=True,pady=8)
        convs=self.backend.conversations_for(uid)
        if self.selected_conversation_id and not any(c["id"]==self.selected_conversation_id for c in convs):
            self.selected_conversation_id=None
        left=tk.Frame(layout,bg=T.bg,width=320); left.pack(side="left",fill="y",padx=(0,8)); left.pack_propagate(False)
        for c in convs:
            def pick(cid=c["id"]): self.selected_conversation_id=cid; self.show_messages(active)
            r=button(left,f"{c['other_name']}\n{c.get('last_message') or 'No messages yet'}",pick,"outline" if c["id"]==self.selected_conversation_id else "ghost",pady=9); r.pack(fill="x",pady=4)
        if not convs: label(left,"No conversations yet. Add a friend or partner first.",10,T.muted,T.bg,wrap=280).pack(anchor="w")
        center_o,center=card(layout); center_o.pack(side="left",fill="both",expand=True)
        if not self.selected_conversation_id and convs: self.selected_conversation_id=convs[0]["id"]
        if self.selected_conversation_id:
            conv=next((c for c in convs if c["id"]==self.selected_conversation_id),None)
            if conv:
                label(center,f"Conversation with {conv['other_name']}",14,T.gold,T.panel,"bold").pack(anchor="w")
                msg_area=tk.Frame(center,bg=T.panel); msg_area.pack(fill="both",expand=True,pady=8)
                for m in self.backend.messages(self.selected_conversation_id,uid):
                    bg=T.panel3 if m["sender_id"]==uid else T.panel2
                    b=tk.Frame(msg_area,bg=bg,padx=10,pady=7); b.pack(anchor="e" if m["sender_id"]==uid else "w",pady=4,padx=6)
                    label(b,m["full_name"],8,T.gold,bg,"bold").pack(anchor="w")
                    attach=("\nAttachment: "+m["attachment_name"]) if m["attachment_name"] else ""
                    label(b,m["body"]+attach,9,T.text,bg,wrap=500).pack(anchor="w")
                row=tk.Frame(center,bg=T.panel); row.pack(fill="x")
                e=entry(row,"Type your message..."); e.pack(side="left",fill="x",expand=True,ipady=9)
                att=tk.StringVar(value="")
                def filepick():
                    p=filedialog.askopenfilename();
                    if p: att.set(p.split('/')[-1])
                button(row,"ATTACH",filepick,"outline",width=8,icon="paperclip").pack(side="left",padx=5)
                def send():
                    try: self.backend.send_message(uid,conv["other_id"],get_entry(e),att.get()); self.show_messages(active)
                    except Exception as exc: error(exc)
                button(row,"SEND",send,"primary",width=8,icon="send").pack(side="left")
        else: label(center,"Select a conversation.",11,T.muted,T.panel).pack(anchor="w")

    # ---------- agreements ----------
    def show_agreements(self):
        self.set_active_view(self.show_agreements)
        body=self.shell("Agreements"); uid=self.current_user["id"]
        label(body,"Agreements",22,T.text,T.bg,"bold").pack(anchor="w")
        filter_row=tk.Frame(body,bg=T.bg); filter_row.pack(fill="x",pady=(8,10))
        search=entry(filter_row,"Search agreements"); self.set_entry_value(search,self.agreement_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        status=tk.StringVar(value=self.agreement_status_filter)
        cb=ttk.Combobox(filter_row,textvariable=status,values=["all","pending","changes_requested","approved","rejected","active","completed"],width=20,state="readonly"); cb.pack(side="left",padx=6)
        def apply_filters():
            self.agreement_search=get_entry(search); self.agreement_status_filter=status.get(); self.show_agreements()
        button(filter_row,"FILTER",apply_filters,"outline",width=10,pady=4,icon="search").pack(side="left")
        if self.agreement_search or self.agreement_status_filter!="all":
            button(filter_row,"CLEAR",lambda:(setattr(self,"agreement_search",""),setattr(self,"agreement_status_filter","all"),self.show_agreements()),"ghost",width=8,pady=4,icon="x").pack(side="left",padx=6)
        agreements=self.backend.agreements_for(uid,self.agreement_search,self.agreement_status_filter)
        for a in agreements:
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,a["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Government: {a['government_name']}   NGO: {a['ngo_name']}   Budget: ${a['budget']:,.2f}",9,T.muted,T.panel).pack(anchor="w")
            row=tk.Frame(i,bg=T.panel); row.pack(fill="x",pady=6)
            tag(row,a["status"].upper(),T.gold if a["status"] in ("pending","changes_requested") else T.success if a["status"]=="approved" else T.danger if a["status"]=="rejected" else T.muted).pack(side="left")
            button(row,"OPEN",lambda aid=a["id"]: self.show_agreement_detail(aid),"outline",pady=4,icon="file-check-2").pack(side="right")
        if not agreements: label(body,"No agreements match the current view.",10,T.muted,T.bg).pack(anchor="w")

    def new_agreement_modal(self,partner_id):
        m=Modal(self,"New Agreement",560,470); label(m.body,"Create Agreement",18,T.gold,T.bg,"bold").pack(anchor="w")
        title=entry(m.body,"Agreement title"); title.pack(fill="x",ipady=9,pady=5)
        budget=entry(m.body,"Budget e.g. 250000"); budget.pack(fill="x",ipady=9,pady=5)
        summary=text_box(m.body,8); summary.pack(fill="both",expand=True,pady=5); summary.insert("1.0","Agreement summary and terms...")
        def save():
            try:
                self.backend.create_agreement(self.current_user["id"],partner_id,get_entry(title),self.text_value(summary,"Agreement summary and terms..."),float(get_entry(budget) or 0)); m.destroy(); self.show_agreements()
            except Exception as exc: error(exc)
        button(m.body,"CREATE & SUBMIT",save,"primary",icon="check").pack(fill="x",pady=10)

    def show_agreement_detail(self,aid):
        self.set_active_view(self.show_agreement_detail, aid)
        body=self.shell("Agreements"); uid=self.current_user["id"]; a=self.backend.agreement(aid,uid)
        label(body,"Agreement Details & Approval",22,T.text,T.bg,"bold").pack(anchor="w")
        o,i=card(body); o.pack(fill="x",pady=8)
        label(i,a["title"],18,T.gold,T.panel,"bold").pack(anchor="w")
        label(i,a["summary"],10,T.text,T.panel,wrap=900).pack(anchor="w",pady=8)
        label(i,f"Government: {a['government_name']} | NGO: {a['ngo_name']} | Budget: ${a['budget']:,.2f} | Status: {a['status'].upper()}",10,T.muted,T.panel).pack(anchor="w")
        actions=tk.Frame(i,bg=T.panel); actions.pack(fill="x",pady=12)
        if self.current_user["role"]=="government" and a["status"] in ("pending","changes_requested"):
            button(actions,"APPROVE",lambda:self.status_agreement(aid,"approved"),"primary",icon="check").pack(side="left",padx=4)
            button(actions,"REQUEST CHANGES",lambda:self.status_agreement(aid,"changes_requested"),"outline",icon="x").pack(side="left",padx=4)
            button(actions,"REJECT",lambda:self.status_agreement(aid,"rejected"),"danger",icon="x").pack(side="left",padx=4)
        if a["status"]=="changes_requested":
            button(actions,"RESUBMIT",lambda:self.status_agreement(aid,"pending"),"primary",icon="upload").pack(side="left",padx=4)
        if a["status"]=="approved":
            button(actions,"MARK ACTIVE",lambda:self.status_agreement(aid,"active"),"success",icon="check").pack(side="left",padx=4)
        if a["status"]=="active":
            button(actions,"MARK COMPLETED",lambda:self.status_agreement(aid,"completed"),"success",icon="check").pack(side="left",padx=4)
        button(actions,"UPLOAD DOCUMENT",lambda:self.upload_doc(aid),"outline",icon="upload").pack(side="right")
        docs,di=card(body); docs.pack(side="left",fill="both",expand=True,padx=(0,6),pady=8)
        label(di,"Documents",13,T.gold,T.panel,"bold").pack(anchor="w")
        for d in self.backend.documents_for_agreement(aid,uid): label(di,f"Document: {d['name']} - {d['uploader']} - {d['created_at']}",9,T.muted,T.panel).pack(anchor="w",pady=4)
        ev,ei=card(body); ev.pack(side="left",fill="both",expand=True,padx=(6,0),pady=8)
        label(ei,"Activity Log",13,T.gold,T.panel,"bold").pack(anchor="w")
        for e in self.backend.agreement_events(aid,uid): label(ei,f"{e['event_type'].upper()} by {e['full_name']} - {e['note']}",9,T.muted,T.panel,wrap=420).pack(anchor="w",pady=4)

    def status_agreement(self,aid,status):
        try: self.backend.update_agreement_status(aid,self.current_user["id"],status,f"{self.current_user['full_name']} marked agreement as {status}."); self.show_agreement_detail(aid)
        except Exception as exc: error(exc)
    def upload_doc(self,aid):
        p=filedialog.askopenfilename();
        if not p: return
        try: self.backend.add_document(self.current_user["id"],Path(p).name,agreement_id=aid,path=p); self.show_agreement_detail(aid)
        except Exception as exc: error(exc)

    def upload_project_doc(self,pid):
        p=filedialog.askopenfilename();
        if not p: return
        try: self.backend.add_document(self.current_user["id"],Path(p).name,project_id=pid,path=p); self.show_projects()
        except Exception as exc: error(exc)

    # ---------- projects/reports ----------
    def show_projects(self):
        self.set_active_view(self.show_projects)
        body=self.shell("Projects"); uid=self.current_user["id"]
        label(body,"Projects",22,T.text,T.bg,"bold").pack(anchor="w")
        top=tk.Frame(body,bg=T.bg); top.pack(fill="x",pady=(8,10))
        search=entry(top,"Search projects"); self.set_entry_value(search,self.project_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        status=tk.StringVar(value=self.project_status_filter)
        cb=ttk.Combobox(top,textvariable=status,values=["all","planning","active","paused","blocked","completed"],width=16,state="readonly"); cb.pack(side="left",padx=6)
        def apply_filters():
            self.project_search=get_entry(search); self.project_status_filter=status.get(); self.show_projects()
        button(top,"FILTER",apply_filters,"outline",width=10,pady=4,icon="search").pack(side="left")
        if self.project_search or self.project_status_filter!="all":
            button(top,"CLEAR",lambda:(setattr(self,"project_search",""),setattr(self,"project_status_filter","all"),self.show_projects()),"ghost",width=8,pady=4,icon="x").pack(side="left",padx=6)
        button(body,"NEW PROJECT",self.new_project_modal,"primary",width=16,icon="folder-kanban").pack(anchor="e")
        projects=self.backend.projects_for(uid,self.project_search,self.project_status_filter)
        for p in projects:
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,p["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Focus: {p['focus_area']} | Status: {p['status']} | Progress: {p['progress']}% | Partner: {p.get('partner_name') or 'None'}",9,T.muted,T.panel).pack(anchor="w")
            inputs=tk.Frame(i,bg=T.panel); inputs.pack(fill="x",pady=(8,4))
            progress=entry(inputs,"Progress 0-100"); progress.pack(side="left",fill="x",expand=True,ipady=6)
            project_status=entry(inputs,"Status: planning, active, paused, blocked, completed"); project_status.pack(side="left",fill="x",expand=True,ipady=6,padx=6)
            actions=tk.Frame(i,bg=T.panel); actions.pack(fill="x",pady=(0,4))
            button(actions,"UPDATE",lambda pid=p["id"],current=p["progress"],current_status=p["status"],pe=progress,se=project_status:self.update_project(pid,current,current_status,pe,se),"outline",pady=4,icon="check").pack(side="left")
            button(actions,"UPLOAD DOC",lambda pid=p["id"]:self.upload_project_doc(pid),"outline",pady=4,icon="upload").pack(side="right",padx=4)
            button(actions,"REPORT",lambda pid=p["id"]:self.report_modal(pid),"primary",pady=4,icon="bar-chart-3").pack(side="right")
            docs=self.backend.documents_for_project(p["id"],uid)
            for d in docs[:4]:
                label(i,f"Document: {d['name']} - {d['uploader']} - {d['created_at']}",9,T.muted,T.panel).pack(anchor="w",pady=2)
        if not projects:
            label(body,"No projects match the current view.",10,T.muted,T.bg).pack(anchor="w",pady=10)
    def new_project_modal(self):
        m=Modal(self,"New Project",540,420); label(m.body,"New Project",18,T.gold,T.bg,"bold").pack(anchor="w")
        title=entry(m.body,"Project title"); title.pack(fill="x",ipady=9,pady=5)
        focus=entry(m.body,"Focus area"); focus.pack(fill="x",ipady=9,pady=5)
        partners=self.backend.partners_and_requests(self.current_user["id"])["partners"]
        partner_var=tk.StringVar(value="")
        label(m.body,"Optional partner",10,T.muted,T.bg).pack(anchor="w")
        cb=ttk.Combobox(m.body,textvariable=partner_var,values=[f"{p['other_id']}|{p['full_name']}" for p in partners]); cb.pack(fill="x",pady=5)
        def save():
            try:
                pid=int(partner_var.get().split("|")[0]) if partner_var.get() else None
                self.backend.create_project(self.current_user["id"],get_entry(title),pid,get_entry(focus)); m.destroy(); self.show_projects()
            except Exception as exc: error(exc)
        button(m.body,"CREATE PROJECT",save,"primary",icon="check").pack(fill="x",pady=12)
    def update_project(self,pid,current,current_status,pe,se):
        try: self.backend.update_project_progress(pid,self.current_user["id"],int(get_entry(pe) or current),get_entry(se) or current_status); self.show_projects()
        except Exception as exc: error(exc)
    def report_modal(self,pid):
        m=Modal(self,"Submit Report",560,460); label(m.body,"Submit Report",18,T.gold,T.bg,"bold").pack(anchor="w")
        title=entry(m.body,"Report title"); title.pack(fill="x",ipady=9,pady=5)
        body=text_box(m.body,8); body.pack(fill="both",expand=True,pady=5)
        def save():
            try: self.backend.create_report(self.current_user["id"],pid,get_entry(title),body.get("1.0","end").strip()); m.destroy(); self.show_reports()
            except Exception as exc: error(exc)
        button(m.body,"SUBMIT REPORT",save,"primary",icon="check").pack(fill="x",pady=10)

    def show_reports(self):
        self.set_active_view(self.show_reports)
        body=self.shell("Reports"); label(body,"Reports",22,T.text,T.bg,"bold").pack(anchor="w")
        search_row=tk.Frame(body,bg=T.bg); search_row.pack(fill="x",pady=(8,10))
        search=entry(search_row,"Search reports"); self.set_entry_value(search,self.report_search); search.pack(side="left",fill="x",expand=True,ipady=7)
        def apply_search():
            self.report_search=get_entry(search); self.show_reports()
        button(search_row,"SEARCH",apply_search,"outline",width=10,pady=4,icon="search").pack(side="left",padx=6)
        if self.report_search:
            button(search_row,"CLEAR",lambda:(setattr(self,"report_search",""),self.show_reports()),"ghost",width=8,pady=4,icon="x").pack(side="left")
        reports=self.backend.reports_for(self.current_user["id"],self.report_search)
        for r in reports:
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,r["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Project: {r['project_title']} | Author: {r['author']} | {r['created_at']}",9,T.gold,T.panel).pack(anchor="w")
            label(i,r["body"],10,T.muted,T.panel,wrap=900).pack(anchor="w",pady=5)
        if not reports:
            label(body,"No reports match the current view.",10,T.muted,T.bg).pack(anchor="w",pady=10)

    def show_notifications(self):
        self.set_active_view(self.show_notifications)
        active="Notifications"; body=self.shell(active); uid=self.current_user["id"]
        label(body,"Notifications",22,T.text,T.bg,"bold").pack(anchor="w")
        button(body,"MARK ALL READ",lambda:(self.backend.mark_notifications_read(uid),self.show_notifications()),"outline",width=16,icon="check").pack(anchor="e")
        for n in self.backend.notifications(uid):
            o,i=card(body); o.pack(fill="x",pady=5)
            label(i,("Unread: " if not n["is_read"] else "")+n["title"],12,T.gold if not n["is_read"] else T.text,T.panel,"bold").pack(anchor="w")
            label(i,n["body"],10,T.muted,T.panel,wrap=850).pack(anchor="w")
            label(i,n["created_at"],8,T.faint,T.panel).pack(anchor="e")
