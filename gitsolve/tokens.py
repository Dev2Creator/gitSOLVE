# gitSOLVE ✦ "Iris" Design Token System — gradient-era theme engine
# Software for Humans. Underground code. Zero hype.
#
# Every visual role used across the UI is declared ONCE per theme here.
# No raw hex lives anywhere else in the codebase.

from typing import Dict, List, Optional, Tuple

from rich.text import Text

from gitsolve.config import load_config

# --- Color primitives --------------------------------------------------------
def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """Parses #RGB or #RRGGBB into an (r, g, b) tuple with a warm fallback."""
    v = str(value).strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    try:
        return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    except Exception:
        return 240, 128, 101


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, int(c))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def lerp_color(start: str, end: str, t: float) -> str:
    """Interpolates between two hex colors in truecolor space (t in 0..1)."""
    ta = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb(start)
    r2, g2, b2 = hex_to_rgb(end)
    return rgb_to_hex((
        round(r1 + (r2 - r1) * ta),
        round(g1 + (g2 - g1) * ta),
        round(b1 + (b2 - b1) * ta),
    ))


# --- Gradient renderables (Charm lipgloss-style sweeps) ----------------------
def gradient_text(
    text: str,
    start: str,
    end: str,
    bold: bool = False,
    italic: bool = False,
) -> Text:
    """Returns a Rich Text with a per-cell horizontal truecolor gradient sweep."""
    t = Text()
    chars = list(text)
    n = len(chars)
    for i, ch in enumerate(chars):
        color = lerp_color(start, end, i / (n - 1)) if n > 1 else start
        style = color
        if bold:
            style = f"bold {style}"
        if italic:
            style = f"italic {style}"
        t.append(ch, style=style)
    return t


def gradient_badge(
    label: str,
    start: str,
    end: str,
    fg: str = "black",
    bold: bool = True,
    padding: int = 1,
) -> Text:
    """Returns a Lip Gloss-style rounded badge with a gradient background sweep."""
    text = f"{' ' * padding}{label}{' ' * padding}"
    t = Text()
    n = len(text)
    for i, ch in enumerate(text):
        color = lerp_color(start, end, i / (n - 1)) if n > 1 else start
        style = f"{fg} on {color}"
        if bold:
            style = f"bold {style}"
        t.append(ch, style=style)
    return t


def gradient_meter(
    score: int,
    max_val: int = 100,
    width: int = 10,
    start: str = "#F29265",
    end: str = "#F6C177",
    empty: str = "#3A2619",
    show_score: bool = True,
    glyph: str = "▰",
) -> str:  # glyph kept for API compatibility; fills always render as ▰/▱
    """Returns markup for a glossy gradient fill meter, e.g. ▰▰▰▰▱▱ 74/100."""
    clamped = max(0, min(int(score), max_val))
    filled = round((clamped / max_val) * width) if max_val > 0 else 0
    filled = max(0, min(width, filled))
    empty_n = width - filled
    fill_glyph, empty_glyph = "▰", "▱"

    segments: List[str] = []
    for i in range(filled):
        color = lerp_color(start, end, i / (filled - 1)) if filled > 1 else lerp_color(start, end, 0.5)
        segments.append(f"[{color}]{fill_glyph}[/]")
    if empty_n > 0:
        segments.append(f"[{empty}]{empty_glyph * empty_n}[/]")

    res = "".join(segments)
    if show_score:
        res += f" [bold {start}]{clamped}[/][{empty}]/{max_val}[/]"
    return res


def gradient_rule(width: int, start: str, end: str, glyph: str = "─") -> str:
    """Returns markup for a horizontal gradient hairline rule."""
    if width <= 0:
        return ""
    segments = []
    for i in range(width):
        color = lerp_color(start, end, i / (width - 1)) if width > 1 else start
        segments.append(f"[{color}]{glyph}[/]")
    return "".join(segments)


def gradient_sparkline(
    values: List[int],
    start: str = "#9CCB86",
    end: str = "#F29265",
    width: Optional[int] = None,
) -> str:
    """Returns markup for a Unicode sparkline with a gradient color sweep."""
    if not values:
        return ""
    bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    vals = list(values)
    if width and len(vals) > width:
        # Downsample evenly into `width` buckets
        bucket = len(vals) / width
        vals = [max(vals[int(i * bucket): max(int(i * bucket) + 1, int((i + 1) * bucket))]) for i in range(width)]
    min_v, max_v = min(vals), max(vals)
    span = max_v - min_v

    segments = []
    n = len(vals)
    for i, v in enumerate(vals):
        idx = int(((v - min_v) / span) * (len(bars) - 1)) if span > 0 else 4
        color = lerp_color(start, end, i / (n - 1)) if n > 1 else start
        segments.append(f"[{color}]{bars[idx]}[/]")
    return "".join(segments)


# --- Design roles ------------------------------------------------------------
# Extra semantic roles shared by every theme (overridable per theme).
DEFAULT_ROLES: Dict[str, str] = {
    "surface": "#33261B",     # dark inset strip behind badges
    "success": "#9CCB86",     # verified / healthy
    "warn": "#E2A957",        # caution / gaps
    "danger": "#E07A79",      # failing / errors
    "info": "#7FA6D9",        # AI / informational
}

def role(theme: Dict[str, str], key: str) -> str:
    """Fetches a semantic color role from a theme with a safe fallback."""
    if key in theme and theme[key]:
        return theme[key]
    return DEFAULT_ROLES.get(key, theme.get("accent", "#F29265"))


# --- The four core themes (with new Iris roles) ------------------------------
THEMES: Dict[str, Dict[str, str]] = {
    "warm_earth": {
        "name": "Warm Earth",
        "accent": "#F29265",
        "cream": "#D7C0AA",
        "muted": "#614B39",
        "border": "#6B4E36",
        "selected": "#2D4F7C",
        "gold": "#F6C177",
        "mythic": "#EB6F92",
        # Iris roles
        "surface": "#33261B",
        "success": "#9CCB86",
        "warn": "#E2A957",
        "danger": "#E07A79",
        "info": "#7FA6D9",
        "grad_a": "#F29265",
        "grad_b": "#F6C177",
    },
    "cyber_peach": {
        "name": "Cyber Peach",
        "accent": "#FF7B54",
        "cream": "#FFD59E",
        "muted": "#5B2A36",
        "border": "#A44569",
        "selected": "#831843",
        "gold": "#FFD93D",
        "mythic": "#FF6B6B",
        "surface": "#3A1420",
        "success": "#7FE9B0",
        "warn": "#FFB35C",
        "danger": "#FF6B6B",
        "info": "#56C2E6",
        "grad_a": "#FF7B54",
        "grad_b": "#FFD93D",
    },
    "emerald_moss": {
        "name": "Emerald Moss",
        "accent": "#4ADE80",
        "cream": "#E2FCD6",
        "muted": "#1E3D29",
        "border": "#2D6A4F",
        "selected": "#065F46",
        "gold": "#FBBF24",
        "mythic": "#34D399",
        "surface": "#0B241A",
        "success": "#86EFAC",
        "warn": "#FBBF24",
        "danger": "#F87171",
        "info": "#7DD3FC",
        "grad_a": "#2D6A4F",
        "grad_b": "#4ADE80",
    },
    "lavender_night": {
        "name": "Lavender Night",
        "accent": "#C084FC",
        "cream": "#E9D5FF",
        "muted": "#3B1B54",
        "border": "#6B21A8",
        "selected": "#581C87",
        "gold": "#FDE047",
        "mythic": "#F472B6",
        "surface": "#241033",
        "success": "#A7F3D0",
        "warn": "#FDBA74",
        "danger": "#FB7185",
        "info": "#93C5FD",
        "grad_a": "#C084FC",
        "grad_b": "#F472B6",
    },
}


def get_current_theme() -> Dict[str, str]:
    """Reads the active theme from config (safe for modules that cannot import ui)."""
    cfg = load_config()
    return THEMES.get(cfg.get("theme", "warm_earth"), THEMES["warm_earth"])


# --- Tier classification visuals ----------------------------------------------
def tier_visual(overall: int, theme: Dict[str, str]) -> Tuple[str, str, str]:
    """Returns (label, gradient_start, gradient_end) for the overall score tier."""
    if overall >= 88:
        return "💎 MYTHIC SLEEPER", role(theme, "mythic") or theme["mythic"], theme["gold"]
    if overall >= 74:
        return "🔥 SOLID GOLD", theme["gold"], theme["accent"]
    return "✨ HIDDEN GEM", theme["accent"], role(theme, "info")


def tier_icon(overall: int) -> str:
    """Compact one-glyph tier marker for board rows and menus."""
    if overall >= 88:
        return "💎"
    if overall >= 74:
        return "🔥"
    return "✨"


# --- Utility -------------------------------------------------------------------
def fmt_size(num_bytes: int) -> str:
    """Humanizes byte counts: 128 B • 4.2 kB • 1.3 MB."""
    n = float(num_bytes or 0)
    if n <= 0:
        return "0 B"
    for unit, div in (("MB", 1024 ** 2), ("kB", 1024)):
        if n >= div:
            return f"{n / div:.1f} {unit}"
    return f"{int(n)} B"
