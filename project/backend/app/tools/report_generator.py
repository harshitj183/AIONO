"""
Report Generator Tool – structures the agent's collected evidence into a
formatted, evidence-backed investigation report.
This is deterministic (no LLM call) – just organises data the agent gathered.
"""

import json
from typing import Any
from langchain_core.tools import tool


@tool
def report_generator_tool(
    question: str,
    root_cause: str,
    evidence: list,
    recommendations: list,
    confidence: str,
    needs_human_review: bool = False,
) -> str:
    """
    Structure investigation findings into a formatted evidence-backed report.

    This tool should be called at the end of an investigation after all
    evidence has been gathered and the root cause has been identified.

    Args:
        question: The original business question being investigated.
        root_cause: One-sentence root cause conclusion.
        evidence: List of evidence dicts, each with keys:
                  - "claim": what the evidence shows
                  - "source": where it came from (tool + table/doc name)
                  - "data": supporting data points (string or dict)
                  - "confidence": "high" | "medium" | "low"
        recommendations: List of actionable recommendation strings.
        confidence: Overall investigation confidence: "high" | "medium" | "low"
        needs_human_review: True if evidence is insufficient or contradictory.

    Returns a structured JSON report ready for the frontend to render.
    """
    if not evidence:
        return json.dumps({
            "error": "Cannot generate report without evidence.",
            "needs_human_review": True,
        })

    if not root_cause or root_cause.strip() == "":
        return json.dumps({
            "error": "Root cause cannot be empty.",
            "needs_human_review": True,
        })

    # Validate evidence items
    validated_evidence = []
    for item in evidence:
        if isinstance(item, dict):
            validated_evidence.append({
                "claim": item.get("claim", ""),
                "source": item.get("source", "Unknown source"),
                "data": item.get("data", ""),
                "confidence": item.get("confidence", "medium"),
            })

    report = {
        "question": question,
        "root_cause": root_cause,
        "confidence": confidence,
        "needs_human_review": needs_human_review,
        "evidence_count": len(validated_evidence),
        "evidence": validated_evidence,
        "recommendations": recommendations,
        "evidence_quality": _assess_evidence_quality(validated_evidence),
        "report_status": "needs_review" if needs_human_review else "complete",
    }

    return json.dumps(report)


def _assess_evidence_quality(evidence: list) -> str:
    """Assess the overall quality of collected evidence."""
    if not evidence:
        return "insufficient"
    high_conf = sum(1 for e in evidence if e.get("confidence") == "high")
    ratio = high_conf / len(evidence)
    if len(evidence) >= 3 and ratio >= 0.6:
        return "strong"
    elif len(evidence) >= 2 and ratio >= 0.3:
        return "moderate"
    else:
        return "weak"
