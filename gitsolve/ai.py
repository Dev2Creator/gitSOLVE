# gitSOLVE ✦ Pollinations AI Forensic Engine
# Software for Humans. Underground code. Zero hype. Powered by pollinations.ai

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from gitsolve.security import sanitize_terminal_output

POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/"

DEEP_VERDICT_SYSTEM_PROMPT = """You are gitSOLVE's Principal Systems Architect and Forensic Code Auditor.
gitSOLVE identity: UNDERGROUND CODE. ZERO HYPE. HANDCRAFTED GEMS.
Your role: Provide an exhaustive, deeply technical, developer-grade forensic evaluation of a software repository based on its verified signals, README documentation, and implementation metrics.

CRITICAL DIRECTIVES:
- DO NOT write vague, generic 1-2 sentence summaries or surface-level praise.
- DO NOT speak in high-level marketing speak. Dive directly into low-level engineering mechanics, data structures, concurrency, algorithms, and design trade-offs.
- Provide a rigorous, multi-sentence analysis for every section citing concrete design choices.

Format your response strictly as valid raw JSON with exactly these 4 keys:
1. "verdict": Detailed architectural breakdown (4-6 comprehensive sentences). Detail what this codebase builds, how data flows through its internal pipeline, the underlying algorithms/data structures, concurrency/memory strategies, and how it actually executes under the hood.
2. "why_good": Deep engineering craftsmanship analysis (4-6 comprehensive sentences). Analyze the code organization, API elegance, memory safety or zero-cost abstractions, dependency discipline (or zero-dependency purity), test architecture, and maintainer discipline.
3. "underground_edge": High-contrast comparative breakdown (3-5 comprehensive sentences). Compare this project directly against bloated corporate frameworks or mainstream libraries. Explain specifically why a principal engineer would adopt this focused implementation over the popular alternatives.
4. "caveats": Honest, hard-hitting technical risk assessment (3-5 comprehensive sentences). Detail single-maintainer bus factor, edge-case gaps, platform limitations, memory/threading trade-offs, and production adoption prerequisites.

Output ONLY valid raw JSON with those 4 keys. No markdown code block wraps, no conversational preamble, no trailing text."""

class PollinationsClient:
    def __init__(self, model: str = "openai", timeout: float = 12.0):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Sends prompt to Pollinations AI text API with multi-model fallback."""
        sys_content = system or DEEP_VERDICT_SYSTEM_PROMPT
        models_to_try = [self.model, "mistral", "qwen"] if self.model == "openai" else [self.model, "openai"]

        for m in models_to_try:
            payload = {
                "messages": [
                    {"role": "system", "content": sys_content},
                    {"role": "user", "content": prompt},
                ],
                "model": m,
                "seed": 42,
            }

            # Try POST JSON
            try:
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    POLLINATIONS_TEXT_URL,
                    data=req_data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "gitSOLVE/0.2.0 (github.com/Dev2Creator/gitSOLVE)",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw_text = resp.read().decode("utf-8", errors="replace")
                    sanitized = sanitize_terminal_output(raw_text, max_length=6000)
                    if sanitized and len(sanitized.strip()) > 30:
                        return sanitized
            except Exception:
                pass

            # Fallback to GET request
            try:
                encoded_prompt = urllib.parse.quote(prompt[:1200])
                encoded_sys = urllib.parse.quote(sys_content[:400])
                url = f"{POLLINATIONS_TEXT_URL}{encoded_prompt}?system={encoded_sys}&model={m}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "gitSOLVE/0.2.0"},
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw_text = resp.read().decode("utf-8", errors="replace")
                    sanitized = sanitize_terminal_output(raw_text, max_length=6000)
                    if sanitized and len(sanitized.strip()) > 30:
                        return sanitized
            except Exception:
                continue

        return ""

    def generate_deep_verdict(self, repo: Dict[str, Any], readme_snippet: str = "") -> Dict[str, str]:
        """Generates an exhaustive, multi-dimensional AI verdict powered by Pollinations AI."""
        repo_name = repo.get("full_name", "unknown/repo")
        desc = repo.get("description") or "Handcrafted underground repository"
        lang = repo.get("primary_language", "Code")
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        age = repo.get("age_text", "established")
        pushed_days = repo.get("pushed_days", 0)
        has_tests = repo.get("has_tests", False)
        has_ci = repo.get("has_ci", False)
        ci_verified = repo.get("ci_verified_passing", False)
        loc = repo.get("loc_estimate", 0)
        source_count = repo.get("source_files_count", 0)
        findings = repo.get("positive_evidence", [])
        risks = repo.get("negative_risks", [])

        # Readme context
        readme_text = readme_snippet or repo.get("readme") or ""
        if readme_text:
            clean_rm = re.sub(r"!\[.*?\]\(.*?\)", "", readme_text)
            clean_rm = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", clean_rm).strip()[:3500]
        else:
            clean_rm = ""

        # Language breakdown
        lang_dict = repo.get("languages", {})
        if lang_dict:
            total_bytes = sum(lang_dict.values())
            lang_breakdown = ", ".join(
                f"{k} ({int(v / total_bytes * 100)}%)"
                for k, v in sorted(lang_dict.items(), key=lambda x: x[1], reverse=True)[:4]
            )
        else:
            lang_breakdown = lang

        prompt_parts = [
            f"=== TARGET SPECIMEN: {repo_name} ===",
            f"Primary Language: {lang} | Language Distribution: {lang_breakdown}",
            f"Stars: {stars} | Forks: {forks} | Age: {age} | Last Pushed: {pushed_days} days ago",
            f"Source Files: ~{source_count} modules (~{loc:,} estimated LoC)",
            f"Automated Tests: {'Verified Present' if has_tests else 'None detected'}",
            f"CI/CD Workflow: {'Passing & Active' if ci_verified else ('Configured' if has_ci else 'None')}",
            f"Official One-Liner Description: {desc}",
        ]
        if findings:
            prompt_parts.append(f"Verified Architectural Signals: {'; '.join(findings[:5])}")
        if risks:
            prompt_parts.append(f"Forensic Risks: {'; '.join(risks[:3])}")
        if clean_rm:
            prompt_parts.append(f"\n=== DOCUMENTATION & ARCHITECTURE EXTRACT ===\n{clean_rm}")
        else:
            prompt_parts.append("\nNote: Rely on language semantics, module footprint, and architectural signals.")

        prompt_parts.append("\nPerform an exhaustive, deeply technical architectural audit as instructed.")
        prompt = "\n".join(prompt_parts)

        raw = self.generate(prompt, system=DEEP_VERDICT_SYSTEM_PROMPT)
        if raw:
            # Strip markdown block wraps if present
            clean_raw = raw.strip()
            if clean_raw.startswith("```"):
                clean_raw = re.sub(r"^```(?:json)?\s*", "", clean_raw)
                clean_raw = re.sub(r"\s*```$", "", clean_raw)

            try:
                match = re.search(r"\{.*\}", clean_raw, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "verdict" in parsed and "why_good" in parsed:
                        return {
                            "verdict": parsed.get("verdict", "").strip(),
                            "why_good": parsed.get("why_good", "").strip(),
                            "underground_edge": parsed.get("underground_edge", "").strip(),
                            "caveats": parsed.get("caveats", "").strip(),
                        }
            except Exception:
                pass

            if len(raw.strip()) > 50:
                return {
                    "verdict": raw.strip(),
                    "why_good": f"Architecturally focused {lang} implementation prioritizing low overhead and zero unnecessary dependencies.",
                    "underground_edge": "Eliminates framework bloat and corporate telemetry, delivering deterministic, auditable execution.",
                    "caveats": "Solo maintainer scope. Verify API stability and boundary test coverage before mission-critical adoption.",
                }

        # Offline deterministic high-signal fallback
        return self._offline_fallback_verdict(repo)

    def explain_repo(self, repo: Dict[str, Any], readme_snippet: str = "") -> str:
        """Returns a formatted plain-text verdict string with deep analysis."""
        v = self.generate_deep_verdict(repo, readme_snippet=readme_snippet)
        lines = [
            f"✦ DETAILED VERDICT:\n  {v['verdict']}\n",
            f"✦ WHY THIS IS GOOD:\n  {v['why_good']}\n",
            f"✦ UNDERGROUND EDGE:\n  {v['underground_edge']}\n",
            f"✦ CAVEATS & TRADEOFFS:\n  {v['caveats']}",
        ]
        return "\n".join(lines)

    def ask_repo(self, repo: Dict[str, Any], question: str) -> str:
        """Asks a specific technical question about the repository to Pollinations AI with rich context."""
        repo_name = repo.get("full_name", "unknown/repo")
        lang = repo.get("primary_language", "Code")
        desc = repo.get("description", "")
        rm_text = repo.get("readme", "")
        clean_rm = re.sub(r"!\[.*?\]\(.*?\)", "", rm_text)[:3000].strip() if rm_text else ""

        sys_prompt = (
            "You are gitSOLVE's Senior Principal Systems Engineer. "
            "You are answering an engineering query about an open-source codebase. "
            "Be technically precise, authoritative, and direct. Explain data structures, algorithms, "
            "concurrency guarantees, performance characteristics, and practical trade-offs. "
            "Never provide generic filler."
        )
        prompt_parts = [
            f"Repository: {repo_name} ({lang})",
            f"Description: {desc}",
        ]
        if clean_rm:
            prompt_parts.append(f"README Documentation Extract:\n{clean_rm}\n")
        prompt_parts.append(f"User Question: {question}")
        prompt_parts.append("Provide a thorough, developer-grade explanation answering the question:")
        ans = self.generate("\n".join(prompt_parts), system=sys_prompt)
        if ans and len(ans.strip()) > 20:
            return ans
        return (
            f"Analysis of {repo_name} ({lang}): {desc}. "
            f"Based on repository metadata, this codebase is structured around {lang} idioms with a flat modular footprint. "
            f"To inspect implementation details regarding '{question}', use `[t] Tree` to explore the source tree or `[r] Readme`."
        )

    def _offline_fallback_verdict(self, repo: Dict[str, Any]) -> Dict[str, str]:
        """Generates exhaustive, multi-paragraph deterministic analysis when offline."""
        repo_name = repo.get("full_name", "unknown/repo")
        desc = repo.get("description") or "Focused, single-purpose software module"
        lang = repo.get("primary_language", "Software")
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        has_tests = repo.get("has_tests", False)
        has_ci = repo.get("has_ci", False)
        ci_verified = repo.get("ci_verified_passing", False)
        age = repo.get("age_text", "established")
        pushed_days = repo.get("pushed_days", 0)
        loc = repo.get("loc_estimate", 0)
        source_count = repo.get("source_files_count", 0)
        license_name = repo.get("license") or "Declared Open Source"

        lang_dict = repo.get("languages", {})
        if lang_dict:
            total_b = sum(lang_dict.values())
            lang_summary = ", ".join(f"{k} ({int(v/total_b*100)}%)" for k, v in sorted(lang_dict.items(), key=lambda x: x[1], reverse=True)[:3])
        else:
            lang_summary = f"100% {lang}"

        # 1. Verdict (Detailed Architecture)
        verdict_paras = [
            f"{repo_name} is an underground {lang} project implementing {desc.rstrip('.')}.",
            f"Under the hood, the project is structured as a disciplined, single-purpose system spanning approximately ~{loc:,} lines of code across {source_count} source modules ({lang_summary}).",
            f"The codebase prioritizes low-overhead runtime execution and direct algorithmic implementation, eschewing heavy multi-layer framework abstractions in favor of transparent, inspectable source routines.",
        ]
        verdict_str = " ".join(verdict_paras)

        # 2. Why Good (Craftsmanship & Engineering Discipline)
        craft_points = []
        if has_tests:
            craft_points.append("Maintains a dedicated automated test suite verifying core functional contracts, a rare discipline in early-stage sleeper repositories")
        else:
            craft_points.append(f"Maintains a compact, flat code footprint that minimizes cognitive overhead during code reviews")
        if ci_verified:
            craft_points.append("Enforces passing continuous integration (CI) pipelines that validate builds across targets")
        elif has_ci:
            craft_points.append("Maintains automated CI workflow definitions to safeguard against compilation regressions")
        craft_points.append(f"Sustained development across {age} with commits pushed within {pushed_days} days, reflecting steady iterative refinement rather than abandoned prototype churn")
        craft_points.append(f"Distributes under {license_name} with zero commercial telemetry or closed tracking bloat")
        why_good_str = ". ".join(craft_points) + "."

        # 3. Underground Edge (Comparative Analysis)
        edge_paras = [
            f"Compared to bloated mainstream alternatives in the {lang} ecosystem, {repo_name} eliminates unnecessary transitive dependencies, runtime daemons, and corporate lock-in.",
            f"A staff engineer would select this codebase for its auditable surface area, predictable memory characteristics, and instant compilation times, making it ideal for low-latency pipelines, embedded utilities, or modular integration.",
        ]
        edge_str = " ".join(edge_paras)

        # 4. Caveats (Engineering Risks)
        risk_points = []
        risk_points.append(f"Solo maintainer territory: with {stars} stars and {forks} forks, development cadence rests primarily on the original creator without a secondary review board")
        risk_points.append(f"API volatility: as an emerging tool with quiet adoption, breaking interface changes may occur between minor revisions")
        if pushed_days > 45:
            risk_points.append(f"Commit latency: last active commit was {pushed_days} days ago, requiring manual verification of compatibility with latest upstream toolchains")
        else:
            risk_points.append(f"Production readiness: developers should benchmark concurrency and boundary conditions against their specific workloads before coupling to mission-critical infrastructure")
        caveat_str = ". ".join(risk_points) + "."

        return {
            "verdict": verdict_str,
            "why_good": why_good_str,
            "underground_edge": edge_str,
            "caveats": caveat_str,
        }

    def parse_natural_radar_query(self, user_text: str) -> Dict[str, Any]:
        """Translates natural language search into radar coordinates."""
        lang = ""
        for known_lang in ("rust", "python", "go", "typescript", "c", "cpp", "zig", "lua"):
            if re.search(rf"\b{known_lang}\b", user_text, re.IGNORECASE):
                lang = known_lang
                break

        return {
            "topic": "",
            "language": lang,
            "query": user_text,
            "min_stars": 2,
            "max_stars": 7,
        }
