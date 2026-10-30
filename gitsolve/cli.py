# gitSOLVE ✦ Interactive CLI & Command Palette Router
# Software for Humans. Underground code. Zero hype.

import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional
import typer
import questionary
import pyperclip
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from gitsolve import __version__
from gitsolve.config import load_config, save_config, update_config_value
from gitsolve.github import GitHubClient
from gitsolve.scanner import RepoInspector
from gitsolve.vault import Vault
from gitsolve.ai import PollinationsClient
from gitsolve.animation import (
    radar_pulse,
    neural_pulse,
    render_meter,
    render_sparkline,
    render_language_bar,
    render_pill,
)
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
    print_keymap_footer,
    get_layout_width,
    menu_style,
    command_choice,
    select_menu,
    get_menu_indent,
    styled_panel,
    render_cinematic_gem,
    render_flight_board,
    render_theme_gallery,
    render_empty_state,
    render_xray_report,
    render_ai_teardown,
    render_markdown_viewer,
    render_tree_viewer,
    render_commits_viewer,
    render_rate_limit_table,
    styled_error,
    styled_success,
    status_dot,
    THEMES,
    MASCOTS,
)
from gitsolve.onboarding import is_onboarding_needed, run_onboarding_ceremony

app = typer.Typer(
    help="gitSOLVE ✦ Underground GitHub Radar & Deep X-Ray Code Scanner for 2-7 Star Masterpieces",
    no_args_is_help=False,
)

vault = Vault()
ai_client = PollinationsClient()
inspector = RepoInspector(client=None, vault=vault, ai_client=ai_client)

def _board_row_label(gem: Dict[str, Any], rank: int) -> str:
    """Questionary-friendly plain-text row label for the flight board."""
    overall = gem.get("overall_score", 0)
    if overall >= 88:
        glyph = "💎"
    elif overall >= 74:
        glyph = "🔥"
    else:
        glyph = "✨"
    tier_label = "MYTHIC" if overall >= 88 else ("GOLD" if overall >= 74 else "GEM")
    name = gem.get("full_name", "?")
    lang = (gem.get("primary_language") or "—")[:9]
    return f" {rank:02d}  {name:<42} {glyph} {tier_label:<6} {overall:>3}/100   ⭐{gem.get('stars', 0):<4} {lang}"

def browse_gems(gems: List[Dict[str, Any]], subtitle: str = "RADAR SWEEP • FLIGHT BOARD") -> None:
    """Cinematic ranked board of all specimens; select one to open its specimen card."""
    while True:
        console.clear()
        print_banner(subtitle=subtitle)
        render_flight_board(gems)

        choices = [questionary.Choice(_board_row_label(g, i + 1), value=i) for i, g in enumerate(gems)]
        choices.append(questionary.Choice("✕  Back to command palette", value=None))
        picked = select_menu(choices, instruction="(↑/↓ to fly over specimens • enter to inspect)")
        if picked is None:
            return
        result = _prompt_gem_actions(gems, picked)
        if result == "board":
            continue
        return

def _prompt_gem_actions(gems: List[Dict[str, Any]], current_idx: int = 0) -> Optional[str]:
    """Interactive action bar for browsing discovered gems with full hotkeys.
    Returns 'board' to redisplay the flight board, 'menu' to exit to palette."""
    if not gems:
        console.print(f"[{cream()}]No gems found matching those parameters. Try widening the search![/]")
        return None

    total = len(gems)
    idx = max(0, min(current_idx, total - 1))
    gem = gems[idx]

    console.clear()
    print_banner(subtitle=f"SPECIMEN {idx + 1} OF {total} • SLEEPER ARCHIVES")
    render_cinematic_gem(gem, index=idx + 1, total=total)

    choices = [
        command_choice("open", "Open repository in web browser", "open", "↗"),
        command_choice("clone", "Copy git clone command or clone locally", "clone", "📋"),
        command_choice("save", "Save this gem to your 'I Was Here First' Vault", "save", "🏆"),
        command_choice("ai", "Deep architectural verdict & interactive Q&A (Pollinations)", "ai", "◈"),
        command_choice("readme", "Read formatted documentation directly in terminal", "readme", "📖"),
        command_choice("tree", "Inspect repository file hierarchy & architecture", "tree", "🌳"),
        command_choice("commits", "Inspect recent commit history & craftsmanship", "commits", "📜"),
        command_choice("xray", "Run full forensic diagnostic breakdown", "xray", "◎"),
        command_choice("forks", "Scan for active & valuable forks with independent changes", "forks", "⑂"),
    ]
    if idx + 1 < total:
        choices.append(command_choice("next", f"Inspect next gem ({idx + 2}/{total})", "next", "▸"))
    if idx > 0:
        choices.append(command_choice("prev", f"Go back to previous gem ({idx}/{total})", "prev", "◂"))
    if total > 1:
        choices.append(command_choice("board", "Back to the ranked flight board view", "board", "▦"))
    choices.append(command_choice("menu", "Return to main command palette", "menu", "✕"))

    action = select_menu(choices)

    if action is None or action == "menu":
        return "menu"
    if action == "board":
        return "board"

    if action == "open":
        webbrowser.open(gem["html_url"])
        styled_success(f"Opened {gem['full_name']} in browser.")
        return _prompt_gem_actions(gems, idx)
    elif action == "clone":
        clone_choice = select_menu(
            choices=[
                questionary.Choice("📋  Copy 'git clone' command to clipboard", value="copy"),
                questionary.Choice("🌐  Open repository in web browser", value="open"),
                questionary.Choice("◂   Back to gem", value="back"),
            ],
            instruction="(Clone Options • ↑/↓ to move • enter to select)",
        )
        if clone_choice == "copy":
            cmd = f"git clone {gem['html_url']}.git"
            pyperclip.copy(cmd)
            styled_success(f"Copied to clipboard: {cmd}")
        elif clone_choice == "open":
            webbrowser.open(gem["html_url"])
            styled_success(f"Opened {gem['full_name']} in browser.")
        return _prompt_gem_actions(gems, idx)
    elif action == "save":
        tags_input = questionary.text("Add tags (comma-separated, e.g. ai, compiler, tool - or enter to skip):", style=menu_style()).ask()
        notes_input = questionary.text("Add curator note (why is this special? - or enter to skip):", style=menu_style()).ask()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        success = vault.save_gem(gem, tags=tags, notes=notes_input or "")
        if success:
            styled_success(f"Locked {gem['full_name']} into your Vault! 🏆")
        else:
            styled_error("Could not save to Vault.")
        return _prompt_gem_actions(gems, idx)
    elif action == "readme":
        with radar_pulse(f"Fetching README for {gem['full_name']}"):
            rm_text = inspector.get_readme(gem["full_name"])
        if rm_text:
            gem["readme"] = rm_text
            render_markdown_viewer(f"{gem['full_name']} README", rm_text)
        else:
            styled_error(
                f"No README documentation found for {gem['full_name']}.",
                hint="Verify that the repository is public and contains a README file (Markdown/RST/plain text)."
            )
        input("\nPress Enter to return to gem...")
        return _prompt_gem_actions(gems, idx)
    elif action == "tree":
        with radar_pulse(f"Excavating architecture tree for {gem['full_name']}"):
            tree_items = inspector.get_tree_structure(gem["full_name"])
        if tree_items:
            render_tree_viewer(gem["full_name"], tree_items)
        else:
            styled_error(f"Could not retrieve file tree for {gem['full_name']}.")
        input("\nPress Enter to return to gem...")
        return _prompt_gem_actions(gems, idx)
    elif action == "commits":
        with radar_pulse(f"Excavating recent commit history for {gem['full_name']}"):
            commits = inspector.get_recent_commits(gem["full_name"], limit=6)
            cadence = inspector.get_commit_cadence(gem["full_name"])
        if commits:
            render_commits_viewer(gem["full_name"], commits, cadence=cadence)
        else:
            styled_error(f"Could not retrieve commit history for {gem['full_name']}.")
        input("\nPress Enter to return to gem...")
        return _prompt_gem_actions(gems, idx)
    elif action == "ai":
        if "readme" not in gem:
            with radar_pulse(f"Gathering codebase documentation for {gem['full_name']}"):
                try:
                    gem["readme"] = inspector.get_readme(gem["full_name"]) or ""
                except Exception:
                    pass
        with neural_pulse(f"Synthesizing deep architectural teardown for {gem['full_name']}"):
            summary = ai_client.explain_repo(gem, readme_snippet=gem.get("readme", ""))
        render_ai_teardown(summary, gem["full_name"])
        while True:
            follow_up = questionary.text("Ask follow-up question about this codebase (or press Enter to return):", style=menu_style()).ask()
            if not follow_up or not follow_up.strip():
                break
            with neural_pulse(f"Consulting Pollinations AI"):
                ans = ai_client.ask_repo(gem, follow_up.strip())
            console.print(f"[bold {accent()}]Q:[/] [{cream()}]{follow_up}[/]\n")
            render_ai_teardown(ans, gem["full_name"])
        return _prompt_gem_actions(gems, idx)
    elif action == "xray":
        _run_xray(gem["full_name"])
        input("\nPress Enter to return to gem...")
        return _prompt_gem_actions(gems, idx)
    elif action == "forks":
        _run_forks(gem["full_name"])
        input("\nPress Enter to return to gem...")
        return _prompt_gem_actions(gems, idx)
    elif action == "next":
        return _prompt_gem_actions(gems, idx + 1)
    elif action == "prev":
        return _prompt_gem_actions(gems, idx - 1)
    return "menu"

def _run_xray(repo_name: str) -> Optional[Dict[str, Any]]:
    """Runs deep forensic X-Ray inspection and displays report."""
    with radar_pulse(f"Interrogating forensic telemetry for {repo_name}"):
        try:
            gem = inspector.xray_repo(repo_name)
        except Exception as e:
            styled_error(f"Failed to run X-Ray on {repo_name}", str(e))
            return None

    render_xray_report(gem)
    return gem

def _run_forks(repo_name: str) -> List[Dict[str, Any]]:
    """Scans and displays active and diverged community forks."""
    t = get_theme()
    with radar_pulse(f"Scanning fork divergence & commit strata for {repo_name}"):
        try:
            forks = inspector.search_forks(repo_name, limit=10)
        except Exception as e:
            styled_error(f"Failed to query forks for {repo_name}", str(e))
            return []

    if not forks:
        console.print(f"[{cream()}]No independent, actively diverged forks found for {repo_name}.[/]")
        return []

    table = Table(
        box=box.ROUNDED,
        border_style=t["border"],
        expand=False,
        width=get_layout_width(),
        show_header=True,
        header_style=f"bold {accent()}",
    )
    table.add_column("Fork Repository", style=f"bold {t['cream']}", ratio=2)
    table.add_column("Stars", style=t["gold"], justify="right")
    table.add_column("Ahead Commits", style=f"bold {accent()}", justify="right")
    table.add_column("Last Push", style=t["cream"])
    table.add_column("Significant Changes / Title", style=t["muted"], ratio=3)

    for f in forks:
        ahead_str = f"▲ +{f['ahead_by']}" if f.get("ahead_by", 0) > 0 else "0"
        table.add_row(
            f["full_name"],
            f"⭐ {f['stars']}",
            ahead_str,
            f"{f.get('pushed_days', 0)}d ago",
            f.get("description") or "Fork with custom modifications",
        )

    console.print()
    console.print(Align.center(table))
    console.print()
    return forks

# --- Interactive Commands ---------------------------------------------------
def interactive_radar() -> None:
    t = get_theme()
    console.clear()
    print_banner(subtitle="RADAR SEARCH • CALIBRATING ANTENNA")

    preset = questionary.select(
        "Select Radar Preset:",
        choices=[
            questionary.Choice("🦀  Rust Alpha         Lock-free, SIMD, compilers, systems (2..7 ★)", value="rust"),
            questionary.Choice("🐍  Python Deep-Tech   Compilers, local AI, math kernels, CLI (2..7 ★)", value="python"),
            questionary.Choice("🐹  Go Concurrency     Network engines, distributed tools, TUI (2..7 ★)", value="go"),
            questionary.Choice("⚡  C/C++ Performance  Allocators, engines, graphics, kernels (2..7 ★)", value="c"),
            questionary.Choice("🌐  TypeScript / WASM  Compilers, parsers, browser runtime tools (2..7 ★)", value="typescript"),
            questionary.Choice("🔒  Security & Crypto  Post-quantum, ZK, reverse-engineering (2..7 ★)", value="security"),
            questionary.Choice("🛠️   Handcrafted CLI    Pure terminal craftsmanship, Charm/TUI (2..7 ★)", value="cli"),
            questionary.Choice("🔍  Custom Radar       Configure custom topic, language, and stars", value="custom"),
        ],
        style=menu_style(),
    ).ask()

    if preset is None:
        return

    topic = ""
    lang = ""
    query = ""
    min_s, max_s = 2, 7

    if preset == "rust":
        lang = "rust"
        topic = "system"
    elif preset == "python":
        lang = "python"
        topic = "compiler"
    elif preset == "go":
        lang = "go"
        topic = "cli"
    elif preset == "c":
        lang = "c"
        topic = "performance"
    elif preset == "typescript":
        lang = "typescript"
        topic = "wasm"
    elif preset == "security":
        topic = "security"
    elif preset == "cli":
        topic = "tui"
    elif preset == "custom":
        topic = questionary.text("Filter by topic (e.g. ai, cli, compiler, database, leave empty for any):", style=menu_style()).ask() or ""
        lang = questionary.text("Filter by language (e.g. rust, python, go, ts, leave empty for any):", style=menu_style()).ask() or ""
        query = questionary.text("Extra search keywords (leave empty for broad radar):", style=menu_style()).ask() or ""
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

    with radar_pulse("Spinning radar array & scanning GitHub stream"):
        try:
            gems = inspector.search_radar(
                topic=topic or "",
                language=lang or "",
                query_text=query or "",
                min_stars=min_s,
                max_stars=max_s,
                limit=8,
            )
        except Exception as e:
            styled_error("Radar scan failed", str(e))
            input("\nPress Enter to return...")
            return

    cfg = load_config()
    update_config_value("scans_completed", cfg.get("scans_completed", 0) + 1)
    if not gems:
        render_empty_state(
            "Radar Silence",
            "No repositories matched those exact coordinates.",
            hint="Try a broader topic, language, or star range.",
        )
        input("\nPress Enter to return...")
        return
    browse_gems(gems, subtitle="RADAR SEARCH • RANKED SWEEP RESULTS")

def interactive_fresh() -> None:
    console.clear()
    print_banner(subtitle="LIVE RADAR • REPOS UPDATED IN THE LAST 48 HOURS")
    lang = questionary.text("Language filter (leave empty for all):", style=menu_style()).ask()
    with radar_pulse("Interrogating live GitHub commit stream"):
        try:
            gems = inspector.search_fresh(language=lang or "", limit=8)
        except Exception as e:
            styled_error("Fresh scan failed", str(e))
            input("\nPress Enter to return...")
            return

    if not gems:
        render_empty_state(
            "Radar Silence",
            "No fresh active sleepers found in the last 48 hours for that filter.",
            hint="Widen the language filter or check back after the next commit wave.",
        )
        input("\nPress Enter to return...")
        return
    browse_gems(gems, subtitle="LIVE RADAR • FRESH SLEEPER BOARD")

def interactive_xray() -> None:
    console.clear()
    print_banner(subtitle="X-RAY FORENSICS • DIAGNOSTIC SCANNER")
    repo_input = questionary.text("Enter GitHub repo (e.g. owner/repo or full URL):", style=menu_style()).ask()
    if repo_input:
        _run_xray(repo_input.strip())
    input("\nPress Enter to return...")

def interactive_forks() -> None:
    console.clear()
    print_banner(subtitle="FORK INTELLIGENCE • COMMUNITY MODIFICATIONS")
    repo_input = questionary.text("Enter target repo to scan forks (owner/repo):", style=menu_style()).ask()
    if repo_input:
        _run_forks(repo_input.strip())
    input("\nPress Enter to return...")

def interactive_compare() -> None:
    console.clear()
    print_banner(subtitle="HEAD-TO-HEAD • SLEEPER SHOWDOWN")
    repo1 = questionary.text("First repository (owner/repo):", style=menu_style()).ask()
    repo2 = questionary.text("Second repository (owner/repo):", style=menu_style()).ask()

    if not repo1 or not repo2:
        return

    t = get_theme()
    with radar_pulse("Running dual X-Ray forensic telemetry"):
        try:
            g1 = inspector.xray_repo(repo1.strip())
            g2 = inspector.xray_repo(repo2.strip())
        except Exception as e:
            styled_error("Failed to fetch one or both repositories", str(e))
            input("\nPress Enter to return...")
            return

    table = Table(
        box=box.ROUNDED,
        border_style=t["border"],
        expand=False,
        width=get_layout_width(),
        header_style=f"bold {accent()}",
    )
    table.add_column("Diagnostic Telemetry", style=f"bold {t['muted']}")
    table.add_column(g1["full_name"], style=t["cream"])
    table.add_column(g2["full_name"], style=t["cream"])

    table.add_row(
        "Overall Rating",
        f"[{t['gold']} bold]{g1.get('overall_score', 80)} / 100[/]",
        f"[{t['gold']} bold]{g2.get('overall_score', 80)} / 100[/]",
    )
    table.add_row(
        "Repository Health",
        render_meter(g1.get("health_score", 75), 100, width=8, fill_color="#68D391"),
        render_meter(g2.get("health_score", 75), 100, width=8, fill_color="#68D391"),
    )
    table.add_row(
        "Discovery Potential",
        render_meter(g1.get("discovery_score", 85), 100, width=8, fill_color=accent()),
        render_meter(g2.get("discovery_score", 85), 100, width=8, fill_color=accent()),
    )
    table.add_row("Stars & Forks", f"⭐ {g1['stars']} • 🍴 {g1.get('forks', 0)}", f"⭐ {g2['stars']} • 🍴 {g2.get('forks', 0)}")
    table.add_row("Primary Language", g1.get("primary_language", "Code"), g2.get("primary_language", "Code"))
    table.add_row("Project Age", g1.get("age_text", "Unknown"), g2.get("age_text", "Unknown"))
    table.add_row("Automated Tests", "✓ Present" if g1.get("has_tests") else "✗ Missing", "✓ Present" if g2.get("has_tests") else "✗ Missing")
    table.add_row("CI/CD Automation", "✓ Configured" if g1.get("has_ci") else "✗ Missing", "✓ Configured" if g2.get("has_ci") else "✗ Missing")
    table.add_row("Estimated LoC", f"~{g1.get('loc_estimate', 0):,}", f"~{g2.get('loc_estimate', 0):,}")
    table.add_row("License", g1.get("license") or "None", g2.get("license") or "None")

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
    with radar_pulse(f"Excavating underground catalog of @{username}"):
        try:
            gems = inspector.author_gems(username.strip(), limit=8)
        except Exception as e:
            styled_error("Failed to query author", str(e))
            input("\nPress Enter to return...")
            return

    if not gems:
        render_empty_state(
            "Silent Catalog",
            f"No underground gems found for @{username}.",
            hint="Try a different creator, or check the exact spelling of the handle.",
        )
        input("\nPress Enter to return...")
        return
    browse_gems(gems, subtitle="AUTHOR ARCHAEOLOGY • PORTFOLIO BOARD")

def interactive_lucky() -> None:
    console.clear()
    print_banner(subtitle="FEELING LUCKY • INSTANT MYTHIC SLEEPER")
    with radar_pulse("Summoning top-tier handcrafted mythic sleeper"):
        try:
            gems = inspector.search_radar(min_stars=2, max_stars=6, limit=6)
        except Exception as e:
            styled_error("Failed to summon lucky gem", str(e))
            input("\nPress Enter to return...")
            return

    if gems:
        _prompt_gem_actions([gems[0]], 0)
    else:
        styled_error("Could not find a lucky gem right now.")
        input("\nPress Enter to return...")

def interactive_vault() -> None:
    t = get_theme()
    console.clear()
    print_banner(subtitle="THE VAULT • YOUR 'I WAS HERE FIRST' PORTFOLIO")

    gems = vault.list_gems()
    rank, rank_desc = vault.get_curator_rank()

    console.print(styled_panel(
        f"[bold {t['accent']}]Curator Rank:[/] [{t['gold']} bold]{rank}[/]\n"
        f"[{t['cream']}]{rank_desc}[/]\n"
        f"[{t['muted']}]Total Saved:[/] [{t['cream']}]{len(gems)} underground gems[/]",
        title="PORTFOLIO TELEMETRY"
    ))
    console.print()

    if not gems:
        console.print(f"[{cream()}]Your Vault is currently empty! Use /radar or /fresh to discover gems and press [s] to save.[/]\n")
        input("Press Enter to return...")
        return

    table = Table(
        box=box.ROUNDED,
        border_style=t["border"],
        expand=False,
        width=get_layout_width(),
        header_style=f"bold {accent()}",
    )
    table.add_column("Repository", style=f"bold {t['cream']}")
    table.add_column("Discovered ⭐", style=t["muted"])
    table.add_column("Current ⭐", style=t["gold"])
    table.add_column("Alpha Gain", style=f"bold {accent()}")
    table.add_column("Tags", style=t["cream"])
    table.add_column("Notes", style=t["muted"])

    for g in gems:
        delta = g["last_checked_stars"] - g["discovered_stars"]
        delta_str = f"▲ +{delta}" if delta >= 0 else f"▼ {delta}"
        tags_str = ", ".join(g.get("tags", [])) if g.get("tags") else "-"
        notes_str = (g.get("notes") or "")[:24]
        table.add_row(
            g["full_name"],
            str(g["discovered_stars"]),
            str(g["last_checked_stars"]),
            delta_str,
            tags_str,
            notes_str,
        )

    console.print(Align.center(table))
    console.print()

    action = select_menu(
        choices=[
            command_choice("refresh", "Ping GitHub for fresh live star counts", "refresh"),
            command_choice("export_md", "Export portfolio to Markdown file", "export_md"),
            command_choice("export_json", "Export portfolio to JSON file", "export_json"),
            command_choice("back", "Return to main palette", "back"),
        ],
    )

    if action == "refresh":
        with radar_pulse("Refreshing star counts from GitHub"):
            vault.refresh_vault(inspector.client)
        interactive_vault()
    elif action == "export_md":
        out_path = Path.cwd() / "gitsolve_portfolio.md"
        vault.export_markdown(out_path)
        styled_success(f"Exported portfolio to {out_path.name}!")
        input("\nPress Enter to return...")
    elif action == "export_json":
        out_path = Path.cwd() / "gitsolve_portfolio.json"
        vault.export_json(out_path)
        styled_success(f"Exported portfolio to {out_path.name}!")
        input("\nPress Enter to return...")

def interactive_theme() -> None:
    console.clear()
    print_banner(subtitle="THEME GALLERY • LIVE IRL™ PREVIEW")
    cfg = load_config()
    current_theme = cfg.get("theme", "warm_earth")
    render_theme_gallery(current_theme)

    choices = [
        questionary.Choice(f"{v['name']} {'(Active)' if k == current_theme else ''}", value=k)
        for k, v in THEMES.items()
    ]
    choices.append(questionary.Choice("Back", value="back"))

    selected = questionary.select("Select visual skin:", choices=choices, style=menu_style()).ask()
    if selected and selected != "back":
        t = THEMES.get(selected, THEMES["warm_earth"])
        update_config_value("theme", selected)
        styled_success(f"Switched skin to {t['name']}! ✦")
        input("\nPress Enter to preview the gallery again...")
        interactive_theme()

def interactive_config() -> None:
    console.clear()
    print_banner(subtitle="CONFIGURATION • SYSTEM SETTINGS")
    cfg = load_config()

    user_name = cfg.get("user_name") or "Explorer"
    pronouns = cfg.get("pronouns", "")
    id_label = f"{user_name} ({pronouns})" if pronouns else user_name
    mascot_key = cfg.get("mascot", "hoodie")
    mascot_name = MASCOTS.get(mascot_key, {}).get("name", "Companion")
    curator_title = cfg.get("curator_title", "Sleeper Hunter")
    scale_label = {
        "ultra": "Ultra HD (20 lines)",
        "high": "High-Res (16 lines)",
        "normal": "Compact (12 lines)",
    }.get(cfg.get("mascot_scale", "high"), "High-Res (16 lines)")

    action = questionary.select(
        "Choose setting to configure:",
        choices=[
            questionary.Choice(f"Explorer Identity (Currently: {id_label})", value="identity"),
            questionary.Choice(f"Companion Mascot (Currently: {mascot_name})", value="mascot"),
            questionary.Choice(f"Mascot Detail & Scale (Currently: {scale_label})", value="scale"),
            questionary.Choice(f"Curator Archetype (Currently: {curator_title})", value="archetype"),
            questionary.Choice("Set GitHub Personal Access Token (Unlocks 5,000 req/hr)", value="token"),
            questionary.Choice(f"Toggle Icon Mode (Currently: {cfg.get('icons_mode', 'auto')})", value="icons"),
            questionary.Choice(f"Default Language Filter (Currently: '{cfg.get('default_language', '') or 'Any'}')", value="lang"),
            questionary.Choice("Re-run Onboarding Ceremony", value="re_onboard"),
            questionary.Choice("Back", value="back"),
        ],
        style=menu_style(),
    ).ask()

    if action == "identity":
        new_name = questionary.text(
            "Enter your callsign / handle:",
            default=cfg.get("user_name") or getpass.getuser(),
            style=menu_style(),
        ).ask()
        if new_name is not None:
            update_config_value("user_name", new_name.strip())

        pronoun_action = questionary.select(
            "Select your preferred pronouns:",
            choices=[
                questionary.Choice("she / her", value="she/her"),
                questionary.Choice("he / him", value="he/him"),
                questionary.Choice("they / them", value="they/them"),
                questionary.Choice("she / they", value="she/they"),
                questionary.Choice("he / they", value="he/they"),
                questionary.Choice("any / all", value="any/all"),
                questionary.Choice("Custom / Write-in...", value="custom"),
                questionary.Choice("Skip (none)", value=""),
            ],
            style=menu_style(),
        ).ask()
        if pronoun_action == "custom":
            custom_p = questionary.text("Enter your pronouns:", style=menu_style()).ask()
            update_config_value("pronouns", custom_p.strip() if custom_p else "")
        elif pronoun_action is not None:
            update_config_value("pronouns", pronoun_action)
        styled_success("Explorer identity updated successfully!")

    elif action == "mascot":
        mascot_choices = [
            questionary.Choice("🌸 Hoodie Wink       — Menhera-chan winking & sparkling stars", value="hoodie"),
            questionary.Choice("💖 Zero Two Darling  — Zero Two smiling, sweet leaning gaze", value="zerotwo_lean"),
            questionary.Choice("✨ Zero Two Stargaze — Zero Two reaching out into the cosmos", value="zerotwo_reach"),
            questionary.Choice("🔮 Rikka Wicked Eye  — Chunibyo dark flame master & wicked eye", value="rikka"),
            questionary.Choice("🎀 Desk Peeker       — Cute anime girl peeking over terminal edge", value="peeker"),
            questionary.Choice("⚡ Pikachu Spark     — Electric companion cheering your code discoveries", value="pikachu"),
            questionary.Choice("🌟 Cheer Chibi       — Energetic cheerleader celebrating every gem found", value="cheer"),
            questionary.Choice("👁️  Manga Glance      — Aesthetic retro manga eye peeker", value="eyes"),
            questionary.Choice("🍃 Emerald Aoko      — Emerald-haired cyber anime girl", value="emerald"),
            questionary.Choice("⚔️  Katana Blade      — Samurai anime warrior with drawn blade", value="katana"),
            questionary.Choice("💎 Cyber Diamond     — Vector mecha diamond prism emblem", value="logo"),
            questionary.Choice("✦  Celestial Prism   — Minimalist procedural ASCII/ANSI crystal", value="crystal"),
        ]
        chosen = questionary.select("Select your Radar Companion Mascot:", choices=mascot_choices, style=menu_style()).ask()
        if chosen:
            update_config_value("mascot", chosen)
            styled_success(f"Companion mascot set to {MASCOTS[chosen]['name']}!")

    elif action == "scale":
        scale_action = questionary.select(
            "Select Mascot Graphic Resolution & Scaling:",
            choices=[
                questionary.Choice("High-Res (16 lines - Crisp, detailed anime facial features) [Default]", value="high"),
                questionary.Choice("Ultra HD (20 lines - Maximum size & highest pixel density)", value="ultra"),
                questionary.Choice("Compact (12 lines - Low-profile retro aesthetic)", value="normal"),
            ],
            style=menu_style(),
        ).ask()
        if scale_action:
            update_config_value("mascot_scale", scale_action)
            styled_success("Mascot resolution updated successfully!")

    elif action == "archetype":
        arch_action = questionary.select(
            "Choose your Curator Archetype:",
            choices=[
                questionary.Choice("Sleeper Hunter     — Tracking 2-7 star hidden gems before the crowd", value="Sleeper Hunter"),
                questionary.Choice("Binary Alchemist   — Extracting pure architectural signal from raw code", value="Binary Alchemist"),
                questionary.Choice("Code Craftsman     — Seeking zero-dependency, pure handcrafted repos", value="Code Craftsman"),
                questionary.Choice("Underground Scout  — Excavating forgotten repositories & underground tools", value="Underground Scout"),
                questionary.Choice("Custom Archetype...", value="custom"),
            ],
            style=menu_style(),
        ).ask()
        if arch_action == "custom":
            custom_a = questionary.text("Enter your custom Archetype title:", style=menu_style()).ask()
            if custom_a:
                update_config_value("curator_title", custom_a.strip())
                styled_success(f"Archetype set to {custom_a.strip()}!")
        elif arch_action:
            update_config_value("curator_title", arch_action)
            styled_success(f"Archetype set to {arch_action}!")

    elif action == "re_onboard":
        run_onboarding_ceremony()
        return

    elif action == "token":
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

def interactive_ask() -> None:
    console.clear()
    print_banner(subtitle="AI FORENSICS • POWERED BY POLLINATIONS.AI")
    repo_input = questionary.text("Enter GitHub repo (owner/repo):", style=menu_style()).ask()
    if not repo_input:
        return
    question = questionary.text("Specific question (leave blank for deep architectural verdict):", style=menu_style()).ask()
    try:
        gem = inspector.xray_repo(repo_input.strip())
        if "readme" not in gem:
            try:
                gem["readme"] = inspector.get_readme(gem["full_name"]) or ""
            except Exception:
                pass
        if question and question.strip():
            with neural_pulse(f"Querying Pollinations AI for {repo_input}"):
                ans = ai_client.ask_repo(gem, question.strip())
            console.print(f"[bold {accent()}]Question:[/] [{cream()}]{question}[/]\n")
            render_ai_teardown(ans, repo_input)
        else:
            with neural_pulse(f"Synthesizing deep AI verdict for {repo_input} (Pollinations AI)"):
                ans = ai_client.explain_repo(gem, readme_snippet=gem.get("readme", ""))
            render_ai_teardown(ans, repo_input)
    except Exception as e:
        styled_error(f"Failed to query {repo_input}", str(e))
    input("\nPress Enter to return...")

def interactive_limits() -> None:
    console.clear()
    print_banner(subtitle="API TELEMETRY • RATE LIMIT QUOTA HEALTH")
    with radar_pulse("Interrogating GitHub API rate limit status"):
        try:
            info = inspector.client.get_rate_limit()
        except Exception as e:
            styled_error("Failed to query rate limits", str(e))
            input("\nPress Enter to return...")
            return
    render_rate_limit_table(info)
    input("Press Enter to return to palette...")

def interactive_velocity() -> None:
    console.clear()
    print_banner(subtitle="SLEEPER VELOCITY • HIGH SURGE UNDERGROUND CODE")
    lang = questionary.text("Language filter (leave empty for all):", style=menu_style()).ask()
    with radar_pulse("Scanning 7-day commit velocity & sleeper acceleration"):
        try:
            gems = inspector.search_velocity(language=lang or "", limit=8)
        except Exception as e:
            styled_error("Velocity scan failed", str(e))
            input("\nPress Enter to return...")
            return

    if not gems:
        render_empty_state(
            "Radar Silence",
            "No high-velocity underground gems found for that filter.",
            hint="Velocity needs the last 7 days — try again tomorrow or widen the language.",
        )
        input("\nPress Enter to return...")
        return
    browse_gems(gems, subtitle="SLEEPER VELOCITY • SURGE BOARD")

# --- Main Command Palette Loop ----------------------------------------------
def run_command_palette() -> None:
    if is_onboarding_needed():
        run_onboarding_ceremony()
    while True:
        console.clear()
        print_header(title="COMMAND PALETTE", status_text="Ready")

        action = select_menu(
            choices=[
                command_choice("radar", "Scan underground repos with presets & filters", "radar", icon("radar")),
                command_choice("fresh", "Stream active repos updated in the last 48 hours", "fresh", icon("fresh")),
                command_choice("velocity", "Detect underground momentum & surging sleepers", "velocity", icon("velocity")),
                command_choice("ai", "Deep architectural synthesis via Pollinations AI", "ai", icon("ai")),
                command_choice("xray", "Deep forensic inspection of ANY repo URL", "xray", icon("xray")),
                command_choice("forks", "Scan for active & valuable community forks", "forks", icon("forks")),
                command_choice("compare", "Head-to-head sleeper showdown between 2 repos", "compare", icon("compare")),
                command_choice("author", "Mine underground gems by a specific solo dev", "author", icon("author")),
                command_choice("lucky", "Instant random mythic sleeper", "lucky", icon("lucky")),
                command_choice("vault", "View your 'I Was Here First' portfolio & star gains", "vault", icon("vault")),
                command_choice("limits", "Check GitHub API rate limit & quota health", "limits", icon("limits")),
                command_choice("theme", "Switch IRL visual theme (Clay, Peach, Moss, Night)", "theme", icon("theme")),
                command_choice("config", "GitHub token & system preferences", "config", icon("config")),
                command_choice("exit", "Leave gitSOLVE", "exit", icon("cross")),
            ],
            instruction="(↑/↓ to move • enter to select • / to filter)",
        )

        if action is None or action == "exit":
            console.print(f"\n[{accent()}]✦ Safe travels. Keep building real things. ✦[/]\n")
            break
        elif action == "radar":
            interactive_radar()
        elif action == "fresh":
            interactive_fresh()
        elif action == "velocity":
            interactive_velocity()
        elif action == "ai" or action == "ask":
            interactive_ask()
        elif action == "xray":
            interactive_xray()
        elif action == "forks":
            interactive_forks()
        elif action == "compare":
            interactive_compare()
        elif action == "author":
            interactive_author()
        elif action == "lucky":
            interactive_lucky()
        elif action == "vault":
            interactive_vault()
        elif action == "limits":
            interactive_limits()
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
    preset: str = typer.Option("", "--preset", "-p", help="Ecosystem preset (rust, python, go, c, typescript, security, cli)"),
    stars: str = typer.Option("2..7", "--stars", "-s", help="Stars range (e.g. 2..7)"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems to inspect"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Scan underground repos with precision filters."""
    min_s, max_s = 2, 7
    if ".." in stars:
        parts = stars.split("..")
        try:
            min_s, max_s = int(parts[0]), int(parts[1])
        except Exception:
            pass

    presets_map = {
        "rust": ("system", "rust"),
        "python": ("compiler", "python"),
        "go": ("cli", "go"),
        "c": ("performance", "c"),
        "typescript": ("wasm", "typescript"),
        "security": ("security", ""),
        "cli": ("tui", ""),
    }
    if preset and preset.lower() in presets_map:
        p_topic, p_lang = presets_map[preset.lower()]
        if not topic and p_topic:
            topic = p_topic
        if not lang and p_lang:
            lang = p_lang

    try:
        if json_out:
            gems = inspector.search_radar(
                topic=topic,
                language=lang,
                query_text=query,
                min_stars=min_s,
                max_stars=max_s,
                limit=limit,
            )
            print(json.dumps(gems, indent=2, default=str))
            raise typer.Exit(0)

        with radar_pulse("Spinning radar array"):
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
        browse_gems(gems)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Radar failed", str(e))

@app.command("xray")
def cmd_xray(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo)"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Deep forensic X-ray inspection of a specific repo."""
    try:
        if json_out:
            gem = inspector.xray_repo(repo)
            print(json.dumps(gem, indent=2, default=str))
            raise typer.Exit(0)

        _run_xray(repo)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("X-Ray failed", str(e))

@app.command("forks")
def cmd_forks(
    repo: str = typer.Argument(..., help="Target GitHub repo name (owner/repo)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of forks to inspect"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Scan for active and diverged community forks."""
    try:
        if json_out:
            forks = inspector.search_forks(repo, limit=limit)
            print(json.dumps(forks, indent=2, default=str))
            raise typer.Exit(0)

        _run_forks(repo)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Forks scan failed", str(e))

@app.command("vault")
def cmd_vault(
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Refresh star counts from GitHub"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: View your saved gem portfolio."""
    if refresh:
        with radar_pulse("Refreshing star counts"):
            vault.refresh_vault(inspector.client)
    if json_out:
        gems = vault.list_gems()
        print(json.dumps(gems, indent=2, default=str))
        raise typer.Exit(0)
    interactive_vault()

@app.command("fresh")
def cmd_fresh(
    lang: str = typer.Option("", "--lang", "-l", help="Language filter"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems to inspect"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Stream active repos updated in the last 48 hours."""
    try:
        if json_out:
            gems = inspector.search_fresh(language=lang, limit=limit)
            print(json.dumps(gems, indent=2, default=str))
            raise typer.Exit(0)

        with radar_pulse("Scanning live commits in the last 48 hours"):
            gems = inspector.search_fresh(language=lang, limit=limit)
        if not gems:
            styled_error("No fresh active sleepers found in the last 48 hours.")
            return
        browse_gems(gems)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Fresh scan failed", str(e))

@app.command("compare")
def cmd_compare(
    repo1: str = typer.Argument(..., help="First repo (owner/repo)"),
    repo2: str = typer.Argument(..., help="Second repo (owner/repo)"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Compare two repos side-by-side."""
    try:
        if json_out:
            comp = inspector.compare_repos(repo1, repo2)
            print(json.dumps(comp, indent=2, default=str))
            raise typer.Exit(0)

        t = get_theme()
        with radar_pulse("Running dual X-Ray telemetry"):
            g1 = inspector.xray_repo(repo1)
            g2 = inspector.xray_repo(repo2)

        table = Table(box=box.ROUNDED, border_style=t["border"], expand=False, width=get_layout_width(), header_style=f"bold {accent()}")
        table.add_column("Diagnostic Telemetry", style=f"bold {t['muted']}")
        table.add_column(g1["full_name"], style=t["cream"])
        table.add_column(g2["full_name"], style=t["cream"])

        table.add_row("Overall Rating", f"[{t['gold']} bold]{g1.get('overall_score', 80)} / 100[/]", f"[{t['gold']} bold]{g2.get('overall_score', 80)} / 100[/]")
        table.add_row("Repository Health", render_meter(g1.get("health_score", 75), 100, width=8, fill_color="#68D391"), render_meter(g2.get("health_score", 75), 100, width=8, fill_color="#68D391"))
        table.add_row("Discovery Potential", render_meter(g1.get("discovery_score", 85), 100, width=8, fill_color=accent()), render_meter(g2.get("discovery_score", 85), 100, width=8, fill_color=accent()))
        table.add_row("Stars & Forks", f"⭐ {g1['stars']} • 🍴 {g1.get('forks', 0)}", f"⭐ {g2['stars']} • 🍴 {g2.get('forks', 0)}")
        table.add_row("Language", g1.get("primary_language", "Code"), g2.get("primary_language", "Code"))
        table.add_row("Age", g1.get("age_text", "Unknown"), g2.get("age_text", "Unknown"))
        table.add_row("Tests", "✓ Present" if g1.get("has_tests") else "✗ Missing", "✓ Present" if g2.get("has_tests") else "✗ Missing")
        table.add_row("CI/CD", "✓ Configured" if g1.get("has_ci") else "✗ Missing", "✓ Configured" if g2.get("has_ci") else "✗ Missing")
        table.add_row("Estimated LoC", f"~{g1.get('loc_estimate', 0):,}", f"~{g2.get('loc_estimate', 0):,}")

        console.print()
        console.print(table)
        console.print()
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Compare failed", str(e))

@app.command("author")
def cmd_author(
    username: str = typer.Argument(..., help="GitHub username to inspect"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of gems"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Mine underground gems by a specific solo dev."""
    try:
        if json_out:
            gems = inspector.author_gems(username, limit=limit)
            print(json.dumps(gems, indent=2, default=str))
            raise typer.Exit(0)

        with radar_pulse(f"Excavating catalog of @{username}"):
            gems = inspector.author_gems(username, limit=limit)
        if not gems:
            styled_error(f"No underground gems found for @{username}.")
            return
        browse_gems(gems)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Author search failed", str(e))

@app.command("lucky")
def cmd_lucky(
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Instant random mythic sleeper."""
    try:
        if json_out:
            gems = inspector.search_radar(min_stars=2, max_stars=6, limit=1)
            print(json.dumps(gems[0] if gems else {}, indent=2, default=str))
            raise typer.Exit(0)

        interactive_lucky()
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Lucky failed", str(e))

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

@app.command("ask")
def cmd_ask(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo or URL)"),
    question: Optional[str] = typer.Option(None, "--question", "-q", help="Specific technical question to ask"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Ask Pollinations AI for deep architectural verdict or answers about any repo."""
    try:
        gem = inspector.xray_repo(repo)
        if "readme" not in gem:
            try:
                gem["readme"] = inspector.get_readme(gem["full_name"]) or ""
            except Exception:
                pass
        if question:
            with neural_pulse(f"Querying Pollinations AI for {repo}"):
                ans = ai_client.ask_repo(gem, question)
            if json_out:
                print(json.dumps({"repo": repo, "question": question, "answer": ans}, indent=2))
                raise typer.Exit(0)
            console.print(f"[bold {accent()}]Question:[/] [{cream()}]{question}[/]\n")
            render_ai_teardown(ans, repo)
        else:
            with neural_pulse(f"Synthesizing deep AI verdict for {repo} (Pollinations AI)"):
                v = ai_client.generate_deep_verdict(gem, readme_snippet=gem.get("readme", ""))
            if json_out:
                print(json.dumps({"repo": repo, "ai_verdict": v}, indent=2))
                raise typer.Exit(0)
            summary_text = ai_client.explain_repo(gem, readme_snippet=gem.get("readme", ""))
            render_ai_teardown(summary_text, repo)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("AI query failed", str(e))

@app.command("ai")
def cmd_ai(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo or URL)"),
    question: Optional[str] = typer.Option(None, "--question", "-q", help="Specific technical question to ask"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI alias: Deep AI codebase analysis powered by Pollinations AI."""
    cmd_ask(repo=repo, question=question, json_out=json_out)

@app.command("velocity")
def cmd_velocity(
    lang: str = typer.Option("", "--lang", "-l", help="Language filter"),
    limit: int = typer.Option(8, "--limit", "-n", help="Number of surging sleepers"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Detect underground momentum & surging sleepers."""
    try:
        if json_out:
            gems = inspector.search_velocity(language=lang, limit=limit)
            print(json.dumps(gems, indent=2, default=str))
            raise typer.Exit(0)

        with radar_pulse("Scanning 7-day commit velocity & sleeper acceleration"):
            gems = inspector.search_velocity(language=lang, limit=limit)
        if not gems:
            styled_error("No high-velocity underground gems found for that filter.")
            return
        browse_gems(gems)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Velocity scan failed", str(e))

@app.command("limits")
def cmd_limits(
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Check GitHub API rate limit & quota health."""
    try:
        info = inspector.client.get_rate_limit()
        if json_out:
            print(json.dumps(info, indent=2, default=str))
            raise typer.Exit(0)
        render_rate_limit_table(info)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Limits check failed", str(e))

@app.command("readme")
def cmd_readme(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo or URL)"),
):
    """Direct CLI: View repository README directly rendered in the terminal."""
    try:
        with radar_pulse(f"Fetching README for {repo}"):
            content = inspector.get_readme(repo)
        if not content:
            styled_error(
                f"No README documentation found or accessible for {repo}.",
                hint="Verify that the repository is public and contains a standard README file (Markdown/RST/plain text)."
            )
            return
        render_markdown_viewer(repo, content)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("README fetch failed", str(e))

@app.command("tree")
def cmd_tree(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo)"),
    limit: int = typer.Option(40, "--limit", "-n", help="Max files/directories to inspect"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: View repository file tree architecture."""
    try:
        with radar_pulse(f"Fetching file hierarchy for {repo}"):
            items = inspector.get_tree_structure(repo, max_items=limit)
        if json_out:
            print(json.dumps(items, indent=2))
            raise typer.Exit(0)
        if not items:
            styled_error(f"Could not retrieve file hierarchy for {repo}.")
            return
        render_tree_viewer(repo, items)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Tree fetch failed", str(e))

@app.command("commits")
def cmd_commits(
    repo: str = typer.Argument(..., help="GitHub repo name (owner/repo)"),
    limit: int = typer.Option(6, "--limit", "-n", help="Number of recent commits"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Direct CLI: Inspect recent commits & craftsmanship."""
    try:
        with radar_pulse(f"Fetching commit stream for {repo}"):
            commits = inspector.get_recent_commits(repo, limit=limit)
            cadence = inspector.get_commit_cadence(repo)
        if json_out:
            print(json.dumps({"commits": commits, "cadence": cadence}, indent=2))
            raise typer.Exit(0)
        if not commits:
            styled_error(f"Could not retrieve recent commits for {repo}.")
            return
        render_commits_viewer(repo, commits, cadence=cadence)
    except typer.Exit:
        raise
    except Exception as e:
        styled_error("Commits fetch failed", str(e))

@app.command("export")
def cmd_export(
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: markdown or json"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Target output file path"),
):
    """Direct CLI: Export your Vault portfolio to Markdown or JSON."""
    try:
        if format.lower() in ("json", "js"):
            target = Path(output) if output else Path.cwd() / "gitsolve_portfolio.json"
            vault.export_json(target)
            styled_success(f"Vault portfolio exported to JSON: {target.resolve()}")
        else:
            target = Path(output) if output else Path.cwd() / "gitsolve_portfolio.md"
            vault.export_markdown(target)
            styled_success(f"Vault portfolio exported to Markdown: {target.resolve()}")
    except Exception as e:
        styled_error("Export failed", str(e))

@app.command("presets")
def cmd_presets():
    """Direct CLI: List curated ecosystem presets for underground discovery."""
    t = get_theme()
    w = get_layout_width()
    table = Table(box=box.ROUNDED, border_style=t["border"], expand=True, width=w)
    table.add_column("Preset", style=f"bold {t['accent']}")
    table.add_column("Focus", style=t["gold"])
    table.add_column("Filters Applied", style=t["cream"])

    presets_info = [
        ("rust", "Rust Systems Alpha", "language:rust topic:system stars:2..7"),
        ("python", "Python Deep-Tech Compilers", "language:python topic:compiler stars:2..7"),
        ("go", "Go Systems & Handcrafted CLI", "language:go topic:cli stars:2..7"),
        ("c", "C/C++ Low-Latency & Performance", "language:c topic:performance stars:2..7"),
        ("typescript", "TypeScript & WebAssembly", "language:typescript topic:wasm stars:2..7"),
        ("security", "Underground Security & Cryptography", "topic:security stars:2..7"),
        ("cli", "Terminal Handcrafted TUIs & Tools", "topic:tui stars:2..7"),
    ]
    for name, focus, filters in presets_info:
        table.add_row(name, focus, filters)

    panel = Panel(
        table,
        title=f"[bold {t['accent']}] ✦ CURATED ECOSYSTEM PRESETS ✦ [/]",
        subtitle="[dim]Run: gitsolve radar --preset <name>[/dim]",
        box=box.ROUNDED,
        border_style=t["border"],
        padding=(0, 1),
        width=w,
    )
    console.print()
    console.print(panel)
    console.print()

@app.command("version")
def cmd_version():
    """Print gitSOLVE version."""
    console.print(f"[bold {accent()}]gitSOLVE[/] [{cream()}]v{__version__}[/]")

def main():
    app()

if __name__ == "__main__":
    main()
