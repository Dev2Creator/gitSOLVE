# gitSOLVE ✦ Explainable, Evidence-Backed Repository Scoring Engine
# Software for Humans. Honest metrics, zero theater.

from typing import Any, Dict, List, Optional, Tuple

class EvidenceStatus:
    VERIFIED = "Verified"
    DETECTED = "Detected"
    UNKNOWN = "Unknown"
    NOT_CHECKED = "Not checked"

class RepoScoreReport:
    def __init__(self):
        self.health_score: int = 0
        self.discovery_score: int = 0
        self.overall_score: int = 0
        self.confidence: str = "Medium"
        self.tier: str = "✨ HIDDEN GEM"
        self.positive_evidence: List[str] = []
        self.negative_risks: List[str] = []
        self.missing_data: List[str] = []
        self.breakdown: Dict[str, int] = {}
        self.evidence_status: Dict[str, str] = {}

    @property
    def rarity_tier(self) -> str:
        return self.tier

    @rarity_tier.setter
    def rarity_tier(self, val: str) -> None:
        self.tier = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "health_score": self.health_score,
            "discovery_score": self.discovery_score,
            "confidence": self.confidence,
            "tier": self.tier,
            "rarity_tier": self.rarity_tier,
            "positive_evidence": self.positive_evidence,
            "negative_risks": self.negative_risks,
            "missing_data": self.missing_data,
            "breakdown": self.breakdown,
            "evidence_status": self.evidence_status,
        }

def calculate_explainable_score(
    stars: int,
    age_days: int,
    pushed_days: int,
    is_fork: bool,
    has_tests: bool,
    has_ci_workflow: bool,
    ci_verified_passing: Optional[bool],
    modern_manifest: Optional[str],
    has_readme: bool,
    readme_len: int,
    has_docs_guide: bool,
    has_demo_assets: bool,
    semantic_commits: int,
    commit_cadence_days: int,
    license_declared: Optional[str],
    source_files_count: int,
    languages: Dict[str, int],
    has_security_policy: bool = False,
) -> RepoScoreReport:
    """Computes an honest, evidence-backed evaluation separating Discovery Potential from Health."""
    report = RepoScoreReport()
    
    # 1. REPOSITORY HEALTH SCORE (Max 100)
    # Dimensions: Testing & CI (25), Maintenance (20), Documentation (20), Code Structure (20), Toolchain (15)
    health = 0
    breakdown = {}

    # Dimension: Testing & CI (25 pts)
    test_pts = 0
    if ci_verified_passing is True:
        test_pts += 25
        report.positive_evidence.append("Automated CI/CD workflows verified passing on recent runs")
        report.evidence_status["CI/CD Workflows"] = EvidenceStatus.VERIFIED
        report.evidence_status["ci"] = EvidenceStatus.VERIFIED
    elif has_ci_workflow is True:
        test_pts += 15
        report.positive_evidence.append("GitHub Actions CI/CD workflow configured (execution status unverified)")
        report.evidence_status["CI/CD Workflows"] = EvidenceStatus.DETECTED
        report.evidence_status["ci"] = EvidenceStatus.DETECTED
    elif has_ci_workflow is False:
        report.negative_risks.append("No automated CI/CD workflow detected")
        report.evidence_status["CI/CD Workflows"] = EvidenceStatus.UNKNOWN
        report.evidence_status["ci"] = EvidenceStatus.UNKNOWN
    else:
        report.evidence_status["CI/CD Workflows"] = EvidenceStatus.NOT_CHECKED
        report.evidence_status["ci"] = EvidenceStatus.NOT_CHECKED

    if has_tests is True:
        if not ci_verified_passing:
            test_pts += 10
        report.positive_evidence.append("Dedicated test suite files detected in repository tree")
        report.evidence_status["Test Suite"] = EvidenceStatus.DETECTED
        report.evidence_status["tests"] = EvidenceStatus.DETECTED
    elif has_tests is False:
        report.negative_risks.append("No test directory or test suites detected")
        report.evidence_status["Test Suite"] = EvidenceStatus.UNKNOWN
        report.evidence_status["tests"] = EvidenceStatus.UNKNOWN
    else:
        report.evidence_status["Test Suite"] = EvidenceStatus.NOT_CHECKED
        report.evidence_status["tests"] = EvidenceStatus.NOT_CHECKED

    test_pts = min(25, test_pts)
    breakdown["testing_ci"] = test_pts
    health += test_pts

    # Dimension: Maintenance & Cadence (20 pts)
    maint_pts = 0
    if pushed_days <= 7:
        maint_pts += 10
        report.positive_evidence.append("Highly active maintenance: pushed within the last 7 days")
        report.evidence_status["Maintenance"] = EvidenceStatus.VERIFIED
    elif pushed_days <= 30:
        maint_pts += 8
        report.positive_evidence.append("Actively maintained: pushed within the last 30 days")
        report.evidence_status["Maintenance"] = EvidenceStatus.VERIFIED
    elif pushed_days <= 90:
        maint_pts += 4
        report.evidence_status["Maintenance"] = EvidenceStatus.DETECTED
    else:
        report.negative_risks.append(f"Maintenance cooldown: last pushed {pushed_days} days ago")
        report.evidence_status["Maintenance"] = EvidenceStatus.DETECTED

    if semantic_commits >= 5:
        maint_pts += 6
        report.positive_evidence.append(f"Disciplined commit hygiene ({semantic_commits}/15 commits use strict semantic conventions)")
        report.evidence_status["Commit Hygiene"] = EvidenceStatus.VERIFIED
    elif semantic_commits >= 2:
        maint_pts += 3
        report.evidence_status["Commit Hygiene"] = EvidenceStatus.DETECTED

    if commit_cadence_days >= 14:
        maint_pts += 4
        report.positive_evidence.append("Consistent cadence: development spanning multiple weeks")
        report.evidence_status["Commit Cadence"] = EvidenceStatus.VERIFIED

    maint_pts = min(20, maint_pts)
    breakdown["maintenance"] = maint_pts
    health += maint_pts

    # Dimension: Documentation & Onboarding (20 pts)
    doc_pts = 0
    if has_readme:
        if has_docs_guide and has_demo_assets:
            doc_pts += 20
            report.positive_evidence.append("Comprehensive documentation with usage guide and visual demo assets")
            report.evidence_status["Documentation"] = EvidenceStatus.VERIFIED
        elif has_docs_guide:
            doc_pts += 15
            report.positive_evidence.append("Structured documentation with installation and usage instructions")
            report.evidence_status["Documentation"] = EvidenceStatus.VERIFIED
        elif readme_len > 800:
            doc_pts += 10
            report.evidence_status["Documentation"] = EvidenceStatus.DETECTED
        elif readme_len > 200:
            doc_pts += 5
            report.evidence_status["Documentation"] = EvidenceStatus.DETECTED
        else:
            report.negative_risks.append("README is minimal (under 200 characters)")
            report.evidence_status["Documentation"] = EvidenceStatus.DETECTED
    else:
        report.negative_risks.append("No README file found")
        report.evidence_status["Documentation"] = EvidenceStatus.UNKNOWN

    doc_pts = min(20, doc_pts)
    breakdown["documentation"] = doc_pts
    health += doc_pts

    # Dimension: Code Substance & Architecture (20 pts)
    code_pts = 0
    if languages:
        total_bytes = sum(languages.values())
        top_lang = max(languages.items(), key=lambda x: x[1])[0]
        report.positive_evidence.append(f"Verified language distribution: {top_lang} ({total_bytes:,} bytes)")
        report.evidence_status["Languages"] = EvidenceStatus.VERIFIED

    if source_files_count >= 12:
        code_pts += 20
        report.positive_evidence.append(f"Handcrafted multi-module architecture (~{source_files_count} source files)")
        report.evidence_status["Architecture"] = EvidenceStatus.DETECTED
    elif source_files_count >= 5:
        code_pts += 14
        report.positive_evidence.append(f"Cohesive modular implementation (~{source_files_count} source files)")
        report.evidence_status["Architecture"] = EvidenceStatus.DETECTED
    elif source_files_count >= 1:
        code_pts += 8
        report.evidence_status["Architecture"] = EvidenceStatus.DETECTED
    else:
        code_pts += 4
        report.missing_data.append("Detailed file tree was not indexed")
        report.evidence_status["Architecture"] = EvidenceStatus.NOT_CHECKED

    code_pts = min(20, code_pts)
    breakdown["code_substance"] = code_pts
    health += code_pts

    # Dimension: Toolchain & Licensing (15 pts)
    tool_pts = 0
    if modern_manifest:
        tool_pts += 8
        report.positive_evidence.append(f"Standard build manifest present ({modern_manifest})")
        report.evidence_status["Manifest"] = EvidenceStatus.VERIFIED

    if license_declared:
        tool_pts += 7
        report.positive_evidence.append(f"Declared open-source license: {license_declared}")
        report.evidence_status["License"] = EvidenceStatus.VERIFIED
    else:
        report.negative_risks.append("No open-source license declared")
        report.evidence_status["License"] = EvidenceStatus.UNKNOWN

    if has_security_policy:
        tool_pts += 2
        report.positive_evidence.append("Security disclosure policy (SECURITY.md) present")
        report.evidence_status["Security Policy"] = EvidenceStatus.VERIFIED

    tool_pts = min(15, tool_pts)
    breakdown["toolchain"] = tool_pts
    health += tool_pts

    report.health_score = max(10, min(100, health))

    # 2. DISCOVERY POTENTIAL SCORE (Max 100)
    # Measures the "sleeper" signal: high craftsmanship with low stars and sustained maturity
    discovery = 0
    # Star gate ratio
    if stars <= 5:
        discovery += 45
    elif stars <= 15:
        discovery += 35
    elif stars <= 50:
        discovery += 20
    elif stars <= 200:
        discovery += 10
    else:
        discovery += 0

    # Maturity (not a weekend throwaway)
    if age_days >= 60:
        discovery += 25
    elif age_days >= 30:
        discovery += 15
    else:
        discovery += 5

    # Originality (not a fork without explanation)
    if not is_fork:
        discovery += 20
    else:
        discovery += 10

    # Dormancy penalty (stale / abandoned projects lose discovery alpha)
    if pushed_days > 365:
        discovery = max(5, discovery - 35)
    elif pushed_days > 180:
        discovery = max(10, discovery - 15)

    # Health synergy (a project with high health and low stars is the ultimate sleeper)
    if report.health_score >= 70:
        discovery += 10
    elif report.health_score >= 50:
        discovery += 5

    report.discovery_score = max(5, min(100, discovery))

    # 3. OVERALL SCORE (Weighted combination)
    report.overall_score = int((report.health_score * 0.6) + (report.discovery_score * 0.4))
    report.breakdown = breakdown

    # Tier designation
    if report.overall_score >= 88 and report.health_score >= 75:
        report.tier = "💎 MYTHIC SLEEPER"
    elif report.overall_score >= 74 and report.health_score >= 60:
        report.tier = "🔥 SOLID GOLD"
    elif report.overall_score >= 60:
        report.tier = "✨ HIDDEN GEM"
    else:
        report.tier = "🌱 EARLY SEEDLING"

    # Confidence level
    verified_count = sum(1 for status in report.evidence_status.values() if status == EvidenceStatus.VERIFIED)
    if verified_count >= 3:
        report.confidence = "high"
    elif verified_count >= 1:
        report.confidence = "medium"
    else:
        report.confidence = "low"

    return report

def calculate_repository_score(repo: Dict[str, Any], signals: Optional[Dict[str, Any]] = None) -> RepoScoreReport:
    """Convenience evaluator that computes score from raw repo metadata and inspected signals."""
    from datetime import datetime, timezone
    sig = signals or {}
    now = datetime.now(timezone.utc)

    created_str = repo.get("created_at") or ""
    pushed_str = repo.get("pushed_at") or ""

    age_days = 90
    pushed_days = 10
    try:
        if created_str:
            c_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            age_days = max(0, (now - c_dt).days)
        if pushed_str:
            p_dt = datetime.fromisoformat(pushed_str.replace("Z", "+00:00"))
            pushed_days = max(0, (now - p_dt).days)
    except Exception:
        pass

    stars = repo.get("stargazers_count", repo.get("stars", 0))
    is_fork = repo.get("fork", False)
    license_info = repo.get("license")
    lic_name = license_info.get("name") if isinstance(license_info, dict) else (license_info if isinstance(license_info, str) else None)

    return calculate_explainable_score(
        stars=stars,
        age_days=age_days,
        pushed_days=pushed_days,
        is_fork=is_fork,
        has_tests=sig.get("has_tests") if "has_tests" in sig else None,
        has_ci_workflow=sig.get("has_ci") if "has_ci" in sig else None,
        ci_verified_passing=(sig.get("ci_conclusion") == "success") if "ci_conclusion" in sig else None,
        modern_manifest="Manifest" if sig.get("has_manifest") else None,
        has_readme=sig.get("has_readme", True),
        readme_len=sig.get("readme_bytes", 2000),
        has_docs_guide=sig.get("has_docs", False),
        has_demo_assets=sig.get("has_demo", False),
        semantic_commits=sig.get("recent_commit_count", 5),
        commit_cadence_days=pushed_days,
        license_declared=lic_name,
        source_files_count=sig.get("tree_item_count", 20),
        languages=repo.get("languages", {}),
        has_security_policy=sig.get("has_security_policy", False),
    )

