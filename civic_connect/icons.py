import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import tkinter as tk

ICON_BY_TEXT = {
    "home": "home",
    "landing page": "home",
    "feed": "rss",
    "post": "plus",
    "friends": "users",
    "add friend": "user-plus",
    "messages": "message-circle",
    "message": "message-circle",
    "comment": "message-square",
    "send": "send",
    "profile": "settings",
    "notifications": "bell",
    "mark all read": "check",
    "dashboard": "layout-dashboard",
    "partners": "handshake",
    "connect": "handshake",
    "new agreement": "file-check-2",
    "agreements": "file-check-2",
    "projects": "folder-kanban",
    "new project": "folder-kanban",
    "reports": "bar-chart-3",
    "export csv": "download",
    "download": "download",
    "search": "search",
    "filter": "search",
    "upload document": "upload",
    "upload doc": "upload",
    "submit report": "check",
    "create project": "check",
    "create & submit": "check",
    "create account": "user-plus",
    "sign up": "user-plus",
    "log in": "log-in",
    "log out": "log-out",
    "save profile": "check",
    "accept": "check",
    "approve": "check",
    "reject": "x",
    "clear": "x",
    "request changes": "x",
    "resubmit": "upload",
    "mark active": "check",
    "mark completed": "check",
    "report": "bar-chart-3",
    "open": "file-check-2",
    "update": "check",
    "attach": "paperclip",
}

_CACHE: Dict[Tuple[str, str, int], tk.PhotoImage] = {}


def resource_dir() -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    candidates = []
    if bundled:
        candidates.append(Path(bundled) / "rescources")
    candidates.extend([
        Path(__file__).resolve().parents[1] / "rescources",
        Path.cwd() / "rescources",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def normalize_button_text(text: str) -> str:
    value = " ".join(text.replace("\n", " ").split()).lower()
    for mark in ("->", "→"):
        value = value.replace(mark, "")
    return value.strip()


def icon_for_text(text: str) -> Optional[str]:
    value = normalize_button_text(text)
    if value in ICON_BY_TEXT:
        return ICON_BY_TEXT[value]
    for key, icon in ICON_BY_TEXT.items():
        if key in value:
            return icon
    return None


def get_icon(name: str, tone: str = "gold", size: int = 16) -> Optional[tk.PhotoImage]:
    key = (name, tone, size)
    if key in _CACHE:
        return _CACHE[key]
    path = resource_dir() / f"{name}-{tone}.png"
    if not path.exists():
        return None
    image = tk.PhotoImage(file=str(path))
    factor = max(1, round(image.width() / size))
    if factor > 1:
        image = image.subsample(factor, factor)
    _CACHE[key] = image
    return image
