"""
Evaluation Service
------------------
Aggregates evaluation scores from individual answers
and produces overall interview performance metrics.
"""

from typing import List, Dict, Optional, Any
from statistics import mean


def aggregate_scores(evaluations: List[Dict]) -> Dict[str, Optional[float]]:
    """
    Given a list of evaluation dicts, compute category-level and overall scores.
    """
    if not evaluations:
        return {
            "overall_score": None,
            "technical_score": None,
            "hr_score": None,
            "behavioral_score": None,
            "communication_score": None,
            "relevance_score": None,
            "completeness_score": None,
        }

    all_scores = [e["score"] for e in evaluations if e.get("score") is not None]
    overall = round(mean(all_scores), 2) if all_scores else None

    def _category_score(cat: str, key: str) -> Optional[float]:
        vals = []
        for e in evaluations:
            if e.get("question_category") == cat:
                cat_scores = e.get("category_scores") or {}
                v = cat_scores.get(key)
                if v is not None:
                    vals.append(v)
        return round(mean(vals), 2) if vals else None

    # Communication — average across all questions
    comm_vals = []
    for e in evaluations:
        cat_scores = e.get("category_scores") or {}
        v = cat_scores.get("communication")
        if v is not None:
            comm_vals.append(v)

    # Relevance
    rel_vals = []
    for e in evaluations:
        cat_scores = e.get("category_scores") or {}
        v = cat_scores.get("relevance")
        if v is not None:
            rel_vals.append(v)

    # Completeness
    comp_vals = []
    for e in evaluations:
        cat_scores = e.get("category_scores") or {}
        v = cat_scores.get("completeness")
        if v is not None:
            comp_vals.append(v)

    # Technical — from technical questions
    tech_vals = []
    for e in evaluations:
        if e.get("question_category") == "technical":
            cat_scores = e.get("category_scores") or {}
            v = cat_scores.get("technical_correctness")
            if v is not None:
                tech_vals.append(v)
            elif e.get("score") is not None:
                tech_vals.append(e["score"])

    # HR
    hr_vals = [e["score"] for e in evaluations if e.get("question_category") == "hr" and e.get("score") is not None]

    # Behavioral
    beh_vals = [e["score"] for e in evaluations if e.get("question_category") == "behavioral" and e.get("score") is not None]

    return {
        "overall_score": overall,
        "technical_score": round(mean(tech_vals), 2) if tech_vals else None,
        "hr_score": round(mean(hr_vals), 2) if hr_vals else None,
        "behavioral_score": round(mean(beh_vals), 2) if beh_vals else None,
        "communication_score": round(mean(comm_vals), 2) if comm_vals else None,
        "relevance_score": round(mean(rel_vals), 2) if rel_vals else None,
        "completeness_score": round(mean(comp_vals), 2) if comp_vals else None,
    }


def readiness_level(score: Optional[float]) -> str:
    if score is None:
        return "Needs Improvement"
    if score >= 8.5:
        return "Interview Ready"
    if score >= 7.0:
        return "Strong"
    if score >= 5.5:
        return "Good"
    if score >= 3.5:
        return "Developing"
    return "Needs Improvement"


def identify_weak_areas(evaluations: List[Dict]) -> List[str]:
    """Return a list of weak skill areas based on evaluations."""
    weak = []
    scores: Dict[str, List[float]] = {}

    for e in evaluations:
        cat = e.get("question_category", "general")
        s = e.get("score")
        if s is not None:
            scores.setdefault(cat, []).append(s)
        for weakness in (e.get("weaknesses") or []):
            if weakness not in weak:
                weak.append(weakness)

    # Also flag low-scoring categories
    for cat, vals in scores.items():
        avg = mean(vals)
        if avg < 5.5:
            label = f"Low {cat.title()} performance (avg {avg:.1f}/10)"
            if label not in weak:
                weak.append(label)

    return weak[:8]
