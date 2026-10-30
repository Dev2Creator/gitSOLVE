# gitSOLVE ✦ SSS-Tier Terminal Interface (Charm Crush & Neofetch Edition)
# Software for Humans. Underground code. Zero hype.

import base64
import getpass
import os
from pathlib import Path
import platform
import socket
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import questionary
from rich import box
from rich.align import Align
from rich.cells import cell_len
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.measure import Measurement
from rich.panel import Panel
from rich.rule import Rule
from rich.segment import Segment
from rich.table import Table
from rich.text import Text

from gitsolve import __version__
from gitsolve import tokens as tk
from gitsolve.tokens import THEMES
from gitsolve.config import load_config
from gitsolve.scoring import EvidenceStatus
from gitsolve.animation import (
    render_meter,
    render_sparkline,
    render_language_bar,
    render_pill,
    render_sonar_sweep,
)

console = Console(highlight=False)

# --- Themes (Iris design tokens — declared in gitsolve/tokens.py) ------------
def get_theme() -> Dict[str, str]:
    cfg = load_config()
    theme_name = cfg.get("theme", "warm_earth")
    return THEMES.get(theme_name, THEMES["warm_earth"])

def accent() -> str:
    return get_theme()["accent"]

def cream() -> str:
    return get_theme()["cream"]

def muted() -> str:
    return get_theme()["muted"]

def border_color() -> str:
    return get_theme()["border"]

def selected_color() -> str:
    return get_theme()["selected"]

def get_layout_width() -> int:
    return min(104, max(56, console.width - 4))

def get_menu_indent() -> int:
    """Calculates left indentation to center Questionary prompts with the centered header."""
    w = get_layout_width()
    left_edge = max(0, (console.width - w) // 2)
    return max(0, left_edge + 2)

# --- Icons & Glyphs ---------------------------------------------------------
ICONS: Dict[str, str] = {
    "radar": "✦",
    "fresh": "⚡",
    "ai": "◈",
    "ask": "💬",
    "xray": "◎",
    "forks": "⑂",
    "compare": "⚔",
    "author": "👤",
    "lucky": "★",
    "vault": "◆",
    "theme": "◐",
    "config": "⚙",
    "limits": "📊",
    "velocity": "⚡",
    "readme": "📖",
    "tree": "🌳",
    "commits": "📜",
    "cross": "✕",
    "check": "✓",
    "star": "★",
    "gem": "💎",
    "arch": "◈",
    "wm": "❖",
    "warning": "⚠️ ",
}

def icon(name: str) -> str:
    cfg = load_config()
    mode = cfg.get("icons_mode", "auto")
    if mode == "nerd":
        nerd_overrides = {
            "arch": "\U000f08c7",
            "wm": "\U000f0ec0",
            "radar": "󰛶",
            "fresh": "󰁯",
        }
        if name in nerd_overrides:
            return nerd_overrides[name]
    elif mode == "ascii":
        ascii_overrides = {
            "radar": "*",
            "fresh": "~",
            "ai": "#",
            "xray": "@",
            "forks": "%",
            "compare": "=",
            "author": "@",
            "lucky": "!",
            "vault": "$",
            "theme": "+",
            "config": "?",
            "limits": "%",
            "velocity": "^",
            "readme": "D",
            "tree": "T",
            "commits": "C",
            "cross": "x",
            "check": "v",
            "star": "*",
            "gem": "*",
            "arch": ">",
            "wm": "#",
        }
        if name in ascii_overrides:
            return ascii_overrides[name]
    return ICONS.get(name, "✦")

# --- Mascot Definitions & High-Resolution TrueColor Rendering ---------------
MASCOTS: Dict[str, Dict[str, str]] = {
    "hoodie": {
        "name": "Hoodie Wink",
        "description": "Menhera-chan winking with sparkling stars",
        "file": "clean_mascot_hoodie.png",
    },
    "zerotwo_lean": {
        "name": "Zero Two Darling",
        "description": "Zero Two smiling and leaning forward",
        "file": "clean_mascot_zerotwo_lean.png",
    },
    "zerotwo_reach": {
        "name": "Zero Two Stargaze",
        "description": "Zero Two reaching out to the cosmos",
        "file": "clean_mascot_zerotwo_reach.png",
    },
    "rikka": {
        "name": "Rikka Wicked Eye",
        "description": "Rikka Chunibyo wicked eye & dark flame master",
        "file": "clean_mascot_rikka.png",
    },
    "peeker": {
        "name": "Desk Peeker",
        "description": "Cute anime girl peeking over your terminal",
        "file": "clean_mascot_peeker.png",
    },
    "pikachu": {
        "name": "Pikachu Spark",
        "description": "Cute electric companion cheering your discoveries",
        "file": "clean_mascot_pikachu.png",
    },
    "cheer": {
        "name": "Cheer Chibi",
        "description": "Blonde anime cheerleader celebrating code",
        "file": "clean_mascot_cheer.png",
    },
    "eyes": {
        "name": "Manga Glance",
        "description": "Aesthetic manga eye peeker",
        "file": "clean_mascot_eyes.png",
    },
    "emerald": {
        "name": "Emerald Aoko",
        "description": "Emerald-haired cyber anime girl",
        "file": "clean_mascot_emerald.png",
    },
    "katana": {
        "name": "Katana Blade",
        "description": "Samurai anime warrior with katana",
        "file": "clean_mascot_katana.png",
    },
    "logo": {
        "name": "Cyber Diamond",
        "description": "Vector mecha diamond prism emblem",
        "file": "gitsolve_anime_logo.png",
    },
    "crystal": {
        "name": "Celestial Prism",
        "description": "Minimalist procedural terminal prism",
        "file": "",
    },
}

_MASCOT_CACHE: Dict[str, List[Text]] = {}

def get_asset_path(filename: str) -> Optional[Path]:
    """Locates an asset file across workspace, config, or package paths."""
    if not filename:
        return None
    candidates = [
        Path(__file__).resolve().parent.parent / "assets" / filename,
        Path.cwd() / "assets" / filename,
        Path.home() / ".config" / "gitsolve" / "assets" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def render_image_halfblocks(
    image_path: Path,
    target_width_box: int = 38,
    max_lines: int = 16,
) -> List[Text]:
    """Converts a PNG image to high-definition 24-bit ANSI truecolor half-block characters (▀/▄) with transparent alpha."""
    cache_key = f"{image_path}:{target_width_box}:{max_lines}"
    if cache_key in _MASCOT_CACHE:
        return _MASCOT_CACHE[cache_key]

    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return []

    try:
        if not image_path.exists():
            return []
        im = Image.open(image_path).convert("RGBA")

        # Anime outline & eye sharpening filter to preserve facial details during downsampling
        im = ImageEnhance.Contrast(im).enhance(1.18)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=2))

        orig_w, orig_h = im.size
        aspect = orig_h / orig_w

        target_pixel_h = max_lines * 2
        target_cols = int(target_pixel_h / aspect)
        if target_cols > target_width_box:
            target_cols = target_width_box
            target_pixel_h = int(target_cols * aspect)
        if target_pixel_h % 2 != 0:
            target_pixel_h += 1

        im = im.resize((target_cols, target_pixel_h), Image.Resampling.LANCZOS)
        w, h = im.size

        pad_left = max(0, (target_width_box - w) // 2)
        lines: List[Text] = []
        for y in range(0, h, 2):
            t = Text(" " * pad_left)
            for x in range(w):
                r1, g1, b1, a1 = im.getpixel((x, y))
                r2, g2, b2, a2 = im.getpixel((x, y + 1)) if y + 1 < h else (0, 0, 0, 0)

                top_vis = a1 > 35
                bot_vis = a2 > 35
                if top_vis and bot_vis:
                    t.append("▀", style=f"rgb({r1},{g1},{b1}) on rgb({r2},{g2},{b2})")
                elif top_vis and not bot_vis:
                    t.append("▀", style=f"rgb({r1},{g1},{b1})")
                elif not top_vis and bot_vis:
                    t.append("▄", style=f"rgb({r2},{g2},{b2})")
                else:
                    t.append(" ")
            lines.append(t)
        _MASCOT_CACHE[cache_key] = lines
        return lines
    except Exception:
        return []

def get_artistic_emblem(theme: Dict[str, str]) -> List[Text]:
    """Handcrafted 7-line isometric celestial radar crystal emblem with theme-reactive palette."""
    cfg = load_config()
    mode = cfg.get("icons_mode", "auto")
    gold = theme.get("gold", "#FDE047")
    accent = theme.get("accent", "#C084FC")
    cream = theme.get("cream", "#E9D5FF")
    muted = theme.get("muted", "#3B1B54")
    highlight = "#38BDF8" if theme.get("accent") != "#4ADE80" else "#A7F3D0"

    if mode == "ascii":
        lines = [
            f"          [bold {gold}]*[/]         [bold {cream}].[/]         [bold {gold}]*[/]",
            f"        [dim {accent}].-----[/][{muted}]__[/][{accent}]###[/][{muted}]__[/][dim {accent}]-----.[/]",
            f"      [dim {accent}]./[/]  [{muted}]_##[/][{accent}]##[/][{cream}]#####[/][{accent}]##[/][{muted}]##_[/]  [dim {accent}]\\.[/]",
            f"    [bold {accent}]*---#[/][{accent}]--###[/][{cream}]#/[/] [bold {highlight}]-###-[/] [bold white]\\###[/][{accent}]--[/][bold {accent}]#---*[/]",
            f"      [dim {accent}]'\\/[/]  [{muted}]-##[/][{accent}]#_[/]   [bold {gold}]v[/]   [{accent}]_##[/][{muted}]-[/]  [dim {accent}]/'[/]",
            f"        [dim {accent}]'-----[/][{muted}]--[/][{accent}]###[/][{muted}]--[/][dim {accent}]-----'[/]",
            f"          [bold {gold}]*[/]         [bold {cream}].[/]         [bold {gold}]*[/]",
        ]
    else:
        lines = [
            f"        [bold {gold}]✦[/]         [bold {cream}]·[/]         [bold {gold}]✧[/]",
            f"      [dim {accent}].─────[/][{muted}]▄▄[/][{accent}]███[/][{muted}]▄▄[/][dim {accent}]─────.[/]",
            f"    [dim {accent}].╱[/]  [{muted}]▄██[/][{accent}]██[/][{cream}]█████[/][{accent}]██[/][{muted}]██▄[/]  [dim {accent}]╲.[/]",
            f"  [bold {accent}]✦──◈[/][{accent}]──███[/][{cream}]█◤[/] [bold {highlight}]▀███▀[/] [bold white]◥███[/][{accent}]──[/][bold {accent}]◈──✦[/]",
            f"    [dim {accent}]'╲[/]  [{muted}]▀██[/][{accent}]█▄[/]   [bold {gold}]▼[/]   [{accent}]▄██[/][{muted}]▀[/]  [dim {accent}]╱'[/]",
            f"      [dim {accent}]'─────[/][{muted}]▀▀[/][{accent}]███[/][{muted}]▀▀[/][dim {accent}]─────'[/]",
            f"        [bold {gold}]✧[/]         [bold {cream}]·[/]         [bold {gold}]✦[/]",
        ]
    return [Text.from_markup(l) for l in lines]

# --- Native Kitty Graphics & Mascot Lines -----------------------------------
def is_kitty() -> bool:
    """Checks whether the terminal supports native Kitty Graphics Protocol."""
    import sys as _sys
    return bool(
        _sys.stdout.isatty()
        and (
            os.environ.get("KITTY_WINDOW_ID")
            or "kitty" in os.environ.get("TERM", "").lower()
            or os.environ.get("TERM_PROGRAM") == "kitty"
            or (os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") and Path("/usr/bin/kitty").exists())
        )
    )

class KittyGraphic:
    """Renders the original PNG sharply using the native Kitty Graphics Protocol."""

    def __init__(self, path: Path, max_cols: int = 32, max_rows: int = 14):
        self.path = path
        self.rows = max_rows
        try:
            from PIL import Image
            with Image.open(path) as im:
                w, h = im.size
            self.cols = max(4, min(max_cols, int(max_rows * (w / h) / 0.48)))
        except Exception:
            self.cols = max_cols

    def __rich_console__(self, console, options):
        b64_path = base64.b64encode(str(self.path.resolve()).encode()).decode()
        yield Segment(f"\033_Ga=T,f=100,t=f,c={self.cols},r={self.rows},q=2;{b64_path}\033\\")
        yield Segment.line()
        for _ in range(self.rows - 1):
            yield Segment(" " * self.cols)
            yield Segment.line()

    def __rich_measure__(self, console, options):
        return Measurement(self.cols, self.cols)

def get_mascot_lines(theme: Dict[str, str], mascot_key: Optional[str] = None) -> List[Any]:
    """Returns rendered mascot (native Kitty PNG or ANSI halfblocks or geometric crystal)."""
    cfg = load_config()
    m_key = mascot_key or cfg.get("mascot", "hoodie")
    if m_key != "crystal" and m_key in MASCOTS:
        file_name = MASCOTS[m_key].get("file")
        if file_name:
            path = get_asset_path(file_name)
            if path and path.exists():
                if is_kitty():
                    return [KittyGraphic(path, max_cols=32, max_rows=14)]
                lines = render_image_halfblocks(path, target_width_box=32, max_lines=14)
                if lines:
                    return lines
    return get_artistic_emblem(theme)

def get_personalized_greeting(user_name: str = "", pronouns: str = "") -> str:
    """Returns an empathetic, personalized time-of-day greeting with name and pronouns."""
    hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        period = "Good morning"
        icon_greet = "🌅"
    elif 12 <= hour < 17:
        period = "Good afternoon"
        icon_greet = "☀️"
    elif 17 <= hour < 22:
        period = "Good evening"
        icon_greet = "🌆"
    else:
        period = "Late night shift"
        icon_greet = "🌙"

    name_str = (user_name or getpass.getuser()).strip()
    pronoun_str = f" ({pronouns.strip()})" if pronouns and pronouns.strip() else ""
    return f"{icon_greet} {period}, {name_str}{pronoun_str}! Radar ready."

def get_artistic_wordmark(theme: Dict[str, str]) -> List[Text]:
    """Crafted 3-line chiseled typography wordmark with theme-reactive gradient."""
    accent = theme.get("accent", "#F29265")
    cream = theme.get("cream", "#D7C0AA")
    gold = theme.get("gold", "#F6C177")
    muted = theme.get("muted", "#614B39")

    lines = [
        f"  [bold {accent}]█▀▀ █ ▀█▀[/]  [bold {cream}]█▀▀ █▀█ █[/]   [bold {gold}]█ █ █▀▀[/]",
        f"  [bold {accent}]█ █ █  █ [/]  [bold {cream}]▀▀█ █ █ █[/]   [bold {gold}]▀▄▀ █▀▀[/]",
        f"  [bold {muted}]▀▀▀ ▀  ▀ [/]  [bold {muted}]▀▀▀ ▀▀▀ ▀▀▀[/]  [bold {muted}] ▀  ▀▀▀[/]",
    ]
    return [Text.from_markup(l) for l in lines]

def print_banner(subtitle: str = "Underground Code. Zero Hype. Handcrafted Gems.") -> None:
    t = get_theme()
    cfg = load_config()
    emblem_lines = get_mascot_lines(t, cfg.get("mascot", "hoodie"))
    wordmark_lines = get_artistic_wordmark(t)
    grid = Table(box=None, expand=False, show_header=False, padding=(0, 2))
    grid.add_column("mascot", justify="center")
    grid.add_column("logo", justify="left")
    sub_text = Text(f"✦ {subtitle} ✦", style=f"bold {t['cream']}")
    grid.add_row(Group(*emblem_lines), Group(*wordmark_lines, Text(""), sub_text))
    console.print(Align.center(grid))
    console.print()

def print_header(title: str = "RADAR READY", status_text: str = "Ready — choose a command below") -> None:
    t = get_theme()
    w = get_layout_width()
    cfg = load_config()

    user_name = (cfg.get("user_name") or getpass.getuser()).strip()
    pronouns = (cfg.get("pronouns") or "").strip()
    curator_title = (cfg.get("curator_title") or "Sleeper Hunter").strip()
    mascot_key = cfg.get("mascot", "hoodie")
    mascot_name = MASCOTS.get(mascot_key, {}).get("name", "Celestial Prism")

    # Left Side: Native Mascot / Emblem + Themed Wordmark + Tagline Badges
    emblem_lines = get_mascot_lines(t, mascot_key)
    wordmark_lines = get_artistic_wordmark(t)
    tagline_badge = Text.from_markup(
        f"\n  [bold black on {t['accent']}] UNDERGROUND [/] [bold {t['cream']} on {t['border']}] ZERO HYPE [/] [bold black on {t['gold']}] GEMS [/]"
    )
    left_group = Group(*emblem_lines, Text(""), *wordmark_lines, tagline_badge)

    # Right Side: Neofetch System Telemetry & Personalized Greeting
    try:
        host = socket.gethostname()
        if host == "sandbox":
            host = os.environ.get("HOSTNAME") or "Spyderman"
    except Exception:
        host = "Spyderman"

    kernel = f"{platform.system()} {platform.release()}"
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP") or "Hyprland 0.56.2 (Wayland)"
    if not desktop_env or desktop_env == "none":
        desktop_env = "Hyprland 0.56.2 (Wayland)"

    right_table = Table(box=None, expand=True, padding=(0, 0), show_header=False)
    right_table.add_column("info", justify="left")

    greeting = get_personalized_greeting(user_name, pronouns)
    user_display = f"{user_name} ({pronouns})" if pronouns else user_name
    greet_line = Text.from_markup(f"[bold {t['gold']}]{greeting}[/]")
    user_host = Text.from_markup(f"[bold {t['accent']}]{user_display}[/] [dim white]@[/] [bold white]{host}[/]")
    divider = Text("──────────────────────⊙──────────────────────", style=t["muted"])

    archetype_line = Text.from_markup(f"[{t['gold']}]◈  →  [/][bold {t['cream']}]Archetype:[/] [bold {t['gold']}]{curator_title}[/]")
    mascot_line = Text.from_markup(f"[{t['accent']}]🐾  →  [/][bold {t['cream']}]Companion:[/] [bold {t['accent']}]{mascot_name}[/]")

    arch_glyph = icon("arch")
    arch_line = Text.from_markup(f"[{t['accent']}]{arch_glyph}  →  [/][bold white]{kernel}[/]")

    wm_glyph = icon("wm")
    wm_line = Text.from_markup(f"[{tk.role(t, 'info')}]{wm_glyph}  →  [/][bold white]{desktop_env}[/]")

    app_ver_line = Text.from_markup(f"[{t['gold']}]✦  →  [/][dim white]Python 3.14.7 • v{__version__}[/]")
    ai_line = Text.from_markup(f"[{t['accent']}]⚡  →  [/][bold {t['cream']}]Pollinations AI Engine[/]")
    radar_line = Text.from_markup(f"[{t['gold']}]◎  →  [/][{t['cream']}]Sleeper Spectrum: 2..7 ⭐[/]")

    right_table.add_row(greet_line)
    right_table.add_row(user_host)
    right_table.add_row(divider)
    right_table.add_row(archetype_line)
    right_table.add_row(mascot_line)
    right_table.add_row(arch_line)
    right_table.add_row(wm_line)
    right_table.add_row(app_ver_line)
    right_table.add_row(ai_line)
    right_table.add_row(radar_line)

    top_banner = Table(box=None, expand=True, padding=(0, 2), show_header=False)
    top_banner.add_column("mascot", justify="center", ratio=1)
    top_banner.add_column("sysinfo", justify="left", ratio=1)
    top_banner.add_row(left_group, right_table)

    # Telemetry Grid (Stats & Status)
    stats_grid = Table(box=None, expand=True, padding=(0, 1), show_header=False)
    stats_grid.add_column("c1", ratio=1)
    stats_grid.add_column("c2", ratio=1)
    stats_grid.add_column("c3", ratio=1)

    auth_label = f"[{t['accent']}]Token (5k/hr)[/]" if cfg.get("github_token") else f"[{t['muted']}]Public (60/hr)[/]"
    theme_name = THEMES.get(cfg.get("theme", "warm_earth"), {}).get("name", "Warm Earth")
    if "Ready" in status_text or "STANDBY" in status_text:
        status_display = f"[bold {t['success']}]● STANDBY[/]"
    elif "Scan" in status_text:
        status_display = f"[bold {t['gold']}]● SCANNING[/]"
    else:
        status_display = f"[bold {t['accent']}]● [/][{t['cream']}]{status_text[:14]}[/]"

    stats_grid.add_row(
        f"[{t['muted']}]STATUS[/]  {status_display}",
        f"[{t['muted']}]VAULT [/]  [bold {t['gold']}]{cfg.get('gems_discovered', 0)} saved[/]",
        f"[{t['muted']}]AUTH  [/]  {auth_label}",
    )
    stats_grid.add_row(
        f"[{t['muted']}]SCANS [/]  [{t['cream']}]{cfg.get('scans_completed', 0)} completed[/]",
        f"[{t['muted']}]THEME [/]  [{t['cream']}]{theme_name}[/]",
        f"[{t['muted']}]RADAR [/]  [bold {t['accent']}]Active (2..7 ⭐)[/]",
    )

    box_sep = Rule(style=t["border"])

    if w < 78:
        center_sep = Text("  ✦ ─── ⊙ ─── ✦  ", style=t["muted"])
        panel_content = Group(left_group, center_sep, right_table, box_sep, stats_grid)
    else:
        panel_content = Group(top_banner, box_sep, stats_grid)

    header_panel = Panel(
        panel_content,
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print(Align.center(header_panel))
    console.print()

def print_keymap_footer(hints: Optional[List[Tuple[str, str]]] = None) -> None:
    """OpenCode-style single-line keymap: accent key tokens with muted labels."""
    t = get_theme()
    w = get_layout_width()
    if not hints:
        hints = [("↑/↓", "navigate"), ("↵", "select"), ("/", "filter"), ("q", "quit")]
    line = Text()
    for i, (key, label) in enumerate(hints):
        if i:
            line.append("  ┊  ", style=t["muted"])
        line.append(f"[{key}]", style=f"bold {t['accent']}")
        line.append(f" {label}", style=t["muted"])
    footer_panel = Panel(
        line,
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 2),
        width=w,
    )
    console.print(Align.center(footer_panel))

# --- OpenCode-style primitives -------------------------------------------------
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

def spin_frame(n: int) -> str:
    """Returns the n-th braille spinner glyph (OpenCode-style)."""
    return SPINNER_FRAMES[n % len(SPINNER_FRAMES)]

def section_bar(title: str, width: Optional[int] = None) -> Text:
    """Clean accent-bar section header: ┃ TITLE ───────────."""
    t = get_theme()
    w = width or get_layout_width()
    label = f"┃ {title} "
    used = cell_len(label) + 2
    line = Text()
    line.append(label, style=f"bold {t['accent']}")
    line.append("─" * max(0, w - used), style=t["border"])
    return line

def status_dot(status: str) -> Text:
    """Colored dot + label status line (● scanning / ✓ done / ⚠ caution)."""
    t = get_theme()
    colors = {
        "ok": ("✓", t["success"]),
        "run": (spin_frame(0), t["accent"]),
        "warn": ("⚠", tk.role(t, "warn")),
        "err": ("✗", tk.role(t, "danger")),
        "ai": ("◈", tk.role(t, "info")),
        "idle": ("●", t["muted"]),
    }
    glyph, color = colors.get(status, colors["idle"])
    return Text(glyph, style=f"bold {color}")

# --- Questionary Styling & Centered Prompts ---------------------------------
def menu_style() -> questionary.Style:
    t = get_theme()
    return questionary.Style([
        ("qmark", f"fg:{t['accent']} bold"),
        ("question", f"fg:{t['cream']} bold"),
        ("answer", f"fg:{t['accent']} bold"),
        ("pointer", f"fg:{t['accent']} bold"),
        ("highlighted", f"bg:{t['selected']} fg:#FFFFFF bold"),
        ("selected", f"fg:{t['cream']}"),
        ("instruction", f"fg:{t['muted']}"),
    ])

def select_menu(
    choices: List[questionary.Choice],
    prompt: str = "",
    instruction: str = "(↑/↓ to move • enter to select)",
    **kwargs,
) -> Any:
    """Centered Questionary select prompt aligned with the centered header panel."""
    indent = get_menu_indent()
    ptr = (" " * indent) + "▸ "
    instr = ((" " * indent) + instruction) if instruction else ""
    return questionary.select(
        prompt,
        choices=choices,
        style=menu_style(),
        qmark="",
        pointer=ptr,
        instruction=instr,
        **kwargs,
    ).ask()

def command_choice(command: str, description: str, value: str, icon_glyph: str = "") -> questionary.Choice:
    w = min(84, max(52, get_layout_width() - 8))
    sym = icon_glyph if icon_glyph else "✦"
    c_len = cell_len(sym)
    pad = "  " if c_len == 1 else " "
    label = f" {sym}{pad}/{command:<9}  │  {description}"
    return questionary.Choice(label.ljust(w), value=value)

# --- Cinematic Result Card (Evidence & Forensic Edition) --------------------
def render_cinematic_gem(gem: Dict[str, Any], index: int = 1, total: int = 1) -> None:
    """Renders a high-art forensic specimen report card for a discovered gem."""
    t = get_theme()
    w = get_layout_width()
    overall = gem.get("overall_score", 85)
    health = gem.get("health_score", 80)
    discovery = gem.get("discovery_score", 85)

    tier_label, tier_start, tier_end = tk.tier_visual(overall, t)
    tier_badge = tk.gradient_badge(f" {tier_label} ", tier_start, tier_end)
    score_badge = Text.from_markup(f"[bold {t['cream']} on {t['surface']}] {overall}/100 [/]")

    meta_line = (
        f"⭐ {gem.get('stars', 0)} stars  •  "
        f"🍴 {gem.get('forks', 0)} forks  •  "
        f"Pushed {gem.get('pushed_days', 0)}d ago  •  "
        f"{gem.get('age_text', '2+ mos old')}  •  "
        f"{gem.get('license') or 'No license'}"
    )

    card_table = Table(box=None, expand=True, show_header=False, padding=(0, 1))
    card_table.add_column()

    header_row = Text()
    header_row.append(f"[{index}/{total}] ", style=t["muted"])
    header_row.append(f"{gem['full_name']}\n", style=f"bold {t['accent']}")
    header_row.append(f"{meta_line}\n", style=t["cream"])
    card_table.add_row(header_row)

    # Visual Meters for Health and Discovery (glossy gradient fills)
    health_meter = tk.gradient_meter(
        health, 100, width=12,
        start=t["success"], end=tk.lerp_color(t["success"], t["cream"], 0.35),
        empty=t["surface"],
    )
    discovery_meter = tk.gradient_meter(
        discovery, 100, width=12,
        start=t["grad_a"], end=t["grad_b"],
        empty=t["surface"],
    )

    score_block = Text()
    score_block.append("TIER CLASSIFICATION  ", style=f"bold {t['muted']}")
    score_block.append_text(tier_badge)
    score_block.append(" ")
    score_block.append_text(score_badge)
    score_block.append("\nREPOSITORY HEALTH    ", style=f"bold {t['muted']}")
    score_block.append_text(Text.from_markup(
        f"{health_meter}  [{t['muted']}](Tests, CI, Architecture, License)[/]"
    ))
    score_block.append("\nDISCOVERY POTENTIAL  ", style=f"bold {t['muted']}")
    score_block.append_text(Text.from_markup(
        f"{discovery_meter}  [{t['muted']}](Underground Alpha, Low Stars, Handcrafted)[/]"
    ))
    card_table.add_row(score_block)

    # Proportional Language Stack
    if gem.get("languages"):
        lang_bar = render_language_bar(gem["languages"], width=22)
        card_table.add_row(Text.from_markup(f"LANGUAGE STACK       {lang_bar}"))

    card_table.add_row(Text.from_markup(f"[{t['border']}]{tk.gradient_rule(w - 8, t['border'], t['muted'])}[/]"))

    # Plainly section
    desc_text = Text()
    desc_text.append("PLAINLY\n", style=f"bold {t['muted']}")
    desc_text.append(f"\"{gem.get('description') or 'No description provided. The code speaks for itself.'}\"", style=t["cream"])
    card_table.add_row(desc_text)

    # Positive Evidence Signals
    pos_evidence = gem.get("positive_evidence", [])
    if pos_evidence:
        why_text = Text()
        why_text.append("\n✓ VERIFIED SIGNALS (WHY IT'S GOLD)\n", style=f"bold {t['accent']}")
        for ev in pos_evidence[:4]:
            why_text.append(f"  • {ev}\n", style=t["cream"])
        card_table.add_row(why_text)

    # Negative Risks / Caution
    neg_risks = gem.get("negative_risks", [])
    if neg_risks:
        risk_text = Text()
        risk_text.append("\n! FORENSIC CAUTION & GAPS\n", style=f"bold {tk.role(t, 'warn')}")
        for r in neg_risks[:3]:
            risk_text.append(f"  • {r}\n", style=t["cream"])
        card_table.add_row(risk_text)

    # Freshness reason if present
    if gem.get("fresh_signal"):
        fresh_text = Text()
        fresh_text.append(f"\n⚡ FRESH COMMIT SIGNAL: {gem['fresh_signal']} — {gem.get('fresh_detail', '')}\n", style=f"bold {t['gold']}")
        card_table.add_row(fresh_text)

    # Pollinations AI Forensic Verdict (theme-reactive AI panel)
    ai_v = gem.get("ai_verdict")
    if ai_v:
        info_c = tk.role(t, "info")
        ai_table = Table(box=box.ROUNDED, border_style=info_c, expand=True, show_header=False, padding=(0, 1))
        ai_table.add_column("label", width=22, no_wrap=True)
        ai_table.add_column("content")

        if ai_v.get("verdict"):
            ai_table.add_row(Text.from_markup(f"[bold black on {info_c}] VERDICT [/]"), Text(ai_v["verdict"], style=t["cream"]))
        if ai_v.get("why_good"):
            ai_table.add_row(Text.from_markup(f"[bold black on {t['success']}] WHY THIS IS GOLD [/]"), Text(ai_v["why_good"], style=t["cream"]))
        if ai_v.get("underground_edge"):
            ai_table.add_row(Text.from_markup(f"[bold black on {t['accent']}] UNDERGROUND EDGE [/]"), Text(ai_v["underground_edge"], style=t["cream"]))
        if ai_v.get("caveats"):
            ai_table.add_row(Text.from_markup(f"[bold black on {tk.role(t, 'warn')}] CAVEATS & RISKS [/]"), Text(ai_v["caveats"], style=t["cream"]))
        card_table.add_row(Panel(
            ai_table,
            title=Text.from_markup(f"[bold {info_c}] 🤖 AI FORENSIC VERDICT (POLLINATIONS.AI) [/]"),
            box=box.ROUNDED,
            border_style=info_c,
            padding=(0, 0),
        ))

    # Status Pills
    pills = []
    if gem.get("ci_verified_passing"):
        pills.append(f"[bold {t['success']}]✓ CI PASSING (Verified)[/]")
    elif gem.get("has_ci"):
        pills.append(f"[{t['accent']}]✓ CI Configured[/]")
    if gem.get("has_tests"):
        pills.append(f"[{t['cream']}]✓ Test Suite[/]")
    if gem.get("license"):
        pills.append(f"[{t['cream']}]{gem['license']}[/]")
    if gem.get("primary_language"):
        pills.append(f"[{t['accent']}]{gem['primary_language']}[/]")

    card_table.add_row(Text.from_markup(f"\nSIGNALS     {' • '.join(pills)}"))
    card_table.add_row(Text(f"COORDINATES {gem.get('html_url', '')}", style=f"dim {t['muted']}"))

    # Action keymap bar
    keymap_line = Text.from_markup(
        f"\n[{t['muted']}]ACTIONS:[/] "
        f"[{t['accent']}]\\[o][/] [{t['cream']}]Open[/]  "
        f"[{t['accent']}]\\[c][/] [{t['cream']}]Clone[/]  "
        f"[{t['accent']}]\\[s][/] [{t['cream']}]Save[/]  "
        f"[{t['accent']}]\\[a][/] [{t['cream']}]AI[/]  "
        f"[{t['accent']}]\\[r][/] [{t['cream']}]Readme[/]  "
        f"[{t['accent']}]\\[t][/] [{t['cream']}]Tree[/]  "
        f"[{t['accent']}]\\[d][/] [{t['cream']}]Commits[/]  "
        f"[{t['accent']}]\\[x][/] [{t['cream']}]X-Ray[/]  "
        f"[{t['accent']}]\\[f][/] [{t['cream']}]Forks[/]  "
        f"[{t['accent']}]\\[n][/] [{t['cream']}]Next[/]  "
        f"[{t['accent']}]\\[p][/] [{t['cream']}]Prev[/]  "
        f"[{t['accent']}]\\[q][/] [{t['cream']}]Menu[/]"
    )
    card_table.add_row(keymap_line)

    gem_card = Panel(
        card_table,
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print(Align.center(gem_card))
    console.print()

# --- Radar Flight Board (ranked sweep results) ------------------------------
def render_flight_board(gems: List[Dict[str, Any]], title: str = "📡 SWEEP RESULTS") -> None:
    """Renders a cinematic ranked board of every discovered specimen before specimen view.

    Rows are hand-aligned Text lines (cell-precision) so the board never collapses."""
    from rich.cells import cell_len
    t = get_theme()
    w = get_layout_width()
    info_c = tk.role(t, "info")

    wide = w >= 100
    mid = w >= 78

    nw = max(18, min(46, w - 58)) if mid else max(16, w - 26)
    if not mid:
        nw = max(16, w - 30)

    def pad(s: str, width: int, right: bool = False) -> str:
        gap = width - cell_len(s)
        if gap < 0:
            return s
        return f"{' ' * gap}{s}" if right else f"{s}{' ' * gap}"

    header = Text()
    header.append("  #  ", style=f"bold {t['muted']}")
    header.append(pad("SPECIMEN", nw), style=f"bold {t['muted']}")
    header.append(pad("TIER", 15), style=f"bold {t['muted']}")
    if mid:
        header.append(pad("HEALTH", 10), style=f"bold {t['muted']}")
    header.append(pad("⭐", 5, right=True) + "  ", style=f"bold {t['muted']}")
    if mid:
        header.append(pad("LANG", 8) + " ", style=f"bold {t['muted']}")
    if wide:
        header.append(pad("ACTIVE", 6, right=True), style=f"bold {t['muted']}")

    body: List[Text] = []
    for i, gem in enumerate(gems):
        overall = gem.get("overall_score", 0)
        tier_label, t_start, t_end = tk.tier_visual(overall, t)
        short_tier = tier_label.split(" ", 1)[-1].split(" ")[0]
        badge = tk.gradient_badge(f" {tk.tier_icon(overall)} {short_tier} ", t_start, t_end, padding=0)
        badge_plain_pad = pad("", max(0, 15 - cell_len(badge.plain)))

        name = str(gem.get("full_name", "?"))
        if cell_len(name) > nw:
            name = name[: max(1, nw - 1)] + "…"

        line = Text()
        line.append(f"  {i + 1:02d}  ", style=f"bold {t['muted']}")
        line.append(pad(name, nw), style=f"bold {t['accent']}")
        line.append_text(badge)
        line.append(badge_plain_pad)
        if mid:
            line.append_text(Text.from_markup(tk.gradient_meter(
                gem.get("health_score", 0), 100, width=8,
                start=t["success"], end=tk.lerp_color(t["success"], t["cream"], 0.35),
                empty=t["surface"], show_score=False,
            ) + "  "))
        line.append(pad(f"⭐ {gem.get('stars', 0)}", 6, right=True) + "  ", style=t["gold"])
        if mid:
            line.append(pad((gem.get("primary_language") or "—")[:8], 8) + " ", style=t["cream"])
        if wide:
            line.append(pad(f"{gem.get('pushed_days', 0)}d", 6, right=True), style=t["muted"])
        body.append(line)

    content: List[Any] = [header]
    content.append(Text.from_markup(f"[{t['border']}]{('─' * (w - 6))}[/]"))
    content.extend(body)

    legend = Text()
    legend.append("  ↵ ", style=f"bold {t['accent']}")
    legend.append("Select a specimen", style=t["muted"])
    legend.append("   ┊   ", style=t["border"])
    legend.append("ranked by explainable sleeper score", style=f"dim {t['muted']}")

    panel = Panel(
        Group(*content, legend),
        title=gradient_panel_title(title, t),
        subtitle=Text.from_markup(f"[dim {info_c}]✦ underground alpha detected[/]"),
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 0),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()

def gradient_panel_title(title: str, theme: Dict[str, str]) -> Text:
    """Gradient-swept panel title using the theme's signature colors."""
    return tk.gradient_text(
        f" {title} ",
        theme.get("grad_a", theme["accent"]),
        theme.get("grad_b", theme["gold"]),
        bold=True,
    )

# --- True ANSI File Tree -----------------------------------------------------
FILE_COLORS: Dict[str, str] = {
    ".py": "#3572A5", ".rs": "#DEA584", ".go": "#00ADD8", ".ts": "#3178C6",
    ".tsx": "#3178C6", ".js": "#F1E05A", ".c": "#A8B9CC", ".h": "#A8B9CC",
    ".cpp": "#F34B7D", ".hpp": "#F34B7D", ".zig": "#DEA584", ".lua": "#000080",
    ".md": "#C9A227", ".toml": "#9C6BB3", ".yml": "#9C6BB3", ".yaml": "#9C6BB3",
    ".json": "#C9A227", ".sh": "#89E051", ".html": "#E34C26", ".css": "#563D7C",
    ".nix": "#7DD3FC", ".swift": "#F05138", ".kt": "#A97BFF", ".ex": "#6E4A7E",
    ".lock": "#676E79", ".txt": "#8B949E",
}

def tree_to_lines(items: List[Dict[str, Any]], max_lines: int = 60) -> List[Dict[str, Any]]:
    """Converts a flat recursive file list into a hierarchical display list.

    Returns dicts: {name, is_dir, size, depth, connector} — pure & unit-testable.
    Dirs sort first (alphabetical), then files (alphabetical)."""
    root: Dict[str, Any] = {"__dirs__": {}, "__files__": [], "__size__": 0}
    for item in items[:800]:
        parts = [p for p in str(item.get("path", "")).split("/") if p]
        node = root
        for depth, part in enumerate(parts):
            is_last = depth == len(parts) - 1
            is_dir = (not is_last) or item.get("type") == "tree"
            if is_dir and not is_last:
                node = node["__dirs__"].setdefault(part, {"__dirs__": {}, "__files__": [], "__size__": 0})
            elif is_dir:
                node["__dirs__"].setdefault(part, {"__dirs__": {}, "__files__": [], "__size__": 0})
            else:
                node["__files__"].append({"name": part, "size": int(item.get("size", 0) or 0)})

    lines: List[Dict[str, Any]] = []

    def walk(node: Dict[str, Any], prefix: str, depth: int) -> bool:
        if len(lines) >= max_lines:
            return False
        dir_names = sorted(node["__dirs__"].keys())
        file_names = sorted(node["__files__"], key=lambda f: f["name"])
        entries = [("dir", d, None) for d in dir_names] + [("file", f["name"], f["size"]) for f in file_names]
        for i, (kind, name, size) in enumerate(entries):
            if len(lines) >= max_lines:
                del lines[max(0, max_lines - 1):]
                lines.append({"name": "…", "is_dir": False, "size": 0, "depth": depth, "connector": "truncated"})
                return True
            last = i == len(entries) - 1
            if kind == "dir":
                child = node["__dirs__"][name]
                total = tree_count(child)
                lines.append({
                    "name": name,
                    "is_dir": True,
                    "size": 0,
                    "depth": depth,
                    "connector": "└─" if last else "├─",
                    "count": total,
                })
                if not walk(child, prefix + ("    " if last else "│   "), depth + 1):
                    return False
            else:
                lines.append({
                    "name": name,
                    "is_dir": False,
                    "size": size or 0,
                    "depth": depth,
                    "connector": "╰─" if last else "├─",
                })
        return True

    walk(root, "", 0)
    return lines

def tree_count(node: Dict[str, Any]) -> int:
    return 1 + sum(tree_count(c) for c in node["__dirs__"].values())

def render_tree_viewer(repo_name: str, items: List[Dict[str, Any]]) -> None:
    """Renders a true ANSI branch-tree of the repository architecture."""
    t = get_theme()
    w = get_layout_width()
    lines = tree_to_lines(items)
    max_depth = max((l.get("depth", 0) for l in lines), default=0) or 1
    # Compact widths depending on depth
    name_w = max(28, min(52, w - (46 if max_depth > 1 else 30)))

    table = Table(box=None, expand=True, width=w - 6, show_header=False, padding=(0, 0))
    table.add_column("Tree", no_wrap=True, ratio=3)
    table.add_column("Size", justify="right", width=9, style=f"dim {tk.role(t, 'info')}")

    shown_dirs = 0
    for line in lines:
        indent = "│  " * line["depth"]
        branch = line.get("connector", "")
        if line["connector"] == "truncated":
            table.add_row(
                Text.from_markup(f"{indent}[dim {t['muted']}]  ⋯ ⋯ ⋯[/]"), ""
            )
            continue
        if line["is_dir"]:
            shown_dirs += 1
            count = line.get("count", 0)
            table.add_row(
                Text.from_markup(
                    f"  {indent}[bold {t['accent']}]{branch}[/] [bold {t['accent']}]▸ {line['name']}/[/] [dim {t['muted']}]({count})[/]"
                ),
                "",
            )
        else:
            ext = "." + line["name"].rsplit(".", 1)[-1] if "." in line["name"] else ""
            color = FILE_COLORS.get(ext.lower(), t["cream"])
            table.add_row(
                Text.from_markup(
                    f"  {indent}[{t['muted']}]{branch}[/] [{color}]◆ {line['name']}[/]"
                ),
                tk.fmt_size(line["size"]),
            )

    stats = f"{shown_dirs} directories • {len(lines)} artifacts • recursive scan"
    panel = Panel(
        table,
        title=gradient_panel_title(f"🌳 {repo_name}", t),
        subtitle=Text.from_markup(f"[dim {t['muted']}]{stats}[/]"),
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()

# --- Commit Cadence (52-week craftsmanship rhythm) ---------------------------
def render_cadence_summary(cadence: Optional[Dict[str, Any]], theme: Dict[str, str]) -> Optional[Any]:
    """Builds the commit-rhythm header block for the commits viewer."""
    if not cadence or not cadence.get("weeks"):
        return None
    t = theme
    spark = tk.gradient_sparkline(
        cadence["weeks"],
        start=t["success"],
        end=tk.lerp_color(t["accent"], t["gold"], 0.5),
    )
    momentum = cadence.get("momentum", "▪ steady")
    m_color = t["success"]
    if "accelerating" in momentum or "surging" in momentum:
        m_color = t["gold"]
    elif "cooling" in momentum:
        m_color = tk.role(t, "warn")

    block = Text()
    block.append("COMMIT RHYTHM  ", style=f"bold {t['muted']}")
    block.append_text(Text.from_markup(f"{spark}  [bold {m_color}]{momentum}[/]"))
    block.append("\n")
    block.append_text(Text.from_markup(
        f"[{t['muted']}]52-week totals:[/] [bold {t['cream']}]{cadence.get('total', 0)} commits[/]"
        f"  [{t['muted']}]•[/] [{t['muted']}]best week:[/] [bold {t['cream']}]{cadence.get('best_week', 0)}[/]"
        f"  [{t['muted']}]•[/] [{t['muted']}]last 4 wk avg:[/] [bold {t['cream']}]{cadence.get('avg4', 0):.1f}[/]"
    ))
    return block

def render_commits_viewer(repo_name: str, commits: List[Dict[str, Any]], cadence: Optional[Dict[str, Any]] = None) -> None:
    """Renders recent commit history showing craftsmanship and commit cadence."""
    t = get_theme()
    w = get_layout_width()

    content_rows: List[Any] = []
    cadence_block = render_cadence_summary(cadence, t)
    if cadence_block is not None:
        content_rows.append(cadence_block)
        content_rows.append(Text.from_markup(f"[{t['border']}]{tk.gradient_rule(w - 8, t['border'], t['muted'])}[/]"))

    table = Table(box=None, expand=True, width=w - 8, show_header=False, padding=(0, 0))
    table.add_column("SHA", width=8, style=f"bold {t['accent']}")
    table.add_column("Message", style=t["cream"], ratio=1)
    table.add_column("Author", style=t["gold"], width=14)

    for c in commits:
        sem = c.get("message", "")
        sem_icon = "◆" if ":" in sem and sem.split(":")[0] in ("feat", "fix", "perf", "refactor", "docs", "test", "chore", "style", "build", "ci") else "•"
        table.add_row(
            f"{c.get('sha', '')}",
            Text.from_markup(f"[{t['gold']}]{sem_icon}[/] {sem[:60]}"),
            c.get("author", "")[:14],
        )
    content_rows.append(table)

    panel = Panel(
        Group(*content_rows),
        title=gradient_panel_title(f"📜 CRAFTSMANSHIP LOG: {repo_name}", t),
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()

# --- Theme Gallery (live side-by-side preview) ---------------------------------
def render_theme_gallery(active: str) -> None:
    """Renders all four themes as live mini-previews in a 2×2 gallery grid."""
    w = get_layout_width()
    cell_w = (w - 2) // 2

    panels = []
    for key, theme in THEMES.items():
        inner = Group(
            Text.from_markup(
                f"[{theme['muted']}]RADAR [/][bold {theme['accent']}]ACTIVE (2..7 ⭐)[/]\n"
                f"{render_meter(82, 100, width=8, fill_color=theme['accent'])}\n"
                f"[bold black on {theme['accent']}] UNDERGROUND [/] [bold {theme['cream']} on {theme['border']}] ZERO HYPE [/]\n"
                f"[bold {theme['gold']}]💎 MYTHIC 94/100[/] [dim {theme['muted']}]• gradient earn[/]"
            ),
        )
        is_active = key == active
        header = Text.from_markup(
            f"[bold {theme['accent']}]{theme['name']}[/] {'[bold gold3]● ACTIVE[/] ' if is_active else ''}"
        )
        panels.append(Panel(
            inner,
            title=header,
            box=box.DOUBLE if is_active else box.ROUNDED,
            border_style=theme["border"] if is_active else theme["muted"],
            width=cell_w,
            padding=(0, 1),
        ))

    grid = Table(box=None, show_header=False, padding=(1, 1), expand=False)
    grid.add_column("a")
    grid.add_column("b")
    grid.add_row(panels[0], panels[1])
    grid.add_row(panels[2], panels[3])

    console.print(Align.center(Group(
        Text.from_markup(f"[bold {get_theme()['accent']}]👀 THEMED PREVIEW GALLERY — pick with your eyes first[/]"),
        Text(""),
        grid,
        Text.from_markup(f"[dim {get_theme()['muted']}]  ↑/↓ navigate • enter to wear the skin[/]"),
    )))
    console.print()

# --- Empty State ---------------------------------------------------------------
def render_empty_state(title: str, message: str, hint: str = "") -> None:
    """A tidy cinematic 'radar silence' panel instead of a bare error line."""
    t = get_theme()
    w = min(72, get_layout_width())
    body = Group(
        Align.center(tk.gradient_text("✧ ⋆ ✧  RADAR SILENCE  ✧ ⋆ ✧", t["accent"], t["gold"], bold=True)),
        Text(""),
        Align.center(Text(message, style=t["cream"])),
    )
    if hint:
        body = Group(body, Text(""), Align.center(Text.from_markup(f"[dim italic {t['muted']}]💡 {hint}[/]")))
    console.print(Align.center(Panel(body, border_style=t["border"], box=box.ROUNDED, width=w, padding=(1, 2))))
    console.print()

def render_xray_report(gem: Dict[str, Any]) -> None:
    """Renders a comprehensive, evidence-backed X-Ray forensic examination report."""
    t = get_theme()
    w = get_layout_width()

    table = Table(
        box=box.ROUNDED,
        border_style=t["border"],
        expand=False,
        width=w,
        show_header=True,
        header_style=f"bold {t['accent']}",
    )
    table.add_column("Diagnostic Metric", style=f"bold {t['cream']}", ratio=1)
    table.add_column("Verified Finding / Telemetry", style=t["cream"], ratio=2)

    table.add_row("Specimen Repository", f"[{t['accent']} bold]{gem['full_name']}[/]")
    table.add_row("Popularity Coordinate", f"⭐ {gem['stars']} stars • 🍴 {gem.get('forks', 0)} forks")
    table.add_row("Project Chronology", f"Created {gem.get('age_text', 'unknown')} • Pushed {gem.get('pushed_days', 0)}d ago")
    
    # Dual scores
    health = gem.get("health_score", 75)
    discovery = gem.get("discovery_score", 85)
    h_meter = tk.gradient_meter(health, 100, width=10, start=t["success"], end=tk.lerp_color(t["success"], t["cream"], 0.35), empty=t["surface"])
    d_meter = tk.gradient_meter(discovery, 100, width=10, start=t["grad_a"], end=t["grad_b"], empty=t["surface"])
    table.add_row("Repository Health", h_meter)
    table.add_row("Discovery Potential", d_meter)

    # Test Suite
    if gem.get("has_tests"):
        test_val = f"[bold {t['success']}]VERIFIED PRESENT[/] [dim]({gem.get('test_file_count', 0)} test files detected)[/]"
    else:
        test_val = f"[{tk.role(t, 'warn')}]NOT DETECTED (Verified absent in root/tests)[/]"
    table.add_row("Automated Test Suite", test_val)

    # CI/CD Workflows
    if gem.get("ci_verified_passing"):
        ci_val = f"[bold {t['success']}]VERIFIED PASSING[/] [dim](Recent GitHub Actions run succeeded)[/]"
    elif gem.get("has_ci"):
        ci_val = f"[{t['accent']}]CONFIGURED[/] [dim](Workflows found; {gem.get('ci_conclusion', 'no recent run logs')})[/]"
    else:
        ci_val = "[dim]NOT DETECTED[/dim]"
    table.add_row("CI/CD Automation", ci_val)

    # Language breakdown
    if gem.get("languages"):
        lang_bar = render_language_bar(gem["languages"], width=18)
        table.add_row("Language Breakdown", lang_bar)
    else:
        table.add_row("Primary Language", gem.get("primary_language", "Code"))

    # LoC estimate with clarity
    table.add_row(
        "Estimated LoC",
        f"~{gem.get('loc_estimate', 0):,} lines [dim](derived from language byte density; not fabricated)[/dim]"
    )
    table.add_row("License Clarity", gem.get("license") or f"[{tk.role(t, 'warn')}]No declared license found[/]")

    # Recent Commits
    recent_commits = gem.get("recent_commits", [])
    if recent_commits:
        commit_lines = [f"[dim]• {c['message'][:50]}[/dim]" for c in recent_commits[:3]]
        table.add_row("Recent Commits", "\n".join(commit_lines))

    console.print()
    console.print(Align.center(table))
    console.print()

    # Evidence details
    if gem.get("positive_evidence"):
        console.print(f"[bold {t['success']}]✓ Verified Forensic Evidence:[/]")
        for ev in gem["positive_evidence"]:
            console.print(f"  [bold {t['success']}]•[/] [{t['cream']}]{ev}[/]")
        console.print()

    if gem.get("negative_risks"):
        console.print(f"[bold {tk.role(t, 'warn')}]! Forensic Risks & Limitations:[/]")
        for r in gem["negative_risks"]:
            console.print(f"  [bold {tk.role(t, 'warn')}]•[/] [{t['cream']}]{r}[/]")
        console.print()

    if gem.get("ai_verdict"):
        ai_v = gem["ai_verdict"]
        info_c = tk.role(t, "info")
        console.print(f"[bold {info_c}]🤖 AI Codebase Forensic Verdict (Pollinations.ai):[/]")
        if ai_v.get("verdict"):
            console.print(f"  [bold {t['gold']}]• Verdict:[/] [{t['cream']}]{ai_v['verdict']}[/]")
        if ai_v.get("why_good"):
            console.print(f"  [bold {t['success']}]• Why This Is Good:[/] [{t['cream']}]{ai_v['why_good']}[/]")
        if ai_v.get("underground_edge"):
            console.print(f"  [bold {t['accent']}]• Underground Edge:[/] [{t['cream']}]{ai_v['underground_edge']}[/]")
        if ai_v.get("caveats"):
            console.print(f"  [bold {tk.role(t, 'warn')}]• Caveats & Risks:[/] [{t['cream']}]{ai_v['caveats']}[/]")
        console.print()

def styled_panel(content: Any, title: Optional[str] = None, **kwargs) -> Panel:
    t = get_theme()
    w = kwargs.pop("width", get_layout_width())
    return Panel(
        content,
        title=f"[{t['accent']} bold] {title} [/]" if title else None,
        border_style=kwargs.pop("border_style", t["border"]),
        box=kwargs.pop("box", box.ROUNDED),
        padding=kwargs.pop("padding", (0, 1)),
        width=w,
        **kwargs,
    )

def styled_error(message: str, hint: Optional[str] = None) -> None:
    t = get_theme()
    w = get_layout_width()
    err_lines = [Text(str(message), style="bold red")]
    if hint:
        err_lines.append(Text(f"\n💡 Hint: {hint}", style=t["cream"]))
    console.print(Align.center(Panel(Group(*err_lines), title="[bold red] Well, this is awkward [/]", border_style="red", box=box.ROUNDED, width=w, padding=(0, 1))))

def styled_success(message: str) -> None:
    t = get_theme()
    console.print(f"[bold {t['accent']}]{icon('check')} {message}[/]")

def render_ai_teardown(ai_text: str, repo_name: str) -> None:
    """Renders a Charm-style AI forensic teardown powered by Pollinations AI."""
    t = get_theme()
    w = get_layout_width()
    info_c = tk.role(t, "info")
    warn_c = tk.role(t, "warn")

    sections = [
        ("✦ DETAILED VERDICT:", f"[bold black on {info_c}] VERDICT [/]"),
        ("✦ WHY THIS IS GOOD:", f"[bold black on {t['success']}] WHY THIS IS GOLD [/]"),
        ("✦ UNDERGROUND EDGE:", f"[bold black on {t['accent']}] UNDERGROUND EDGE [/]"),
        ("✦ CAVEATS & TRADEOFFS:", f"[bold black on {warn_c}] CAVEATS & RISKS [/]"),
    ]

    has_structured_sections = any(sec[0] in ai_text for sec in sections)

    if has_structured_sections:
        table = Table(box=box.ROUNDED, border_style=info_c, expand=True, show_header=False, padding=(0, 1))
        table.add_column("badge", width=22, no_wrap=True)
        table.add_column("content")

        remaining = ai_text
        for i, (marker, badge) in enumerate(sections):
            if marker in remaining:
                parts = remaining.split(marker, 1)
                after = parts[1]
                next_pos = len(after)
                for next_marker, _ in sections[i+1:]:
                    pos = after.find(next_marker)
                    if pos != -1 and pos < next_pos:
                        next_pos = pos
                chunk = after[:next_pos].strip()
                table.add_row(Text.from_markup(badge), Text(chunk, style=t["cream"]))
                remaining = after[next_pos:]

        content_group = Group(
            Text(f"Specimen: {repo_name} • Architectural Forensics\n", style=f"dim {t['muted']}"),
            table,
        )
    else:
        panel_content = Text()
        panel_content.append(f"✦ POLLINATIONS AI FORENSIC SYNTHESIS ✦\n", style=f"bold {t['gold']}")
        panel_content.append(f"Specimen: {repo_name}\n\n", style=f"dim {t['muted']}")
        panel_content.append(ai_text, style=t["cream"])
        content_group = panel_content

    p = Panel(
        content_group,
        title=f"[bold {info_c}] 🤖 AI CODEBASE SYNTHESIS [/]",
        subtitle="[dim]Powered by Pollinations.ai • Zero Hype[/dim]",
        box=box.ROUNDED,
        border_style=info_c,
        padding=(1, 2),
        width=w,
    )
    console.print()
    console.print(Align.center(p))
    console.print()

def render_markdown_viewer(title: str, content: str) -> None:
    """Renders formatted README documentation with Rich syntax highlighting inside a panel."""
    t = get_theme()
    w = get_layout_width()
    try:
        renderable = Markdown(content)
    except Exception:
        renderable = Text(content, style=t["cream"])
    panel = Panel(
        renderable,
        title=f"[bold {t['accent']}] 📖 {title.upper()} [/]",
        subtitle=f"[{t['muted']} dim]gitSOLVE In-Terminal Documentation Reader[/]",
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(1, 2),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()

def _legacy_render_tree_viewer(repo_name: str, items: List[Dict[str, Any]]) -> None:
    """Old flat table fallback (kept for tests/debug)."""
    t = get_theme()
    w = get_layout_width()

    table = Table(box=box.ROUNDED, border_style=t["border"], expand=True, width=w)
    table.add_column("Type", width=6, justify="center")
    table.add_column("Path", style=f"bold {t['cream']}")
    table.add_column("Size", justify="right", style=f"dim {t['muted']}")

    for item in items[:35]:
        p = item.get("path", "")
        is_dir = item.get("type") == "tree"
        icon_str = f"[bold {tk.role(t, 'info')}]📁[/]" if is_dir else f"[{t['success']}]📄[/]"
        size_str = "-" if is_dir else f"{item.get('size', 0):,} B"
        table.add_row(icon_str, p, size_str)

    panel = Panel(
        table,
        title=f"[bold {t['accent']}] 🌳 ARCHITECTURE TREE: {repo_name} [/]",
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()

def render_rate_limit_table(rate_info: Dict[str, Any]) -> None:
    """Renders GitHub API rate limit telemetry and quota health."""
    t = get_theme()
    w = get_layout_width()

    resources = rate_info.get("resources", {})
    core = resources.get("core", {})
    search = resources.get("search", {})

    table = Table(box=box.ROUNDED, border_style=t["border"], expand=True, width=w)
    table.add_column("Resource Stream", style=f"bold {t['cream']}")
    table.add_column("Remaining / Limit", justify="center")
    table.add_column("Quota Meter", justify="center")
    table.add_column("Reset In", justify="right", style=f"dim {t['muted']}")

    now_ts = int(time.time())
    for name, res in [("Core API (Metadata & Trees)", core), ("Search API (Radar & Discovery)", search)]:
        rem = res.get("remaining", 0)
        lim = res.get("limit", 60)
        reset_ts = res.get("reset", now_ts)
        delta_m = max(0, (reset_ts - now_ts) // 60)
        meter = tk.gradient_meter(rem, max_val=max(1, lim), width=10, start=t["accent"], end=t["grad_b"], empty=t["surface"], show_score=False)
        table.add_row(name, f"{rem}/{lim}", meter, f"{delta_m} mins")

    panel = Panel(
        table,
        title=gradient_panel_title("📊 GITHUB API RATE LIMIT TELEMETRY", t),
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print()
    console.print(Align.center(panel))
    console.print()


