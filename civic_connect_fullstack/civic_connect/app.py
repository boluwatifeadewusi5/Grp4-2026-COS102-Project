import tkinter as tk
from tkinter import ttk, filedialog
from typing import Dict, Optional
from .backend import CivicBackend, BackendError, AuthError, PermissionError
from .theme import T, FONT
from .ui import clear, label, button, entry, get_entry, text_box, card, tag, Scroll, Modal, toast, error

class CivicConnectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Civic Connect — Full Working Tkinter + SQLite")
        self.geometry("1320x850")
        self.minsize(1120, 720)
        self.configure(bg=T.bg)
        self.backend = CivicBackend()
        self.current_user: Optional[Dict] = None
        self.selected_conversation_id: Optional[int] = None
        self.selected_agreement_id: Optional[int] = None
        self.root = tk.Frame(self, bg=T.bg)
        self.root.pack(fill="both", expand=True)
        self.show_landing()

    # ---------- core layout ----------
    def reset(self):
        clear(self.root)

    def nav(self, public=True):
        n = tk.Frame(self.root, bg=T.bg, height=58)
        n.pack(fill="x"); n.pack_propagate(False)
        label(n, "▛  CIVIC CONNECT", 16, T.gold, T.bg, "bold").pack(side="left", padx=26)
        if public:
            for txt, cmd in [("HOME", self.show_landing), ("COMMUNITY", self.show_landing), ("RESOURCES", self.show_landing)]:
                button(n, txt, cmd, "ghost", pady=5).pack(side="left", padx=4)
            button(n, "LOG IN", self.show_login, "outline", width=10, pady=6).pack(side="right", padx=(4, 26))
            button(n, "SIGN UP", self.show_signup, "primary", width=10, pady=6).pack(side="right", padx=4)
        else:
            unread = self.backend.unread_count(self.current_user["id"])
            label(n, f"🔔 {unread}   {self.current_user['full_name']} ({self.current_user['role'].title()})", 10, T.text, T.bg, "bold").pack(side="right", padx=26)
            button(n, "LOG OUT", self.logout, "outline", width=10, pady=6).pack(side="right", padx=4)

    def logout(self):
        self.current_user = None
        self.show_landing()

    def route_home(self):
        if not self.current_user:
            self.show_landing(); return
        role = self.current_user["role"]
        if role == "casual": self.show_casual_home()
        else: self.show_org_home()

    # ---------- public ----------
    def show_landing(self):
        self.reset(); self.nav(public=True)
        s = Scroll(self.root); s.pack(fill="both", expand=True)
        main = tk.Frame(s.content, bg=T.bg, padx=54, pady=42); main.pack(fill="both", expand=True)
        hero = tk.Frame(main, bg=T.bg); hero.pack(fill="x")
        left = tk.Frame(hero, bg=T.bg); left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(hero, bg=T.bg); right.pack(side="right", fill="both", expand=True)
        label(left, "A PLATFORM FOR POSITIVE CHANGE", 10, T.gold, T.bg, "bold").pack(anchor="w")
        label(left, "CONNECT. COLLABORATE.", 31, T.text, T.bg, "bold").pack(anchor="w", pady=(16,0))
        label(left, "CREATE IMPACT.", 34, T.gold, T.bg, "bold").pack(anchor="w")
        label(left, "Government Agencies and NGOs connect, message, approve agreements, manage projects and reports.\nCasual Users have a separate social space with posts, comments, likes, friends, and private messages.", 12, T.muted, T.bg, wrap=600).pack(anchor="w", pady=18)
        row = tk.Frame(left, bg=T.bg); row.pack(anchor="w")
        button(row, "GET STARTED →", self.show_signup, "primary", width=18).pack(side="left", padx=(0,10))
        button(row, "LOG IN", self.show_login, "outline", width=14).pack(side="left")
        c = tk.Canvas(right, width=430, height=280, bg=T.bg, highlightthickness=0); c.pack(anchor="center")
        c.create_oval(165, 60, 285, 180, outline=T.gold2, width=2); c.create_text(225,120,text="▛",fill=T.gold,font=(FONT,42,"bold"))
        for x,y,t in [(225,30,"🤝"),(70,125,"👥"),(380,125,"🌐"),(225,245,"💬")]:
            c.create_line(225,120,x,y,fill=T.gold2,dash=(3,3)); c.create_oval(x-30,y-30,x+30,y+30,outline=T.border,width=2); c.create_text(x,y,text=t,font=(FONT,20),fill=T.text)
        c.create_text(225,270,text="Strict role separation enforced by backend",fill=T.muted,font=(FONT,9,"bold"))
        stats = tk.Frame(main,bg=T.bg,pady=24); stats.pack(fill="x")
        for title,val,sub,color in [("Casual Users","4 demo","Posts, friends, messages",T.blue),("NGOs","3 demo","Partnerships and reports",T.red),("Government","2 demo","Review and approvals",T.green),("Backend","SQLite","Fully persistent local DB",T.gold)]:
            self.stat(stats,title,val,sub,color).pack(side="left",fill="x",expand=True,padx=6)
        label(main,"DEMO LOGINS",16,T.gold,T.bg,"bold",anchor="center").pack(fill="x",pady=(8,10))
        demos = "Casual: alex@demo.com / password     NGO: ngo@demo.com / password     Government: gov@demo.com / password"
        label(main,demos,12,T.text,T.bg,anchor="center").pack(fill="x")
        cards = tk.Frame(main,bg=T.bg,pady=22); cards.pack(fill="x")
        self.role_card(cards,"CASUAL USER","Posts, comments, likes, friendships, casual-only messaging",T.blue).pack(side="left",fill="x",expand=True,padx=7)
        self.role_card(cards,"NGO","Discover government partners, agreements, messages, projects, reports",T.red).pack(side="left",fill="x",expand=True,padx=7)
        self.role_card(cards,"GOVERNMENT","Approve partners, review agreements, manage public initiatives",T.green).pack(side="left",fill="x",expand=True,padx=7)

    def stat(self,parent,title,value,sub,color):
        o,i=card(parent); label(i,value,22,color,T.panel,"bold").pack(anchor="w"); label(i,title,10,T.text,T.panel,"bold").pack(anchor="w"); label(i,sub,9,T.muted,T.panel).pack(anchor="w",pady=(4,0)); return o

    def role_card(self,parent,title,body,color):
        o,i=card(parent); label(i,"●",36,color,T.panel,"bold",anchor="center").pack(fill="x"); label(i,title,14,color,T.panel,"bold",anchor="center").pack(fill="x"); label(i,body,10,T.muted,T.panel,wrap=300,anchor="center",justify="center").pack(fill="x",pady=10); return o

    def show_login(self):
        self.reset(); self.nav(public=True)
        main=tk.Frame(self.root,bg=T.bg,padx=40,pady=40); main.pack(fill="both",expand=True)
        o,i=card(main,padx=36,pady=32); o.place(relx=.5,rely=.43,anchor="center",width=500)
        label(i,"▛",36,T.gold,T.panel,"bold",anchor="center").pack(fill="x")
        label(i,"WELCOME BACK",23,T.gold,T.panel,"bold",anchor="center").pack(fill="x",pady=(4,8))
        em=entry(i,"Email"); em.pack(fill="x",ipady=10,pady=7)
        pw=entry(i,"Password",show="*"); pw.pack(fill="x",ipady=10,pady=7)
        def do_login():
            try:
                self.current_user=self.backend.login(get_entry(em),get_entry(pw)); self.route_home()
            except Exception as exc: error(exc)
        button(i,"LOG IN →",do_login,"primary").pack(fill="x",pady=14)
        label(i,"Demo: alex@demo.com, ngo@demo.com, gov@demo.com — password: password",9,T.muted,T.panel,wrap=430,anchor="center").pack(fill="x")
        bottom=tk.Frame(i,bg=T.panel); bottom.pack(pady=10)
        label(bottom,"No account? ",9,T.muted,T.panel).pack(side="left"); button(bottom,"Sign up",self.show_signup,"ghost",pady=2).pack(side="left")

    def show_signup(self):
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
                uid=self.backend.create_user(get_entry(fields["full_name"]),get_entry(fields["email"]),get_entry(pw),role.get(),get_entry(fields["phone"]),get_entry(fields["org"]),get_entry(fields["location"]),bio.get("1.0","end").strip())
                self.current_user=self.backend.user(uid); self.route_home()
            except Exception as exc: error(exc)
        button(i,"CREATE ACCOUNT →",do_signup,"primary").pack(fill="x",pady=12)

    # ---------- shell ----------
    def shell(self, active:str):
        self.reset(); self.nav(public=False)
        layout=tk.Frame(self.root,bg=T.bg); layout.pack(fill="both",expand=True)
        side=tk.Frame(layout,bg=T.bg2,width=250,padx=16,pady=20); side.pack(side="left",fill="y"); side.pack_propagate(False)
        label(side,self.current_user["full_name"],12,T.gold,T.bg2,"bold",wrap=210).pack(anchor="w")
        label(side,self.current_user["role"].upper(),9,T.muted,T.bg2,"bold").pack(anchor="w",pady=(0,14))
        if self.current_user["role"]=="casual":
            items=[("Feed",self.show_casual_home),("Friends",self.show_friends),("Messages",self.show_casual_messages),("Profile",self.show_profile),("Notifications",self.show_notifications)]
        else:
            items=[("Dashboard",self.show_org_home),("Partners",self.show_partners),("Messages",self.show_org_messages),("Agreements",self.show_agreements),("Projects",self.show_projects),("Reports",self.show_reports),("Notifications",self.show_notifications)]
        for name,cmd in items:
            button(side,name,cmd,"primary" if name==active else "ghost",pady=9).pack(fill="x",pady=3)
        button(side,"Landing Page",self.show_landing,"outline",pady=7).pack(side="bottom",fill="x")
        content=Scroll(layout,T.bg); content.pack(side="left",fill="both",expand=True)
        body=tk.Frame(content.content,bg=T.bg,padx=26,pady=22); body.pack(fill="both",expand=True)
        return body

    # ---------- casual ----------
    def show_casual_home(self):
        body=self.shell("Feed"); uid=self.current_user["id"]
        counts=self.backend.dashboard_counts(uid)
        label(body,"Casual Social Feed",22,T.text,T.bg,"bold").pack(anchor="w")
        label(body,"Only Casual Users can post, like, comment, add friends, and message here.",10,T.muted,T.bg).pack(anchor="w",pady=(0,12))
        st=tk.Frame(body,bg=T.bg); st.pack(fill="x")
        for k,v,c in [("Posts",counts["posts"],T.blue),("Friends",counts["friends"],T.green),("Messages",counts["messages"],T.gold),("Unread",counts["notifications"],T.warning)]: self.stat(st,k,str(v),"live from SQLite",c).pack(side="left",fill="x",expand=True,padx=5)
        comp_o,comp=card(body); comp_o.pack(fill="x",pady=12)
        new=text_box(comp,3); new.pack(fill="x"); new.insert("1.0","What’s on your mind?")
        topic=entry(comp,"Topic e.g. Community"); topic.pack(fill="x",ipady=7,pady=6)
        def post():
            try: self.backend.create_post(uid,new.get("1.0","end").strip(),get_entry(topic) or "General"); self.show_casual_home()
            except Exception as exc: error(exc)
        button(comp,"POST",post,"primary",width=12).pack(anchor="e")
        for p in self.backend.feed(uid):
            self.post_widget(body,p)

    def post_widget(self,parent,p):
        o,i=card(parent); o.pack(fill="x",pady=8)
        label(i,f"{p['full_name']}  •  {p['topic']}  •  {p['created_at']}",10,T.gold,T.panel,"bold").pack(anchor="w")
        label(i,p["body"],11,T.text,T.panel,wrap=850).pack(anchor="w",pady=8)
        acts=tk.Frame(i,bg=T.panel); acts.pack(fill="x")
        def like():
            try: self.backend.toggle_like(self.current_user["id"],p["id"]); self.show_casual_home()
            except Exception as exc: error(exc)
        button(acts,("♥" if p["liked_by_me"] else "♡")+f" {p['like_count']}",like,"outline",pady=4).pack(side="left")
        label(acts,f"💬 {p['comment_count']}",10,T.muted,T.panel).pack(side="left",padx=12)
        ce=entry(acts,"Write a comment..."); ce.pack(side="left",fill="x",expand=True,ipady=6,padx=8)
        def comment():
            try: self.backend.add_comment(self.current_user["id"],p["id"],get_entry(ce)); self.show_casual_home()
            except Exception as exc: error(exc)
        button(acts,"COMMENT",comment,"primary",pady=4).pack(side="left")
        for c in self.backend.comments_for_post(p["id"])[-3:]:
            label(i,f"   {c['full_name']}: {c['body']}",9,T.muted,T.panel,wrap=800).pack(anchor="w",pady=2)

    def show_friends(self):
        body=self.shell("Friends"); uid=self.current_user["id"]
        label(body,"Friends & Requests",22,T.text,T.bg,"bold").pack(anchor="w")
        data=self.backend.friends_and_requests(uid)
        cols=tk.Frame(body,bg=T.bg); cols.pack(fill="x",pady=10)
        for title,items in [("Friends",data["friends"]),("Incoming Requests",data["incoming"]),("Sent Requests",data["outgoing"]),("Suggested Users",self.backend.suggested_casual_users(uid))]:
            o,i=card(cols); o.pack(side="left",fill="both",expand=True,padx=5)
            label(i,title,12,T.gold,T.panel,"bold").pack(anchor="w")
            for item in items:
                r=tk.Frame(i,bg=T.panel2,padx=8,pady=6); r.pack(fill="x",pady=4)
                label(r,item["full_name"],9,T.text,T.panel2,"bold").pack(anchor="w")
                if title=="Incoming Requests":
                    button(r,"ACCEPT",lambda fid=item["id"]: self.respond_friend(fid,True),"primary",pady=3).pack(side="left",padx=2)
                    button(r,"REJECT",lambda fid=item["id"]: self.respond_friend(fid,False),"danger",pady=3).pack(side="left",padx=2)
                elif title=="Suggested Users":
                    button(r,"ADD FRIEND",lambda rid=item["id"]: self.add_friend(rid),"outline",pady=3).pack(anchor="e")
                elif title=="Friends":
                    button(r,"MESSAGE",lambda rid=item["other_id"]: self.open_casual_conversation(rid),"outline",pady=3).pack(anchor="e")

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
        body=self.shell("Profile"); u=self.backend.user(self.current_user["id"])
        label(body,"Profile",22,T.text,T.bg,"bold").pack(anchor="w")
        fields={}
        for key,ph,val in [("full_name","Full Name",u["full_name"]),("phone","Phone",u["phone"]),("location","Location",u["location"]),("bio","Bio",u["bio"] or "")]:
            label(body,ph,9,T.gold,T.bg,"bold").pack(anchor="w",pady=(8,2)); e=entry(body,ph); e.delete(0,"end"); e.insert(0,val); e.config(fg=T.text); e.pack(fill="x",ipady=8); fields[key]=e
        def save():
            try:
                self.backend.update_profile(u["id"],get_entry(fields["full_name"]),get_entry(fields["phone"]),get_entry(fields["location"]),get_entry(fields["bio"])); self.current_user=self.backend.user(u["id"]); toast("Saved","Profile updated.")
            except Exception as exc: error(exc)
        button(body,"SAVE PROFILE",save,"primary",width=18).pack(anchor="e",pady=12)

    # ---------- org ----------
    def show_org_home(self):
        body=self.shell("Dashboard"); uid=self.current_user["id"]; counts=self.backend.dashboard_counts(uid)
        label(body,f"{self.current_user['role'].title()} Dashboard",22,T.text,T.bg,"bold").pack(anchor="w")
        label(body,"Government and NGO workspaces are separate from Casual Users. Partnerships must be accepted before messages and agreements.",10,T.muted,T.bg,wrap=900).pack(anchor="w",pady=(0,12))
        st=tk.Frame(body,bg=T.bg); st.pack(fill="x")
        for k in ["partners","pending_requests","agreements","pending_agreements","projects","reports","notifications"]:
            self.stat(st,k.replace("_"," ").title(),str(counts[k]),"live metric",T.gold if "pending" in k else T.green).pack(side="left",fill="x",expand=True,padx=4)
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

    def show_partners(self):
        body=self.shell("Partners"); uid=self.current_user["id"]
        label(body,"Partners & Requests",22,T.text,T.bg,"bold").pack(anchor="w")
        data=self.backend.partners_and_requests(uid)
        sections=[("Accepted Partners",data["partners"]),("Incoming Requests",data["incoming"]),("Outgoing Requests",data["outgoing"]),("Discover",self.backend.discover_orgs(uid))]
        for title,items in sections:
            o,i=card(body); o.pack(fill="x",pady=8); label(i,title,13,T.gold,T.panel,"bold").pack(anchor="w")
            for item in items:
                r=tk.Frame(i,bg=T.panel2,padx=10,pady=8); r.pack(fill="x",pady=4)
                nm=item.get("organization_name") or item.get("full_name"); label(r,nm,10,T.text,T.panel2,"bold").pack(side="left")
                if title=="Incoming Requests":
                    button(r,"ACCEPT",lambda rid=item["id"]: self.respond_partner(rid,True),"primary",pady=3).pack(side="right",padx=3)
                    button(r,"REJECT",lambda rid=item["id"]: self.respond_partner(rid,False),"danger",pady=3).pack(side="right",padx=3)
                elif title=="Discover": button(r,"CONNECT",lambda oid=item["id"]: self.partner_request(oid),"outline",pady=3).pack(side="right")
                elif title=="Accepted Partners":
                    button(r,"MESSAGE",lambda oid=item["other_id"]: self.open_org_conversation(oid),"outline",pady=3).pack(side="right",padx=3)
                    button(r,"NEW AGREEMENT",lambda oid=item["other_id"]: self.new_agreement_modal(oid),"primary",pady=3).pack(side="right",padx=3)

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
        body=self.shell(active); uid=self.current_user["id"]
        label(body,"Messages",22,T.text,T.bg,"bold").pack(anchor="w")
        layout=tk.Frame(body,bg=T.bg); layout.pack(fill="both",expand=True,pady=8)
        convs=self.backend.conversations_for(uid)
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
                    attach=("\n📎 "+m["attachment_name"]) if m["attachment_name"] else ""
                    label(b,m["body"]+attach,9,T.text,bg,wrap=500).pack(anchor="w")
                row=tk.Frame(center,bg=T.panel); row.pack(fill="x")
                e=entry(row,"Type your message..."); e.pack(side="left",fill="x",expand=True,ipady=9)
                att=tk.StringVar(value="")
                def filepick():
                    p=filedialog.askopenfilename();
                    if p: att.set(p.split('/')[-1])
                button(row,"📎",filepick,"outline",width=4).pack(side="left",padx=5)
                def send():
                    try: self.backend.send_message(uid,conv["other_id"],get_entry(e),att.get()); self.show_messages(active)
                    except Exception as exc: error(exc)
                button(row,"SEND",send,"primary",width=8).pack(side="left")
        else: label(center,"Select a conversation.",11,T.muted,T.panel).pack(anchor="w")

    # ---------- agreements ----------
    def show_agreements(self):
        body=self.shell("Agreements"); uid=self.current_user["id"]
        label(body,"Agreements",22,T.text,T.bg,"bold").pack(anchor="w")
        for a in self.backend.agreements_for(uid):
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,a["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Government: {a['government_name']}   NGO: {a['ngo_name']}   Budget: ${a['budget']:,.2f}",9,T.muted,T.panel).pack(anchor="w")
            row=tk.Frame(i,bg=T.panel); row.pack(fill="x",pady=6)
            tag(row,a["status"].upper(),T.gold if a["status"] in ("pending","changes_requested") else T.success if a["status"]=="approved" else T.danger if a["status"]=="rejected" else T.muted).pack(side="left")
            button(row,"OPEN",lambda aid=a["id"]: self.show_agreement_detail(aid),"outline",pady=4).pack(side="right")
        if not self.backend.agreements_for(uid): label(body,"No agreements yet. Create one from an accepted partner.",10,T.muted,T.bg).pack(anchor="w")

    def new_agreement_modal(self,partner_id):
        m=Modal(self,"New Agreement",560,470); label(m.body,"Create Agreement",18,T.gold,T.bg,"bold").pack(anchor="w")
        title=entry(m.body,"Agreement title"); title.pack(fill="x",ipady=9,pady=5)
        budget=entry(m.body,"Budget e.g. 250000"); budget.pack(fill="x",ipady=9,pady=5)
        summary=text_box(m.body,8); summary.pack(fill="both",expand=True,pady=5); summary.insert("1.0","Agreement summary and terms...")
        def save():
            try:
                self.backend.create_agreement(self.current_user["id"],partner_id,get_entry(title),summary.get("1.0","end").strip(),float(get_entry(budget) or 0)); m.destroy(); self.show_agreements()
            except Exception as exc: error(exc)
        button(m.body,"CREATE & SUBMIT",save,"primary").pack(fill="x",pady=10)

    def show_agreement_detail(self,aid):
        body=self.shell("Agreements"); uid=self.current_user["id"]; a=self.backend.agreement(aid,uid)
        label(body,"Agreement Details & Approval",22,T.text,T.bg,"bold").pack(anchor="w")
        o,i=card(body); o.pack(fill="x",pady=8)
        label(i,a["title"],18,T.gold,T.panel,"bold").pack(anchor="w")
        label(i,a["summary"],10,T.text,T.panel,wrap=900).pack(anchor="w",pady=8)
        label(i,f"Government: {a['government_name']} | NGO: {a['ngo_name']} | Budget: ${a['budget']:,.2f} | Status: {a['status'].upper()}",10,T.muted,T.panel).pack(anchor="w")
        actions=tk.Frame(i,bg=T.panel); actions.pack(fill="x",pady=12)
        if self.current_user["role"]=="government":
            button(actions,"APPROVE",lambda:self.status_agreement(aid,"approved"),"primary").pack(side="left",padx=4)
            button(actions,"REQUEST CHANGES",lambda:self.status_agreement(aid,"changes_requested"),"outline").pack(side="left",padx=4)
            button(actions,"REJECT",lambda:self.status_agreement(aid,"rejected"),"danger").pack(side="left",padx=4)
        button(actions,"UPLOAD DOCUMENT",lambda:self.upload_doc(aid),"outline").pack(side="right")
        docs,di=card(body); docs.pack(side="left",fill="both",expand=True,padx=(0,6),pady=8)
        label(di,"Documents",13,T.gold,T.panel,"bold").pack(anchor="w")
        for d in self.backend.documents_for_agreement(aid,uid): label(di,f"📄 {d['name']} — {d['uploader']} — {d['created_at']}",9,T.muted,T.panel).pack(anchor="w",pady=4)
        ev,ei=card(body); ev.pack(side="left",fill="both",expand=True,padx=(6,0),pady=8)
        label(ei,"Activity Log",13,T.gold,T.panel,"bold").pack(anchor="w")
        for e in self.backend.agreement_events(aid,uid): label(ei,f"{e['event_type'].upper()} by {e['full_name']} — {e['note']}",9,T.muted,T.panel,wrap=420).pack(anchor="w",pady=4)

    def status_agreement(self,aid,status):
        try: self.backend.update_agreement_status(aid,self.current_user["id"],status,f"Government marked agreement as {status}."); self.show_agreement_detail(aid)
        except Exception as exc: error(exc)
    def upload_doc(self,aid):
        p=filedialog.askopenfilename();
        if not p: return
        try: self.backend.add_document(self.current_user["id"],p.split('/')[-1],agreement_id=aid,path=p); self.show_agreement_detail(aid)
        except Exception as exc: error(exc)

    # ---------- projects/reports ----------
    def show_projects(self):
        body=self.shell("Projects"); uid=self.current_user["id"]
        label(body,"Projects",22,T.text,T.bg,"bold").pack(anchor="w")
        button(body,"NEW PROJECT",self.new_project_modal,"primary",width=16).pack(anchor="e")
        for p in self.backend.projects_for(uid):
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,p["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Focus: {p['focus_area']} | Status: {p['status']} | Progress: {p['progress']}% | Partner: {p.get('partner_name') or 'None'}",9,T.muted,T.panel).pack(anchor="w")
            row=tk.Frame(i,bg=T.panel); row.pack(fill="x",pady=6)
            progress=entry(row,"Progress 0-100"); progress.pack(side="left",ipady=6)
            status=entry(row,"Status"); status.pack(side="left",ipady=6,padx=6)
            button(row,"UPDATE",lambda pid=p["id"],pe=progress,se=status:self.update_project(pid,pe,se),"outline",pady=4).pack(side="left")
            button(row,"REPORT",lambda pid=p["id"]:self.report_modal(pid),"primary",pady=4).pack(side="right")
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
        button(m.body,"CREATE PROJECT",save,"primary").pack(fill="x",pady=12)
    def update_project(self,pid,pe,se):
        try: self.backend.update_project_progress(pid,self.current_user["id"],int(get_entry(pe) or 0),get_entry(se) or "active"); self.show_projects()
        except Exception as exc: error(exc)
    def report_modal(self,pid):
        m=Modal(self,"Submit Report",560,460); label(m.body,"Submit Report",18,T.gold,T.bg,"bold").pack(anchor="w")
        title=entry(m.body,"Report title"); title.pack(fill="x",ipady=9,pady=5)
        body=text_box(m.body,8); body.pack(fill="both",expand=True,pady=5)
        def save():
            try: self.backend.create_report(self.current_user["id"],pid,get_entry(title),body.get("1.0","end").strip()); m.destroy(); self.show_reports()
            except Exception as exc: error(exc)
        button(m.body,"SUBMIT REPORT",save,"primary").pack(fill="x",pady=10)

    def show_reports(self):
        body=self.shell("Reports"); label(body,"Reports",22,T.text,T.bg,"bold").pack(anchor="w")
        for r in self.backend.reports_for(self.current_user["id"]):
            o,i=card(body); o.pack(fill="x",pady=7)
            label(i,r["title"],13,T.text,T.panel,"bold").pack(anchor="w")
            label(i,f"Project: {r['project_title']} | Author: {r['author']} | {r['created_at']}",9,T.gold,T.panel).pack(anchor="w")
            label(i,r["body"],10,T.muted,T.panel,wrap=900).pack(anchor="w",pady=5)

    def show_notifications(self):
        active="Notifications"; body=self.shell(active); uid=self.current_user["id"]
        label(body,"Notifications",22,T.text,T.bg,"bold").pack(anchor="w")
        button(body,"MARK ALL READ",lambda:(self.backend.mark_notifications_read(uid),self.show_notifications()),"outline",width=16).pack(anchor="e")
        for n in self.backend.notifications(uid):
            o,i=card(body); o.pack(fill="x",pady=5)
            label(i,("● " if not n["is_read"] else "")+n["title"],12,T.gold if not n["is_read"] else T.text,T.panel,"bold").pack(anchor="w")
            label(i,n["body"],10,T.muted,T.panel,wrap=850).pack(anchor="w")
            label(i,n["created_at"],8,T.faint,T.panel).pack(anchor="e")
