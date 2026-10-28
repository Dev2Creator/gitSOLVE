# gitSOLVE ✦ IRL™ Design System UI
# Software for Humans. Less terminal drama.

import os
import sys
from typing import Dict, Any, Optional, Tuple, List
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import questionary

from gitsolve.config import load_config

console = Console(highlight=False)

# --- Themes -----------------------------------------------------------------
THEMES: Dict[str, Dict[str, str]] = {
    "warm_earth": {
        "name": "Warm Earth (IRL Classic)",
        "accent": "#F29265",
        "cream": "#D7C0AA",
        "muted": "#614B39",
        "border": "#6B4E36",
        "selected": "#3478F6",
        "gold": "#F6C177",
        "mythic": "#EB6F92",
    },
    "cyber_peach": {
        "name": "Cyber Peach",
        "accent": "#FF7B54",
        "cream": "#FFD59E",
        "muted": "#5B2A36",
        "border": "#A44569",
        "selected": "#EC4899",
        "gold": "#FFD93D",
        "mythic": "#FF6B6B",
    },
    "emerald_moss": {
        "name": "Emerald Moss",
        "accent": "#4ADE80",
        "cream": "#E2FCD6",
        "muted": "#1E3D29",
        "border": "#2D6A4F",
        "selected": "#10B981",
        "gold": "#FBBF24",
        "mythic": "#34D399",
    },
    "lavender_night": {
        "name": "Lavender Night",
        "accent": "#C084FC",
        "cream": "#E9D5FF",
        "muted": "#3B1B54",
        "border": "#6B21A8",
        "selected": "#8B5CF6",
        "gold": "#FDE047",
        "mythic": "#F472B6",
    },
}

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

# --- Icons & Glyphs ---------------------------------------------------------
ICONS: Dict[str, Tuple[str, str]] = {
    "radar": ("\uf012", "[RADAR]"),
    "gem": ("\uf3a5", "[GEM]"),
    "star": ("\uf005", "*"),
    "sparkles": ("\uf890", "✦"),
    "search": ("\uf002", "[?]"),
    "check": ("\uf00c", "OK"),
    "cross": ("\uf00d", "X"),
    "fire": ("\uf06d", "^"),
    "rocket": ("\uf135", "=>"),
    "vault": ("\uf023", "[V]"),
    "trophy": ("\uf091", "#1"),
    "git": ("\uf1d3", "git"),
    "branch": ("\uf126", "--"),
    "code": ("\uf121", "</>"),
    "clock": ("\uf017", "~"),
    "user": ("\uf007", "@"),
    "heart": ("\uf004", "<3"),
    "package": ("\uf187", "[+]"),
    "warning": ("\uf071", "/!\\"),
}

_NERD_HINT_ENV = (
    "KITTY_WINDOW_ID",
    "WEZTERM_EXECUTABLE",
    "ITERM_PROFILE",
    "WT_SESSION",
    "TERMINAL_EMULATOR",
    "ALACRITTY_LOG",
)

def use_nerd_icons() -> bool:
    cfg = load_config()
    mode = cfg.get("icons_mode", "auto")
    if mode == "nerd":
        return True
    if mode == "ascii":
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("CI"):
        return False
    if "256color" in os.environ.get("TERM", "") or os.environ.get("COLORTERM"):
        return any(var in os.environ for var in _NERD_HINT_ENV)
    return False

def icon(name: str) -> str:
    nerd, ascii_ = ICONS.get(name, ("", "?"))
    return nerd if (nerd and use_nerd_icons()) else ascii_

# --- Wordmark & Banner ------------------------------------------------------
_GITSOLVE_WORDMARK = [
    ("██████╗ ██╗████████╗███████╗ ██████╗ ██╗    ██╗   ██╗███████╗", "#F29265"),
    ("██╔════╝ ██║╚══██╔══╝██╔════╝██╔═══██╗██║    ██║   ██║██╔════╝", "#F49B6A"),
    ("██║  ███╗██║   ██║   ███████╗██║   ██║██║    ██║   ██║█████╗  ", "#F6A46F"),
    ("██║   ██║██║   ██║   ╚════██║██║   ██║██║    ╚██╗ ██╔╝██╔══╝  ", "#F8AD74"),
    ("╚██████╔╝██║   ██║   ███████║╚██████╔╝███████╗╚████╔╝ ███████╗", "#FBB679"),
    (" ╚═════╝ ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚══════╝ ╚═══╝  ╚══════╝", "#D7C0AA"),
]

def print_banner(subtitle: str = "Underground Code. Zero Hype. Handcrafted Gems.") -> None:
    t = get_theme()
    lines = [Text(line, style=f"bold {color}") for line, color in _GITSOLVE_WORDMARK]
    console.print(Group(*lines))
    console.print(Text(f"✦  {subtitle}  ✦", style=f"bold {t['cream']}"))
    console.print()

def print_header(title: str = "RADAR READY", status_text: str = "Awaiting command") -> None:
    t = get_theme()
    print_banner()
    
    header_box = Table(box=box.SQUARE, border_style=t["border"], expand=True, show_header=False)
    header_box.add_column(style=f"bold {t['accent']}")
    header_box.add_column(style=t["cream"])
    
    cfg = load_config()
    header_box.add_row("Status", f"[bold {t['accent']}]● [/][{t['cream']}]{status_text}[/]")
    header_box.add_row("Scans Run", f"[{t['cream']}]{cfg.get('scans_completed', 0)} completed[/]")
    header_box.add_row("Saved Gems", f"[{t['cream']}]{cfg.get('gems_discovered', 0)} in vault[/]")
    if cfg.get("github_token"):
        header_box.add_row("GitHub Auth", f"[{t['accent']}]Authenticated (5,000 req/hr)[/]")
    else:
        header_box.add_row("GitHub Auth", f"[{t['muted']}]Public Mode (Rate limits apply. Run /config to add token)[/]")
        
    console.print(header_box)
    console.print()

# --- Questionary Styling ----------------------------------------------------
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

def command_choice(command: str, description: str, value: str) -> questionary.Choice:
    width = max(52, console.width - 6)
    label = f"/{command:<13}{description}"
    return questionary.Choice(label.ljust(width), value=value)

# --- Panels, Cards & Output -------------------------------------------------
def styled_panel(content: Any, title: Optional[str] = None, **kwargs) -> Panel:
    t = get_theme()
    return Panel(
        content,
        title=f"[{t['accent']}] {title} [/]" if title else None,
        border_style=kwargs.pop("border_style", t["border"]),
        box=kwargs.pop("box", box.SQUARE),
        padding=kwargs.pop("padding", (0, 1)),
        **kwargs,
    )

def render_cinematic_gem(gem: Dict[str, Any], index: int = 1, total: int = 1) -> None:
    t = get_theme()
    sleeper_score = gem.get("sleeper_score", 85)
    
    # Rarity tier
    if sleeper_score >= 90:
        tier_label = f"[{t['mythic']} bold]💎 MYTHIC SLEEPER ({sleeper_score}/100)[/]"
    elif sleeper_score >= 75:
        tier_label = f"[{t['gold']} bold]🔥 SOLID GOLD ({sleeper_score}/100)[/]"
    else:
        tier_label = f"[{t['accent']} bold]✨ HIDDEN GEM ({sleeper_score}/100)[/]"

    card = Table(box=box.SQUARE, border_style=t["border"], expand=True, show_header=False)
    card.add_column()

    header_text = Text()
    header_text.append(f"[{index}/{total}]  ", style=t["muted"])
    header_text.append(f"{gem['full_name']}", style=f"bold {t['accent']}")
    header_text.append(f"   ⭐ {gem.get('stars', 0)} stars", style=f"bold {t['gold']}")
    header_text.append(f"  •  {gem.get('age_text', '2+ months old')}", style=t["cream"])
    header_text.append(f"  •  {gem.get('primary_language', 'Code')}", style=f"bold {t['cream']}")

    card.add_row(header_text)
    card.add_row(Text.from_markup(f"RATING: {tier_label}"))
    card.add_row(Text("─" * (min(76, console.width - 4)), style=t["border"]))

    # What it does
    plainly = Text()
    plainly.append("PLAINLY\n", style=f"bold {t['muted']}")
    plainly.append(gem.get("description") or "No description provided. The code speaks for itself.", style=t["cream"])
    card.add_row(plainly)

    # Why it's gold
    findings = gem.get("findings", [])
    if findings:
        why = Text()
        why.append("\nWHY IT'S GOLD\n", style=f"bold {t['accent']}")
        for f in findings:
            why.append(f"• {f}\n", style=t["cream"])
        card.add_row(why)

    # Tech stack & metadata pills
    meta_pills = []
    if gem.get("has_tests"):
        meta_pills.append(f"[{t['accent']}]✓ Tests[/]")
    if gem.get("has_ci"):
        meta_pills.append(f"[{t['accent']}]✓ CI/CD[/]")
    if gem.get("license"):
        meta_pills.append(f"[{t['cream']}]{gem['license']}[/]")
    if gem.get("loc_estimate"):
        meta_pills.append(f"[{t['cream']}]{gem['loc_estimate']} LoC[/]")

    card.add_row(Text.from_markup(f"METRICS: {' • '.join(meta_pills)}"))
    card.add_row(Text(f"URL: {gem.get('html_url', '')}", style=f"dim {t['muted']}"))

    console.print(card)
    console.print()

def styled_error(message: str, hint: Optional[str] = None) -> None:
    t = get_theme()
    err_lines = [Text(str(message), style="bold red")]
    if hint:
        err_lines.append(Text(f"\n💡 Hint: {hint}", style=t["cream"]))
    console.print(styled_panel(Group(*err_lines), title="Well, this is awkward", border_style="red"))

def styled_success(message: str) -> None:
    t = get_theme()
    console.print(f"[bold {t['accent']}]{icon('check')} {message}[/]")
