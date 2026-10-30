# gitSOLVE ✦ First-Launch Onboarding Ceremony
# Software for Humans. Underground code. Zero hype.

import getpass
from typing import Any, Dict
import questionary
from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from gitsolve.config import load_config, update_config_value
from gitsolve.ui import (
    console,
    get_theme,
    menu_style,
    MASCOTS,
    get_mascot_lines,
    get_personalized_greeting,
    THEMES,
)

def is_onboarding_needed() -> bool:
    """Returns True if the user has not completed the onboarding ceremony."""
    cfg = load_config()
    return not bool(cfg.get("onboarded", False))

def run_onboarding_ceremony() -> Dict[str, Any]:
    """Runs the interactive first-entry explorer onboarding ceremony."""
    console.clear()
    t = get_theme()
    cfg = load_config()

    default_user = cfg.get("user_name") or getpass.getuser()

    # Step 0: Welcome Ceremony Banner
    welcome_panel = Panel(
        Group(
            Text.from_markup(f"[bold {t['gold']}]✦ WELCOME TO GITSOLVE ✦[/]", justify="center"),
            Text.from_markup(f"[bold {t['accent']}]UNDERGROUND GITHUB RADAR & CODE GEM SCANNER[/]", justify="center"),
            Text(""),
            Text.from_markup(
                f"[{t['cream']}]Let's calibrate your radar frequency and personalize your terminal companion.[/]",
                justify="center",
            ),
            Text.from_markup(
                f"[{t['cream']} dim](Takes 15 seconds • You can modify any of these anytime in /config)[/]",
                justify="center",
            ),
        ),
        box=box.ROUNDED,
        border_style=t["accent"],
        padding=(1, 2),
        width=min(78, console.width - 4),
    )
    console.print(Align.center(welcome_panel))
    console.print()

    # Step 1: Explorer Name / Handle
    name = questionary.text(
        "◈ Step 1/5: What callsign / handle should gitSOLVE greet you with?",
        default=default_user,
        style=menu_style(),
    ).ask()
    if name is None:
        name = default_user
    name = name.strip() or default_user

    # Step 2: Pronouns
    pronoun_action = questionary.select(
        f"◈ Step 2/5: What are your preferred pronouns, {name}?",
        choices=[
            questionary.Choice("she / her", value="she/her"),
            questionary.Choice("he / him", value="he/him"),
            questionary.Choice("they / them", value="they/them"),
            questionary.Choice("she / they", value="she/they"),
            questionary.Choice("he / they", value="he/they"),
            questionary.Choice("any / all", value="any/all"),
            questionary.Choice("Custom / Write-in...", value="custom"),
            questionary.Choice("Skip (prefer not to say)", value=""),
        ],
        style=menu_style(),
    ).ask()

    if pronoun_action == "custom":
        custom_pronouns = questionary.text(
            "Enter your pronouns (e.g. ze/zir, fae/faer, she/he):",
            style=menu_style(),
        ).ask()
        pronouns = custom_pronouns.strip() if custom_pronouns else ""
    else:
        pronouns = pronoun_action or ""

    # Step 3: Curator Archetype
    archetype_action = questionary.select(
        "◈ Step 3/5: Choose your Curator Archetype / Field Title:",
        choices=[
            questionary.Choice("Sleeper Hunter     — Tracking 2-7 star hidden gems before the crowd", value="Sleeper Hunter"),
            questionary.Choice("Binary Alchemist   — Extracting pure architectural signal from raw code", value="Binary Alchemist"),
            questionary.Choice("Code Craftsman     — Seeking zero-dependency, pure handcrafted repos", value="Code Craftsman"),
            questionary.Choice("Underground Scout  — Excavating forgotten repositories & underground tools", value="Underground Scout"),
            questionary.Choice("Custom Archetype...", value="custom"),
        ],
        style=menu_style(),
    ).ask()

    if archetype_action == "custom":
        custom_arch = questionary.text(
            "Enter your custom Archetype title (e.g. Kernel Mystic, Terminal Ronin):",
            default="Sleeper Hunter",
            style=menu_style(),
        ).ask()
        archetype = custom_arch.strip() if custom_arch else "Sleeper Hunter"
    else:
        archetype = archetype_action or "Sleeper Hunter"

    # Step 4: Companion Mascot
    mascot_choices = [
        questionary.Choice("🌸 Hoodie Wink       — Menhera-chan winking & sparkling stars", value="hoodie"),
        questionary.Choice("💖 Zero Two Darling  — Zero Two smiling, sweet leaning gaze", value="zerotwo_lean"),
        questionary.Choice("✨ Zero Two Stargaze — Zero Two reaching out into the cosmos", value="zerotwo_reach"),
        questionary.Choice("🔮 Rikka Wicked Eye  — Chunibyo dark flame master & eye of the wicked lord", value="rikka"),
        questionary.Choice("🎀 Desk Peeker       — Cute anime girl peeking over terminal edge", value="peeker"),
        questionary.Choice("⚡ Pikachu Spark     — Electric companion cheering your code discoveries", value="pikachu"),
        questionary.Choice("🌟 Cheer Chibi       — Energetic cheerleader celebrating every gem found", value="cheer"),
        questionary.Choice("👁️  Manga Glance      — Aesthetic retro manga eye peeker", value="eyes"),
        questionary.Choice("🍃 Emerald Aoko      — Emerald-haired cyber anime girl", value="emerald"),
        questionary.Choice("⚔️  Katana Blade      — Samurai anime warrior with drawn blade", value="katana"),
        questionary.Choice("💎 Cyber Diamond     — Vector mecha diamond prism emblem", value="logo"),
        questionary.Choice("✦  Celestial Prism   — Minimalist procedural ASCII/ANSI crystal", value="crystal"),
    ]
    mascot = questionary.select(
        "◈ Step 4/5: Choose your Radar Companion Mascot:",
        choices=mascot_choices,
        style=menu_style(),
    ).ask() or "hoodie"

    # Step 5: Visual Skin / Theme
    theme_choices = [
        questionary.Choice("Emerald Moss    (Fresh emerald green, neon jade & forest obsidian)", value="emerald_moss"),
        questionary.Choice("Lavender Night  (Cosmic violet, soft lilac & night amethyst)", value="lavender_night"),
        questionary.Choice("Warm Earth      (Terracotta clay, warm parchment & deep ember)", value="warm_earth"),
        questionary.Choice("Cyber Peach     (Retro neon coral, warm peach & synthwave amber)", value="cyber_peach"),
    ]
    theme = questionary.select(
        "◈ Step 5/5: Select your preferred terminal color skin:",
        choices=theme_choices,
        style=menu_style(),
    ).ask() or "emerald_moss"

    # Save to config
    update_config_value("user_name", name)
    update_config_value("pronouns", pronouns)
    update_config_value("curator_title", archetype)
    update_config_value("mascot", mascot)
    update_config_value("theme", theme)
    update_config_value("onboarded", True)

    # Re-load theme for celebration panel
    t = THEMES.get(theme, THEMES["emerald_moss"])
    mascot_name = MASCOTS.get(mascot, {}).get("name", "Companion")
    greeting = get_personalized_greeting(name, pronouns)

    console.clear()
    celebration_panel = Panel(
        Group(
            Text.from_markup(f"[bold {t['gold']}]✨ RADAR CALIBRATION COMPLETE ✨[/]", justify="center"),
            Text(""),
            Text.from_markup(f"[bold {t['gold']}]{greeting}[/]", justify="center"),
            Text(""),
            Text.from_markup(
                f"[dim {t['cream']}]Callsign:[/] [bold {t['accent']}]{name}[/] {f'({pronouns})' if pronouns else ''}  •  "
                f"[dim {t['cream']}]Archetype:[/] [bold {t['gold']}]{archetype}[/]",
                justify="center",
            ),
            Text.from_markup(
                f"[dim {t['cream']}]Companion:[/] [bold {t['accent']}]{mascot_name}[/]  •  "
                f"[dim {t['cream']}]Theme:[/] [bold {t['cream']}]{t['name']}[/]",
                justify="center",
            ),
            Text(""),
            Text.from_markup(f"[bold {t['accent']}]✦ Your journey into the underground begins now. ✦[/]", justify="center"),
        ),
        box=box.ROUNDED,
        border_style=t["accent"],
        padding=(1, 3),
        width=min(78, console.width - 4),
    )
    console.print(Align.center(celebration_panel))
    console.print()
    try:
        input("  Press [Enter] to launch the Radar Command Palette...")
    except (KeyboardInterrupt, EOFError):
        pass

    return {
        "user_name": name,
        "pronouns": pronouns,
        "curator_title": archetype,
        "mascot": mascot,
        "theme": theme,
        "onboarded": True,
    }
