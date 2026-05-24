import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from .theme import T, FONT
from .icons import get_icon

#defining functions for creating ui components eg(Label, button, entry etc..)
def clear(widget: tk.Widget):
    for child in widget.winfo_children():
        child.destroy()


def label(parent, text, size=10, color=None, bg=None, weight="normal", anchor="w", wrap=0, justify="left"):
    return tk.Label(parent, text=text, font=(FONT, size, weight), fg=color or T.text, bg=bg or parent.cget("bg"), anchor=anchor, justify=justify, wraplength=wrap)


def icon_label(parent, icon, tone="gold", size=32, bg=None):
    image = get_icon(icon, tone=tone, size=size)
    if image is None:
        return tk.Label(parent, text="", bg=bg or parent.cget("bg"))
    lbl = tk.Label(parent, image=image, bg=bg or parent.cget("bg"))
    lbl._icon_image = image
    return lbl


def button(parent, text, command: Optional[Callable] = None, variant="primary", width=None, pady=7, icon=None):
    colors = {
        "primary": (T.gold, "#111111", T.gold),
        "outline": (T.panel, T.gold, T.gold2),
        "ghost": (parent.cget("bg"), T.text, T.border),
        "danger": (T.panel, T.danger, T.danger),
        "success": (T.panel, T.success, T.success),
    }
    bg, fg, border = colors.get(variant, colors["ghost"])
    tone = "dark" if variant == "primary" else "gold"
    icon_image = get_icon(icon, tone=tone) if icon else None
    options = {
        "text": f" {text}" if icon_image else text,
        "command": command,
        "bg": bg,
        "fg": fg,
        "activebackground": T.panel2,
        "activeforeground": fg,
        "relief": "flat",
        "bd": 0,
        "highlightthickness": 1,
        "highlightbackground": border,
        "padx": 12,
        "pady": pady,
        "font": (FONT, 9, "bold"),
        "cursor": "hand2",
    }
    if icon_image:
        options["image"] = icon_image
        options["compound"] = "left"
    elif width is not None:
        options["width"] = width
    btn = tk.Button(parent, **options)
    btn._icon_image = icon_image
    return btn


def entry(parent, placeholder="", show: Optional[str] = None):
    e = tk.Entry(parent, bg=T.panel2, fg=T.faint, insertbackground=T.gold, relief="flat", bd=0, highlightthickness=1,
                 highlightbackground=T.border, font=(FONT, 10))
    e.insert(0, placeholder)
    e._placeholder = placeholder
    e._real_show = show

    def focus_in(_):
        if e.get() == placeholder:
            e.delete(0, "end")
            e.config(fg=T.text, show=show or "")

    def focus_out(_):
        if not e.get():
            e.insert(0, placeholder)
            e.config(fg=T.faint, show="")
    e.bind("<FocusIn>", focus_in)
    e.bind("<FocusOut>", focus_out)
    return e


def text_box(parent, height=4):
    t = tk.Text(parent, height=height, bg=T.panel2, fg=T.text, insertbackground=T.gold, relief="flat", bd=0,
                highlightthickness=1, highlightbackground=T.border, font=(FONT, 10), wrap="word")
    return t


def get_entry(e: tk.Entry) -> str:
    val = e.get().strip()
    return "" if hasattr(e, "_placeholder") and val == e._placeholder else val


def card(parent, padx=14, pady=12, bg=None):
    outer = tk.Frame(parent, bg=T.border)
    inner = tk.Frame(outer, bg=bg or T.panel, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


def tag(parent, text, color=None):
    return tk.Label(parent, text=text, bg=T.panel2, fg=color or T.gold, font=(FONT, 8, "bold"), padx=7, pady=2,
                    highlightthickness=1, highlightbackground=color or T.gold2)


def toast(title: str, body: str = ""):
    messagebox.showinfo(title, body or title)


def error(exc: Exception):
    messagebox.showerror("Civic Connect", str(exc))

#defining the scrollable and modal classes for the ui
class Scroll(tk.Frame):
    def __init__(self, parent, bg=None):
        super().__init__(parent, bg=bg or T.bg)
        self.canvas = tk.Canvas(self, bg=bg or T.bg, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=bg or T.bg)
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)
        self.bind("<Destroy>", self._destroy, add="+")

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._wheel)

    def _unbind_wheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _destroy(self, event):
        if event.widget is self:
            self._unbind_wheel()

    def _wheel(self, event):
        try:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")
        except tk.TclError:
            pass


class Modal(tk.Toplevel):
    def __init__(self, parent, title="Civic Connect", width=520, height=420):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=T.bg)
        app_icon = getattr(parent, "app_icon", None)
        if app_icon:
            self.iconphoto(False, app_icon)
        self.transient(parent)
        self.grab_set()
        self.body = tk.Frame(self, bg=T.bg, padx=20, pady=20)
        self.body.pack(fill="both", expand=True)
