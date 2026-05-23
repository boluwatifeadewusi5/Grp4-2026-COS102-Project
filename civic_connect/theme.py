from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    bg: str = "#111214"
    bg2: str = "#17191c"
    panel: str = "#1d2024"
    panel2: str = "#24272c"
    panel3: str = "#2b2e35"
    border: str = "#3b3f46"
    text: str = "#f0f0ea"
    muted: str = "#a8a8a0"
    faint: str = "#72756f"
    gold: str = "#f1c84b"
    gold2: str = "#b9982e"
    blue: str = "#7f8ea8"
    red: str = "#b46458"
    green: str = "#93a56b"
    success: str = "#7fb069"
    danger: str = "#d05c4a"
    warning: str = "#ddad3f"
    white: str = "#ffffff"

T = Theme()
FONT = "Segoe UI"
