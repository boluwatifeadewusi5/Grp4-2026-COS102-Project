import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import tkinter as tk

_CACHE: Dict[Tuple[str, str, int], tk.PhotoImage] = {}
FALLBACK_ICON = "landmark"


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


def get_icon(name: str, tone: str = "gold", size: int = 16) -> Optional[tk.PhotoImage]:
    key = (name, tone, size)
    if key in _CACHE:
        return _CACHE[key]
    path = resource_dir() / f"{name}-{tone}.png"
    if not path.exists():
        path = resource_dir() / f"{FALLBACK_ICON}-{tone}.png"
    if not path.exists() and tone != "gold":
        path = resource_dir() / f"{FALLBACK_ICON}-gold.png"
    if not path.exists():
        return None
    image = tk.PhotoImage(file=path.resolve().as_posix())
    factor = max(1, round(image.width() / size))
    if factor > 1:
        image = image.subsample(factor, factor)
    _CACHE[key] = image
    return image
