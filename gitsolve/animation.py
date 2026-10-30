# gitSOLVE ✦ Charm & Lip Gloss Style Live Animations & Visual Gauges
# Underground Code. Zero Hype. Handcrafted Gems.

import math
import os
import random
import sys
import time
import threading
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from gitsolve.tokens import (
    THEMES,
    get_current_theme,
    role,
    gradient_text,
)

console = Console(highlight=False)

# --- Short Scan Stage Checklist (pursued inside the radar scope) --------------
SCAN_STAGES = [
    "Antenna sweep & search synthesis",
    "Language byte census",
    "File tree reconnaissance",
    "CI & test verification",
    "Commit forensics & cadence",
    "Explainable scoring & ranking",
]

# --- 2D Rotating Radar Scope Frames (Braille & ASCII) ------------------------
BRAILLE_RADAR_SCOPES = [
    # 000° North
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁     ⡇     ⠈⢆ ",
        "⡐       ⡇  ✦    ⢢",
        " ⢣      ⡇      ⡜ ",
        "  ⠑⠤⣀⡀   ⡇   ⢀⣀⠤⠊  ",
    ],
    # 030° North-North-East
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁    ⢀⠇     ⠈⢆ ",
        "⡐      ⡠⠁   ✦   ⢢",
        " ⢣    ⡠⠁        ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 060° East-North-East
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁   ⢀⠤⠒⠉    ⠈⢆ ",
        "⡐    ⠤⠊       ✦  ⢢",
        " ⢣             ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 090° East
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐     ───────✦─  ⢢",
        " ⢣             ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 120° East-South-East
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐    ⠤⣀       ✦  ⢢",
        " ⢣   ⠈⠢⠤⣀     ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 150° South-South-East
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐      ⠢⡀   ✦   ⢢",
        " ⢣    ⢀⠜       ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 180° South
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁      ✦      ⠈⢆ ",
        "⡐       ⡇       ⢢",
        " ⢣      ⡇      ⡜ ",
        "  ⠑⠤⣀⡀   ⡇   ⢀⣀⠤⠊  ",
    ],
    # 210° South-South-West
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐   ✦   ⡠⠊       ⢢",
        " ⢣     ⠱⡀        ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 240° West-South-West
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐  ✦ ⣀⠤⠊         ⢢",
        " ⢣   ⠉⠒⠤⡀     ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 270° West
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁             ⠈⢆ ",
        "⡐  ─✦───────     ⢢",
        " ⢣             ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 300° West-North-West
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁   ⠉⠒⠤⣀     ⠈⢆ ",
        "⡐  ✦ ⠒⠤⣀         ⢢",
        " ⢣             ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
    # 330° North-North-West
    [
        "  ⢀⡠⠔⠊⠉⠉⠉⠑⠢⢄⡀  ",
        " ⡰⠁ ⠈⠢⡀         ⠈⢆ ",
        "⡐     ⠈⠢⡀   ✦   ⢢",
        " ⢣             ⡜ ",
        "  ⠑⠤⣀⡀      ⢀⣀⠤⠊  ",
    ],
]

BRAILLE_NEURAL_SCOPES = [
    [
        "  ⢀⠔⠊⠉⠉⠉⠑⠢⡀  ",
        " ⡰⠃  ⢀⡠⠔⠢⢄  ⠈⢆ ",
        "⡐   ⡰⠁ ✦  ⠈⢆   ⢢",
        " ⢣   ⠈⠢⠤⠔⠊   ⡜ ",
        "  ⠑⠤⣀⡀   ⢀⣀⠤⠊  ",
    ],
    [
        "  ⢀⠔⠊⠉⠉⠉⠑⠢⡀  ",
        " ⡰⠃  ⢀⣀⠤⣀   ⠈⢆ ",
        "⡐   ⡐  ✦  ⢢   ⢢",
        " ⢣   ⠑⠢⠤⠊   ⡜ ",
        "  ⠑⠤⣀⡀   ⢀⣀⠤⠊  ",
    ],
    [
        "  ⢀⠔⠊⠉⠉⠉⠑⠢⡀  ",
        " ⡰⠃   ⡠⠔⠒⢄  ⠈⢆ ",
        "⡐    ⠱⡀ ✦ ⡰   ⢢",
        " ⢣    ⠈⠉⠁    ⡜ ",
        "  ⠑⠤⣀⡀   ⢀⣀⠤⠊  ",
    ],
    [
        "  ⢀⠔⠊⠉⠉⠉⠑⠢⡀  ",
        " ⡰⠃  ⠤⠤⠤⠤  ⠈⢆ ",
        "⡐    ⠠ ✦ ⠄    ⢢",
        " ⢣   ⠒⠒⠒⠒   ⡜ ",
        "  ⠑⠤⣀⡀   ⢀⣀⠤⠊  ",
    ],
]

BEARINGS = [
    "000° N   • POLAR SECTOR",
    "030° NNE • ALPHA STRATA",
    "060° ENE • SYNTHESIS GRID",
    "090° E   • AST HORIZON",
    "120° ESE • LATENCY STRIP",
    "150° SSE • COMMIT CORE",
    "180° S   • DEEP ARCHIVES",
    "210° SSW • SHANNON ENTROPY",
    "240° WSW • CODE CAVERN",
    "270° W   • UNDERGROUND",
    "300° WNW • LONE WOLF ALPHA",
    "330° NNW • HANDCRAFTED",
]

EQUALIZER_CHARS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
SPARKLE_FRAMES = ["✦", "✧", "⋆", "｡", "°", "✵", "✶", "★"]

SCAN_HINTS = [
    "Interrogating AST, commit velocity, and test manifests...",
    "Filtering corporate hype & automated template forks...",
    "Sifting handcrafted gems & calculating Shannon health scores...",
    "Evaluating repository originality & dependency clarity...",
    "Running NFKC unicode normalizer & security sanitizers...",
    "Extracting language byte distribution from raw tree...",
]

AI_SYNTH_HINTS = [
    "Interrogating Pollinations AI neural synthesis engine...",
    "Decoding architectural trade-offs & underground design edge...",
    "Evaluating solo-maintainer craftsmanship vs corporate bloat...",
    "Generating 4-part forensic verdict: verdict, why_good, edge, caveats...",
    "Cross-referencing AST density and commit semantics...",
]

# --- Gauges & Metric Visualizers --------------------------------------------
def render_meter(
    score: int,
    max_val: int = 100,
    width: int = 12,
    fill_color: str = "#F29265",
    empty_color: str = "#3A2619",
    show_score: bool = True,
) -> str:
    """Renders a Charm-style solid block meter (e.g. ▰▰▰▰▰▰▰▱▱▱ 74/100)."""
    clamped = max(0, min(score, max_val))
    filled_len = int((clamped / max_val) * width) if max_val > 0 else 0
    empty_len = width - filled_len
    filled_str = "▰" * filled_len
    empty_str = "▱" * empty_len
    res = f"[{fill_color}]{filled_str}[/][{empty_color}]{empty_str}[/]"
    if show_score:
        res += f" [{fill_color} bold]{clamped}[/][{empty_color}]/{max_val}[/]"
    return res

def render_sparkline(values: List[int]) -> str:
    """Renders a Unicode sparkline ( ▂▃▄▅▆▇█) from numeric data points."""
    if not values:
        return ""
    bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    min_v = min(values)
    max_v = max(values)
    span = max_v - min_v
    if span == 0:
        return bars[3] * len(values)

    spark = []
    for v in values:
        idx = int(((v - min_v) / span) * (len(bars) - 1))
        spark.append(bars[idx])
    return "".join(spark)

def render_language_bar(languages: Dict[str, int], width: int = 24) -> str:
    """Renders a proportional multi-color language distribution bar (theme-aware)."""
    if not languages:
        return "[dim]No language breakdown available[/dim]"

    theme = get_current_theme()
    palette = [
        theme["accent"],
        role(theme, "info"),
        role(theme, "success"),
        theme["gold"],
        theme["mythic"],
        role(theme, "warn"),
    ]
    total_bytes = sum(languages.values())
    if total_bytes == 0:
        return "[dim]Empty repository[/dim]"

    segments = []
    text_labels = []
    used_width = 0

    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    for i, (lang_name, b_count) in enumerate(sorted_langs[:4]):
        pct = (b_count / total_bytes)
        seg_w = max(1, int(round(pct * width)))
        used_width += seg_w
        color = palette[i % len(palette)]
        segments.append(f"[{color}]{'█' * seg_w}[/]")
        text_labels.append(f"[{color}]{lang_name} {pct * 100:.0f}%[/]")

    bar_str = "".join(segments)
    labels_str = " • ".join(text_labels)
    return f"{bar_str}  {labels_str}"

def render_pill(text: str, bg_color: str = "#F29265", fg_color: str = "#000000") -> str:
    """Renders a Lip Gloss-style rounded pill badge."""
    return f"[bold {fg_color} on {bg_color}] {text} [/]"

def render_equalizer(step: int, num_bars: int = 8) -> str:
    """Generates an animated dancing telemetry equalizer spectrum with harmonic modulation."""
    bars = []
    for i in range(num_bars):
        primary = math.sin(step * 0.45 + i * 0.75)
        secondary = 0.5 * math.cos(step * 0.25 - i * 0.5)
        val = int(((primary + secondary) / 1.5 + 1.0) * 4.0)
        clamped = max(0, min(8, val))
        bars.append(EQUALIZER_CHARS[clamped])
    return "".join(bars)

# --- Charm 2D Radar Scope Animation Worker ----------------------------------
class _LiveRadarScopeWorker(threading.Thread):
    def __init__(
        self,
        message: str,
        stage_hints: Optional[List[str]] = None,
        accent_color: Optional[str] = None,
        cream_color: Optional[str] = None,
        muted_color: Optional[str] = None,
        stages: Optional[List[str]] = None,
    ):
        super().__init__(daemon=True)
        theme = get_current_theme()
        self.message = message
        self.stage_hints = stage_hints or SCAN_HINTS
        self.stages = stages if stages is not None else SCAN_STAGES
        self.accent = accent_color or theme["accent"]
        self.cream = cream_color or theme["cream"]
        self.muted = muted_color or theme["muted"]
        self.border = theme["border"]
        self.gold = theme["gold"]
        self.success = role(theme, "success")
        self.grad_a = theme.get("grad_a", theme["accent"])
        self.grad_b = theme.get("grad_b", theme["gold"])
        self.stop_event = threading.Event()
        self.start_time = time.time()
        self.frame_idx = 0
        self.prev_levels: List[float] = []
        self.live: Optional[Live] = None

    def _smooth_equalizer(self, num_bars: int = 7) -> List[int]:
        """Harmonic equalizer with exponential smoothing for a silky dance."""
        targets = []
        for i in range(num_bars):
            primary = math.sin(self.frame_idx * 0.42 + i * 0.72)
            secondary = 0.5 * math.cos(self.frame_idx * 0.23 - i * 0.48)
            targets.append(((primary + secondary) / 1.5 + 1.0) / 2.0)
        if len(self.prev_levels) != num_bars:
            self.prev_levels = targets[:]
        for i in range(num_bars):
            self.prev_levels[i] = 0.62 * self.prev_levels[i] + 0.38 * targets[i]
        lo, hi = min(self.prev_levels), max(self.prev_levels)
        span = (hi - lo) or 1.0
        return [7 if (hi - lo) < 0.06 else int((v - lo) / span * 7.999) for v in self.prev_levels]

    def build_frame(self) -> Panel:
        elapsed = time.time() - self.start_time
        frame_mod = self.frame_idx % len(BRAILLE_RADAR_SCOPES)
        scope_lines = BRAILLE_RADAR_SCOPES[frame_mod]
        bearing = BEARINGS[frame_mod]

        # Left Column: The 2D Radar Scope (cleanly built with Text objects)
        scope_text = Text()
        for line in scope_lines:
            parts = line.split("✦")
            if len(parts) == 2:
                scope_text.append(parts[0], style=f"bold {self.accent}")
                scope_text.append("✦", style=f"bold {self.gold}")
                scope_text.append(parts[1] + "\n", style=f"bold {self.accent}")
            else:
                scope_text.append(line + "\n", style=f"bold {self.accent}")

        # Right Column: High-tech Telemetry Stream
        eq_levels = self._smooth_equalizer(num_bars=7)
        equalizer = "".join(EQUALIZER_CHARS[lv] for lv in eq_levels)
        sparkle = SPARKLE_FRAMES[self.frame_idx % len(SPARKLE_FRAMES)]

        # Pulsing radar progress percentage & meter
        pct = min(98, int((elapsed / 2.0) * 100)) % 100
        filled_cnt = int((pct / 100) * 10)
        empty_cnt = 10 - filled_cnt
        meter_markup = f"[{self.accent}]{'▰' * filled_cnt}[/][{self.muted}]{'▱' * empty_cnt}[/]"

        hint_idx = int(elapsed / 1.3) % len(self.stage_hints)
        hint = self.stage_hints[hint_idx]

        # Progressive forensic stage checklist
        stage_done = max(0, min(len(self.stages) - 1, int(elapsed / 1.9)))
        spin = SPARKLE_FRAMES[(self.frame_idx * 2) % len(SPARKLE_FRAMES)]
        checklist = Text()
        stage_lines = []
        for i, stage in enumerate(self.stages):
            if i < stage_done:
                stage_lines.append((f"✓ {stage}", f"{self.success}"))
            elif i == stage_done:
                stage_lines.append((f"{spin} {stage}", f"bold {self.accent}"))
            else:
                stage_lines.append((f"○ {stage}", f"dim {self.muted}"))
        visible = stage_lines[:4]
        for label_txt, style_name in visible:
            checklist.append(f"{label_txt}\n", style=style_name)

        telem_text = Text()
        telem_text.append(f"{sparkle} RADAR SCOPE ACTIVE ", style=f"bold {self.accent}")
        telem_text.append(f"[{bearing}]\n", style=f"bold {self.cream}")
        telem_text.append(f"Target: 2-7★ Sleepers  •  Echo: 14ms  •  ETag: Warm\n", style=f"dim {self.muted}")

        # Use Text.from_markup to properly render colors without leaking markup tags
        eq_markup = f"SPECTRUM: [bold {self.accent}]{equalizer}[/]  {meter_markup} [bold {self.cream}]{pct}%[/] [dim {self.muted}]({elapsed:.1f}s)[/]\n"
        telem_text.append_text(Text.from_markup(eq_markup))
        telem_text.append_text(checklist)
        telem_text.append(f"{hint}", style=f"italic {self.cream}")

        grid = Table(box=None, expand=True, padding=(0, 1), show_header=False)
        grid.add_column("scope", justify="center", width=22, no_wrap=True)
        grid.add_column("telemetry", justify="left", no_wrap=True)
        grid.add_row(scope_text, telem_text)

        scope_title = gradient_text(f" 📡 {self.message.upper()} ", self.grad_a, self.grad_b, bold=True)
        panel = Panel(
            grid,
            title=scope_title,
            box=box.ROUNDED,
            border_style=self.border,
            padding=(0, 1),
            width=min(84, max(56, console.width - 4)),
        )
        return panel

    def run(self):
        try:
            self.live = Live(
                self.build_frame(),
                console=console,
                refresh_per_second=14,
                transient=True,
            )
            self.live.start()
            while not self.stop_event.is_set():
                self.frame_idx += 1
                if self.live:
                    self.live.update(self.build_frame())
                time.sleep(0.07)
        except Exception:
            pass
        finally:
            if self.live:
                try:
                    self.live.stop()
                except Exception:
                    pass

    def stop(self):
        self.stop_event.set()
        self.join(timeout=0.3)
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass

@contextmanager
def radar_pulse(message: str, stage_hints: Optional[List[str]] = None, stages: Optional[List[str]] = None) -> Generator[None, None, None]:
    """Charm-style interactive live radar sweep with 2D animated scope, dancing spectrum,
    progressive stage checklist, and rotating bearing. Runs smoothly in a daemon background thread."""
    theme = get_current_theme()
    if not sys.stdout.isatty() or os.environ.get("CI") or os.environ.get("GITSOLVE_NO_ANIM"):
        with console.status(f"[bold {theme['accent']}]●[/] [bold {theme['cream']}]{message}[/]"):
            yield
        return

    worker = _LiveRadarScopeWorker(message, stage_hints=stage_hints, stages=stages)
    start_time = time.time()
    worker.start()
    try:
        yield
    finally:
        worker.stop()
        elapsed = time.time() - start_time
        console.print(
            f"[bold {theme['accent']}][/]✓ [bold {theme['accent']}]{message} completed[/] [dim {theme['muted']}]({elapsed:.1f}s)[/]"
        )

# --- Charm Live Neural Pulse Animation Worker (Pollinations AI) -------------
class _LiveNeuralWorker(threading.Thread):
    def __init__(
        self,
        message: str,
        stage_hints: Optional[List[str]] = None,
        accent_color: Optional[str] = None,
        gold_color: Optional[str] = None,
        cream_color: Optional[str] = None,
        muted_color: Optional[str] = None,
        stages: Optional[List[str]] = None,
    ):
        super().__init__(daemon=True)
        theme = get_current_theme()
        self.message = message
        self.stage_hints = stage_hints or AI_SYNTH_HINTS
        self.stages = stages if stages is not None else ["Cataloguing evidence", "Reasoning pass", "Synthesis"]
        self.accent = accent_color or role(theme, "info")
        self.gold = gold_color or theme["gold"]
        self.cream = cream_color or theme["cream"]
        self.muted = muted_color or theme["muted"]
        self.border = theme["border"]
        self.grad_a = role(theme, "info")
        self.grad_b = theme["accent"]
        self.stop_event = threading.Event()
        self.start_time = time.time()
        self.frame_idx = 0
        self.prev_levels: List[float] = []
        self.live: Optional[Live] = None

    def _smooth_equalizer(self, num_bars: int = 7) -> List[int]:
        targets = []
        for i in range(num_bars):
            primary = math.sin(self.frame_idx * 0.36 + i * 0.62)
            secondary = 0.5 * math.cos(self.frame_idx * 0.19 - i * 0.51)
            targets.append(((primary + secondary) / 1.5 + 1.0) / 2.0)
        if len(self.prev_levels) != num_bars:
            self.prev_levels = targets[:]
        for i in range(num_bars):
            self.prev_levels[i] = 0.62 * self.prev_levels[i] + 0.38 * targets[i]
        lo, hi = min(self.prev_levels), max(self.prev_levels)
        span = (hi - lo) or 1.0
        return [7 if (hi - lo) < 0.06 else int((v - lo) / span * 7.999) for v in self.prev_levels]

    def build_frame(self) -> Panel:
        elapsed = time.time() - self.start_time
        frame_mod = self.frame_idx % len(BRAILLE_NEURAL_SCOPES)
        scope_lines = BRAILLE_NEURAL_SCOPES[frame_mod]

        scope_text = Text()
        for line in scope_lines:
            parts = line.split("✦")
            if len(parts) == 2:
                scope_text.append(parts[0], style=f"bold {self.accent}")
                scope_text.append("✦", style=f"bold {self.gold}")
                scope_text.append(parts[1] + "\n", style=f"bold {self.accent}")
            else:
                scope_text.append(line + "\n", style=f"bold {self.accent}")

        eq_levels = self._smooth_equalizer(num_bars=7)
        equalizer = "".join(EQUALIZER_CHARS[lv] for lv in eq_levels)
        sparkle = SPARKLE_FRAMES[self.frame_idx % len(SPARKLE_FRAMES)]

        pct = min(98, int((elapsed / 2.5) * 100)) % 100
        filled_cnt = int((pct / 100) * 10)
        empty_cnt = 10 - filled_cnt
        meter_markup = f"[{self.accent}]{'▰' * filled_cnt}[/][{self.muted}]{'▱' * empty_cnt}[/]"

        hint_idx = int(elapsed / 1.2) % len(self.stage_hints)
        hint = self.stage_hints[hint_idx]

        # Reasoning stage checklist
        stage_done = max(0, min(len(self.stages), int(elapsed / 2.4)))
        spin = SPARKLE_FRAMES[(self.frame_idx * 2) % len(SPARKLE_FRAMES)]
        checklist = Text()
        for i, stage in enumerate(self.stages):
            if i < stage_done:
                checklist.append(f"✓ {stage}\n", style=self.gold)
            elif i == stage_done:
                checklist.append(f"{spin} {stage}\n", style=f"bold {self.accent}")
            else:
                checklist.append(f"○ {stage}\n", style=f"dim {self.muted}")

        telem_text = Text()
        telem_text.append(f"{sparkle} POLLINATIONS.AI SYNAPSE ", style=f"bold {self.accent}")
        telem_text.append("• REASONING ENGINE ACTIVE\n", style=f"bold {self.gold}")
        telem_text.append("Provider: pollinations.ai  •  Temperature: 0.2  •  Zero Hype\n", style=f"dim {self.muted}")

        eq_markup = f"SYNAPSE: [bold {self.accent}]{equalizer}[/]  {meter_markup} [bold {self.cream}]{pct}%[/] [dim {self.muted}]({elapsed:.1f}s)[/]\n"
        telem_text.append_text(Text.from_markup(eq_markup))
        telem_text.append_text(checklist)
        telem_text.append(f"{hint}", style=f"italic {self.cream}")

        grid = Table(box=None, expand=True, padding=(0, 1), show_header=False)
        grid.add_column("scope", justify="center", width=22, no_wrap=True)
        grid.add_column("telemetry", justify="left", no_wrap=True)
        grid.add_row(scope_text, telem_text)

        title = gradient_text(f" 🤖 {self.message.upper()} ", self.grad_a, self.grad_b, bold=True)
        panel = Panel(
            grid,
            title=title,
            box=box.ROUNDED,
            border_style=self.border,
            padding=(0, 1),
            width=min(84, max(56, console.width - 4)),
        )
        return panel

    def run(self):
        try:
            self.live = Live(
                self.build_frame(),
                console=console,
                refresh_per_second=14,
                transient=True,
            )
            self.live.start()
            while not self.stop_event.is_set():
                self.frame_idx += 1
                if self.live:
                    self.live.update(self.build_frame())
                time.sleep(0.07)
        except Exception:
            pass
        finally:
            if self.live:
                try:
                    self.live.stop()
                except Exception:
                    pass

    def stop(self):
        self.stop_event.set()
        self.join(timeout=0.3)
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass

@contextmanager
def neural_pulse(message: str, stage_hints: Optional[List[str]] = None, stages: Optional[List[str]] = None) -> Generator[None, None, None]:
    """Charm-style live Pollinations AI neural lattice animation worker."""
    theme = get_current_theme()
    info_c = theme.get("info") or role(theme, "info")
    if not sys.stdout.isatty() or os.environ.get("CI") or os.environ.get("GITSOLVE_NO_ANIM"):
        with console.status(f"[bold {info_c}]●[/] [bold {theme['cream']}]{message}[/]"):
            yield
        return

    worker = _LiveNeuralWorker(message, stage_hints=stage_hints, stages=stages)
    start_time = time.time()
    worker.start()
    try:
        yield
    finally:
        worker.stop()
        elapsed = time.time() - start_time
        console.print(
            f"[bold {info_c}]✓[/] [bold {theme['cream']}]{message} completed[/] [dim {theme['muted']}]({elapsed:.1f}s)[/]"
        )

def animate_stage_transition(stages: List[str], delay_per_stage: float = 0.10) -> None:
    """Simulates a rapid multi-stage forensic scan sequence with clean visual ticks."""
    if not sys.stdout.isatty() or os.environ.get("CI") or os.environ.get("GITSOLVE_NO_ANIM"):
        return
    for stage in stages:
        theme = get_current_theme()
        step_text = Text()
        step_text.append(f"  [bold {theme['accent']}]✓[/] ")
        step_text.append(stage, style=theme["cream"])
        console.print(step_text)
        time.sleep(delay_per_stage)

def render_sonar_sweep(width: int = 40) -> str:
    """Returns a visual sonar acoustic sweep bar."""
    theme = get_current_theme()
    return f"[bold {theme['accent']}]≈≈≈≈ ( • ) ≈≈≈≈[/] [dim {theme['muted']}]{'─' * max(0, width - 16)}[/]"
