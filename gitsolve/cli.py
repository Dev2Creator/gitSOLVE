# gitSOLVE ✦ Interactive CLI & Command Palette Router
# Software for Humans. Less terminal drama.

import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional
import typer
import questionary
import pyperclip
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text
from rich import box

from gitsolve import __version__
from gitsolve.config import load_config, save_config, update_config_value
from gitsolve.github import GitHubClient
from gitsolve.scanner import RepoInspector
from gitsolve.vault import Vault
from gitsolve.ui import (
    console,
    get_theme,
    accent,
    cream,
    muted,
    border_color,
    selected_color,
    icon,
    print_banner,
    print_header,
    menu_style,
    command_choice,
    styled_panel,
    render_cinematic_gem,
    styled_error,
    styled_success,
    THEMES,
)

app = typer.Typer(
    help="gitSOLVE ✦ Underground GitHub Radar & Deep X-Ray Code Scanner for 2-5 Star Masterpieces",
    no_args_is_help=False,
)

vault = Vault()
inspector = RepoInspector()

def _prompt_gem_actions(gems: List[Dict[str, Any]], current_idx: int = 0) -> None:
    """Interactive action bar for browsing discovered gems."""
    if not gems:
        console.print(f"[{cream()}]No gems found matching those parameters. Try widening the search![/]")
        return

    total = len(gems)
    idx = max(0, min(current_idx, total - 1))
    gem = gems[idx]

    console.clear()
    print_banner(subtitle=f"GEM {idx + 1} OF {total} • SLEEPER ARCHIVES")
    render_cinematic_gem(gem, index=idx + 1, total=total)

    choices = [
        command_choice("open", "Open repository in web browser", "open"),
        command_choice("clone", "Copy git clone command to clipboard", "clone"),
        command_choice("save", "Save this gem to your 'I Was Here First' Vault", "save"),
        command_choice("xray", "Run full forensic diagnostic breakdown", "xray"),
    ]
    if idx + 1 < total:
        choices.append(command_choice("next", f"Inspect next gem ({idx + 2}/{total})", "next"))
    if idx > 0:
        choices.append(command_choice("prev", f"Go back to previous gem ({idx}/{total})", "prev"))
    choices.append(command_choice("menu", "Return to main command palette", "menu"))

    action = questionary.select(
        "/",
        choices=choices,
        style=menu_style(),
        qmark="",
        instruction="(↑/↓ to move • enter to select)",
    ).ask()

    if action is None or action == "menu":
        return

    if action == "open":
        webbrowser.open(gem["html_url"])
        styled_success(f"Opened {gem['full_name']} in browser.")
        _prompt_gem_actions(gems, idx)
    elif action == "clone":
        cmd = f"git clone {gem['html_url']}.git"
        pyperclip.copy(cmd)
        styled_success(f"Copied to clipboard: {cmd}")
        _prompt_gem_actions(gems, idx)
    elif action == "save":
        success = vault.save_gem(gem)
        if success:
            styled_success(f"Locked {gem['full_name']} into your Vault! 🏆")
        else:
            styled_error("Could not save to Vault.")
        _prompt_gem_actions(gems, idx)
    elif action == "xray":
        _run_xray(gem["full_name"])
        input("\nPress Enter to return to gem...")
        _prompt_gem_actions(gems, idx)
    elif action == "next":
        _prompt_gem_actions(gems, idx + 1)
    elif action == "prev":
        _prompt_gem_actions(gems, idx - 1)

def _run_xray(repo_name: str) -> None:
    t = get_theme()
    console.print(f"[{accent()}]Scanning repository forensic telemetry for {repo_name}...[/]")
    try:
        gem = inspector.xray_repo(repo_name)
    except Exception as e:
        styled_error(f"Failed to run X-Ray on {repo_name}", str(e))
        return

    table = Table(box=box.SQUARE, border_style=t["border"], expand=True, show_header=True, header_style=f"bold {accent()}")
    table.add_column("Diagnostic Metric", style=f"bold {t['cream']}")
    table.add_column("Result / Finding", style=t["cream"])

    table.add_row("Repository", f"[{accent()}]{gem['full_name']}[/]")
    table.add_row("Current Stars", f"⭐ {gem['stars']}")
    table.add_row("Project Age", f"{gem['age_text']}")
    table.add_row("Recent Activity", f"Pushed {gem['pushed_days']} days ago")
    table.add_row("Sleeper Rating", f"[{t['gold']} bold]{gem['sleeper_score']} / 100[/]")
    table.add_row("Automated Tests", "[green]PASSING / PRESENT[/green]" if gem["has_tests"] else "[dim]Not detected[/dim]")
    table.add_row("CI/CD Workflows", "[green]CONFIGURED[/green]" if gem["has_ci"] else "[dim]Not detected[/dim]")
    table.add_row("Estimated LoC", f"~{gem.get('loc_estimate', 0):,} lines of core logic")
    table.add_row("License", gem.get("license") or "No official license found")

    console.print()
    console.print(table)
    console.print()

    if gem.get("findings"):
        console.print(f"[bold {accent()}]Forensic Inspection Findings:[/]")
        for f in gem["findings"]:
            console.print(f"  [{accent()}]•[/] [{cream()}]{f}[/]")
        console.print()

# --- Interactive Commands ---------------------------------------------------
def interactive_radar() -> None:
    t = get_theme()
    console.clear()
    print_banner(subtitle="RADAR SEARCH • CALIBRATING ANTENNA")

    topic = questionary.text("Filter by topic (e.g. ai, cli, compiler, database, leave empty for any):", style=menu_style()).ask()
    lang = questionary.text("Filter by language (e.g. rust, python, go, ts, leave empty for any):", style=menu_style()).ask()
    query = questionary.text("Extra search keywords (leave empty for broad radar):", style=menu_style()).ask()

    stars_choice = questionary.select(
        "Select star range:",
        choices=[
            questionary.Choice("1 to 5 stars (Ultra underground alpha)", value=(1, 5)),
            questionary.Choice("2 to 7 stars (The sweet spot)", value=(2, 7)),
            questionary.Choice("5 to 15 stars (Gaining early momentum)", value=(5, 15)),
        ],
        style=menu_style(),
    ).ask()

    min_s, max_s = stars_choice if stars_choice else (2, 7)

    console.print(f"\n[{accent()}]Spinning radar array... scanning GitHub stream...[/]")
    try:
        gems = inspector.search_radar(
            topic=topic or "",
            language=lang or "",
            query_text=query or "",
            min_stars=min_s,
            max_stars=max_s,
            limit=8,
        )
        cfg = load_config()
        update_config_value("scans_completed", cfg.get("scans_completed", 0) + 1)
        if not gems:
            styled_error("No repositories matched those exact coordinates. Try a broader topic or language.")
            input("\nPress Enter to return...")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Radar scan failed", str(e))
        input("\nPress Enter to return...")

def interactive_fresh() -> None:
    console.clear()
    print_banner(subtitle="LIVE RADAR • REPOS UPDATED IN THE LAST 48 HOURS")
    lang = questionary.text("Language filter (leave empty for all):", style=menu_style()).ask()
    console.print(f"\n[{accent()}]Interrogating live GitHub commit stream...[/]")
    try:
        gems = inspector.search_fresh(language=lang or "", limit=8)
        if not gems:
            styled_error("No fresh active sleepers found in the last 48 hours for that filter.")
            input("\nPress Enter to return...")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Fresh scan failed", str(e))
        input("\nPress Enter to return...")

def interactive_xray() -> None:
    console.clear()
    print_banner(subtitle="X-RAY FORENSICS • DIAGNOSTIC SCANNER")
    repo_input = questionary.text("Enter GitHub repo (e.g. owner/repo or full URL):", style=menu_style()).ask()
    if repo_input:
        _run_xray(repo_input)
    input("\nPress Enter to return...")

def interactive_compare() -> None:
    console.clear()
    print_banner(subtitle="HEAD-TO-HEAD • SLEEPER SHOWDOWN")
    repo1 = questionary.text("First repository (owner/repo):", style=menu_style()).ask()
    repo2 = questionary.text("Second repository (owner/repo):", style=menu_style()).ask()

    if not repo1 or not repo2:
        return

    t = get_theme()
    console.print(f"[{accent()}]Running dual X-Ray telemetry...[/]")
    try:
        g1 = inspector.xray_repo(repo1)
        g2 = inspector.xray_repo(repo2)
    except Exception as e:
        styled_error("Failed to fetch one or both repositories", str(e))
        input("\nPress Enter to return...")
        return

    table = Table(box=box.SQUARE, border_style=t["border"], expand=True, header_style=f"bold {accent()}")
    table.add_column("Telemetry", style=f"bold {t['muted']}")
    table.add_column(g1["full_name"], style=t["cream"])
    table.add_column(g2["full_name"], style=t["cream"])

    table.add_row("Sleeper Rating", f"[{t['gold']} bold]{g1['sleeper_score']} / 100[/]", f"[{t['gold']} bold]{g2['sleeper_score']} / 100[/]")
    table.add_row("Stars", f"⭐ {g1['stars']}", f"⭐ {g2['stars']}")
    table.add_row("Language", g1["primary_language"], g2["primary_language"])
    table.add_row("Age", g1["age_text"], g2["age_text"])
    table.add_row("Tests", "✓ Present" if g1["has_tests"] else "✗ Missing", "✓ Present" if g2["has_tests"] else "✗ Missing")
    table.add_row("CI/CD", "✓ Configured" if g1["has_ci"] else "✗ Missing", "✓ Configured" if g2["has_ci"] else "✗ Missing")
    table.add_row("Estimated LoC", f"~{g1['loc_estimate']:,}", f"~{g2['loc_estimate']:,}")

    console.print()
    console.print(table)
    console.print()
    input("\nPress Enter to return...")

def interactive_author() -> None:
    console.clear()
    print_banner(subtitle="AUTHOR ARCHAEOLOGY • SOLO CREATOR MINING")
    username = questionary.text("Enter GitHub username:", style=menu_style()).ask()
    if not username:
        return
    console.print(f"[{accent()}]Excavating underground catalog of @{username}...[/]")
    try:
        gems = inspector.author_gems(username, limit=8)
        if not gems:
            styled_error(f"No underground gems found for @{username}.")
            input("\nPress Enter to return...")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Failed to query author", str(e))
        input("\nPress Enter to return...")

def interactive_lucky() -> None:
    console.clear()
    print_banner(subtitle="FEELING LUCKY • INSTANT MYTHIC SLEEPER")
    console.print(f"[{accent()}]Summoning a top-tier handcrafted repository...[/]")
    try:
        gems = inspector.search_radar(min_stars=2, max_stars=6, limit=6)
        if gems:
            _prompt_gem_actions([gems[0]], 0)
        else:
            styled_error("Could not find a lucky gem right now.")
            input("\nPress Enter to return...")
    except Exception as e:
        styled_error("Failed to summon lucky gem", str(e))
        input("\nPress Enter to return...")

def interactive_vault() -> None:
    t = get_theme()
    console.clear()
    print_banner(subtitle="THE VAULT • YOUR 'I WAS HERE FIRST' PORTFOLIO")

    gems = vault.list_gems()
    rank, rank_desc = vault.get_curator_rank()

    console.print(styled_panel(
        f"[bold {t['accent']}]Curator Rank:[/][{t['gold']} bold]{rank}[/]\n"
        f"[{t['cream']}]{rank_desc}[/]\n"
        f"[{t['muted']}]Total Saved:[/] [{t['cream']}]{len(gems)} underground gems[/]",
        title="PORTFOLIO TELEMETRY"
    ))
    console.print()

    if not gems:
        console.print(f"[{cream()}]Your Vault is currently empty! Use /radar or /fresh to discover gems and press [s] to save.[/]\n")
        input("Press Enter to return...")
        return

    table = Table(box=box.SQUARE, border_style=t["border"], expand=True, header_style=f"bold {accent()}")
    table.add_column("Repository", style=f"bold {t['cream']}")
    table.add_column("Discovered ⭐", style=t["muted"])
    table.add_column("Current ⭐", style=t["gold"])
    table.add_column("Alpha Gain", style=f"bold {accent()}")
    table.add_column("Language", style=t["cream"])

    for g in gems:
        delta = g["last_checked_stars"] - g["discovered_stars"]
        delta_str = f"▲ +{delta}" if delta >= 0 else f"▼ {delta}"
        table.add_row(
            g["full_name"],
            str(g["discovered_stars"]),
            str(g["last_checked_stars"]),
            delta_str,
            g["primary_language"] or "Code",
        )

    console.print(table)
    console.print()

    action = questionary.select(
        "/",
        choices=[
            command_choice("refresh", "Ping GitHub for fresh live star counts", "refresh"),
            command_choice("export", "Export portfolio to Markdown file", "export"),
            command_choice("back", "Return to main palette", "back"),
        ],
        style=menu_style(),
    ).ask()

    if action == "refresh":
        console.print(f"[{accent()}]Refreshing star counts from GitHub...[/]")
        vault.refresh_vault(inspector.client)
        interactive_vault()
    elif action == "export":
        out_path = Path.cwd() / "gitsolve_portfolio.md"
        vault.export_markdown(out_path)
        styled_success(f"Exported portfolio to {out_path.name}!")
        input("\nPress Enter to return...")

def interactive_theme() -> None:
    console.clear()
    print_banner(subtitle="THEME SELECTOR • IRL™ PALETTE")
    cfg = load_config()
    current_theme = cfg.get("theme", "warm_earth")

    choices = [
        questionary.Choice(f"{v['name']} {'(Active)' if k == current_theme else ''}", value=k)
        for k, v in THEMES.items()
    ]
    choices.append(questionary.Choice("Back", value="back"))

    selected = questionary.select("Select visual skin:", choices=choices, style=menu_style()).ask()
    if selected and selected != "back":
        update_config_value("theme", selected)
        styled_success(f"Switched skin to {THEMES[selected]['name']}!")
        input("\nPress Enter to reload...")

def interactive_config() -> None:
    console.clear()
    print_banner(subtitle="CONFIGURATION • SYSTEM SETTINGS")
    cfg = load_config()

    action = questionary.select(
        "Choose setting to configure:",
        choices=[
            questionary.Choice("Set GitHub Personal Access Token (Unlocks 5,000 req/hr)", value="token"),
            questionary.Choice(f"Toggle Icon Mode (Currently: {cfg.get('icons_mode', 'auto')})", value="icons"),
            questionary.Choice(f"Default Language Filter (Currently: '{cfg.get('default_language', '') or 'Any'}')", value="lang"),
            questionary.Choice("Back", value="back"),
        ],
        style=menu_style(),
    ).ask()

    if action == "token":
        tok = questionary.password("Paste your GitHub Personal Access Token (classic or fine-grained):", style=menu_style()).ask()
        if tok is not None:
            update_config_value("github_token", tok.strip())
            styled_success("GitHub token safely updated!")
    elif action == "icons":
        mode = questionary.select(
            "Select icon mode:",
            choices=[
                questionary.Choice("Auto (Nerd Font if terminal supports, else ASCII)", value="auto"),
                questionary.Choice("Always Nerd Fonts", value="nerd"),
                questionary.Choice("Strict ASCII Only", value="ascii"),
            ],
            style=menu_style(),
        ).ask()
        if mode:
            update_config_value("icons_mode", mode)
            styled_success(f"Icon mode set to {mode}!")
    elif action == "lang":
        new_lang = questionary.text("Enter default language (leave blank for any):", style=menu_style()).ask()
        if new_lang is not None:
            update_config_value("default_language", new_lang.strip())
            styled_success("Default language updated!")

    input("\nPress Enter to return...")

# --- Main Command Palette Loop ----------------------------------------------
def run_command_palette() -> None:
    while True:
        console.clear()
        print_header(title="COMMAND PALETTE", status_text="Ready — choose a command below")

        action = questionary.select(
            "/",
            choices=[
                command_choice("radar", "Scan underground repos by topic & language", "radar"),
                command_choice("fresh", "Stream active repos updated in the last 48 hours", "fresh"),
                command_choice("xray", "Deep forensic inspection of ANY repo URL", "xray"),
                command_choice("compare", "Head-to-head sleeper showdown between 2 repos", "compare"),
                command_choice("author", "Mine underground gems by a specific solo dev", "author"),
                command_choice("lucky", "Instant random mythic sleeper", "lucky"),
                command_choice("vault", "View your 'I Was Here First' portfolio & star gains", "vault"),
                command_choice("theme", "Switch IRL visual theme (Clay, Peach, Moss, Night)", "theme"),
                command_choice("config", "GitHub token & system preferences", "config"),
                command_choice("exit", "Leave gitSOLVE", "exit"),
            ],
            style=menu_style(),
            qmark="",
            instruction="(↑/↓ to move • enter to select)",
        ).ask()

        if action is None or action == "exit":
            console.print(f"\n[{accent()}]✦ Safe travels. Keep building real things. ✦[/]\n")
            break
        elif action == "radar":
            interactive_radar()
        elif action == "fresh":
            interactive_fresh()
        elif action == "xray":
            interactive_xray()
        elif action == "compare":
            interactive_compare()
        elif action == "author":
            interactive_author()
        elif action == "lucky":
            interactive_lucky()
        elif action == "vault":
            interactive_vault()
        elif action == "theme":
            interactive_theme()
        elif action == "config":
            interactive_config()

# --- Direct CLI Subcommands -------------------------------------------------
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """gitSOLVE entrypoint. Launches command palette if no subcommand provided."""
    if ctx.invoked_subcommand is None:
        run_command_palette()

@app.command("radar")
def cmd_radar(
    topic: str = typer.Option("", "--topic", "-t", help="Filter by topic"),
    lang: str = typer.Option("", "--lang", "-l", help="Filter by language"),
    query: str = typer.Option("", "--query", "-q", help="Search keywords"),
    stars: str = typer.Option("2..7", "--stars", "-s", help="Stars range (e.g. 2..7)"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems to inspect"),
):
    """Direct CLI: Scan underground repos with precision filters."""
    min_s, max_s = 2, 7
    if ".." in stars:
        parts = stars.split("..")
        try:
            min_s, max_s = int(parts[0]), int(parts[1])
        except Exception:
            pass

    console.print(f"[{accent()}]Spinning radar array...[/]")
    try:
        gems = inspector.search_radar(
            topic=topic,
            language=lang,
            query_text=query,
            min_stars=min_s,
            max_stars=max_s,
            limit=limit,
        )
        if not gems:
            styled_error("No repositories found matching those criteria.")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Radar failed", str(e))

@app.command("xray")
def cmd_xray(repo: str = typer.Argument(..., help="GitHub repo name (owner/repo)")):
    """Direct CLI: Deep forensic X-ray inspection of a specific repo."""
    _run_xray(repo)

@app.command("vault")
def cmd_vault(refresh: bool = typer.Option(False, "--refresh", "-r", help="Refresh star counts from GitHub")):
    """Direct CLI: View your saved gem portfolio."""
    if refresh:
        console.print(f"[{accent()}]Refreshing star counts...[/]")
        vault.refresh_vault(inspector.client)
    interactive_vault()

@app.command("fresh")
def cmd_fresh(
    lang: str = typer.Option("", "--lang", "-l", help="Language filter"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems to inspect"),
):
    """Direct CLI: Stream active repos updated in the last 48 hours."""
    console.print(f"[{accent()}]Scanning live commits in the last 48 hours...[/]")
    try:
        gems = inspector.search_fresh(language=lang, limit=limit)
        if not gems:
            styled_error("No fresh active sleepers found in the last 48 hours.")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Fresh scan failed", str(e))

@app.command("compare")
def cmd_compare(
    repo1: str = typer.Argument(..., help="First repo (owner/repo)"),
    repo2: str = typer.Argument(..., help="Second repo (owner/repo)"),
):
    """Direct CLI: Compare two repos side-by-side."""
    t = get_theme()
    console.print(f"[{accent()}]Running dual X-Ray telemetry...[/]")
    try:
        g1 = inspector.xray_repo(repo1)
        g2 = inspector.xray_repo(repo2)
    except Exception as e:
        styled_error("Failed to fetch repositories", str(e))
        return

    table = Table(box=box.SQUARE, border_style=t["border"], expand=True, header_style=f"bold {accent()}")
    table.add_column("Telemetry", style=f"bold {t['muted']}")
    table.add_column(g1["full_name"], style=t["cream"])
    table.add_column(g2["full_name"], style=t["cream"])

    table.add_row("Sleeper Rating", f"[{t['gold']} bold]{g1['sleeper_score']} / 100[/]", f"[{t['gold']} bold]{g2['sleeper_score']} / 100[/]")
    table.add_row("Stars", f"⭐ {g1['stars']}", f"⭐ {g2['stars']}")
    table.add_row("Language", g1["primary_language"], g2["primary_language"])
    table.add_row("Age", g1["age_text"], g2["age_text"])
    table.add_row("Tests", "✓ Present" if g1["has_tests"] else "✗ Missing", "✓ Present" if g2["has_tests"] else "✗ Missing")
    table.add_row("CI/CD", "✓ Configured" if g1["has_ci"] else "✗ Missing", "✓ Configured" if g2["has_ci"] else "✗ Missing")
    table.add_row("Estimated LoC", f"~{g1['loc_estimate']:,}", f"~{g2['loc_estimate']:,}")

    console.print()
    console.print(table)
    console.print()

@app.command("author")
def cmd_author(
    username: str = typer.Argument(..., help="GitHub username to inspect"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems"),
):
    """Direct CLI: Mine underground gems by a specific solo dev."""
    console.print(f"[{accent()}]Excavating catalog of @{username}...[/]")
    try:
        gems = inspector.author_gems(username, limit=limit)
        if not gems:
            styled_error(f"No underground gems found for @{username}.")
            return
        _prompt_gem_actions(gems, 0)
    except Exception as e:
        styled_error("Author search failed", str(e))

@app.command("lucky")
def cmd_lucky():
    """Direct CLI: Instant random mythic sleeper."""
    interactive_lucky()

@app.command("theme")
def cmd_theme(name: Optional[str] = typer.Argument(None, help="Theme name (warm_earth, cyber_peach, emerald_moss, lavender_night)")):
    """Direct CLI: Switch IRL visual theme."""
    if name and name in THEMES:
        update_config_value("theme", name)
        styled_success(f"Switched theme to {THEMES[name]['name']}!")
    else:
        interactive_theme()

@app.command("config")
def cmd_config():
    """Direct CLI: Open system preferences & token setup."""
    interactive_config()

@app.command("version")
def cmd_version():
    """Print gitSOLVE version."""
    console.print(f"[bold {accent()}]gitSOLVE[/] [{cream()}]v{__version__}[/]")

def main():
    app()

if __name__ == "__main__":
    main()
