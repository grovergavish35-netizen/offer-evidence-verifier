"""Explain relationships between existing verification findings.

This module never changes individual check verdicts or determines fraud.
"""
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CorrelationObservation:
    observation_id: str
    title: str
    explanation: str
    related_checks: tuple[str, ...]
    recommended_action: str
    limitation: str
    category: str = "combined_risk_signals"

    def to_dict(self) -> dict:
        result = asdict(self)
        result["related_checks"] = list(self.related_checks)
        return result


def _value(item: Any) -> str:
    return str(getattr(item, "value", item)).lower()


def _risk(check: Any) -> bool:
    return _value(getattr(check, "finding_type", "")) == "risk_signal"


def _contradiction(check: Any) -> bool:
    return _value(getattr(check, "finding_type", "")) == "contradiction"


def _support(check: Any) -> bool:
    return _value(getattr(check, "finding_type", "")) == "supporting_evidence"


def correlate_evidence(report: Any) -> list[CorrelationObservation]:
    """Correlate check *classifications*, without inferring unsupported facts.

    Accepts a VerificationReport-like object exposing ``checks``. Repeated
    check names are deduplicated. Missing checks are never assumed negative.
    """
    checks = list(getattr(report, "checks", []) or [])
    risks = {str(c.check_name) for c in checks if _risk(c)}
    contradictions = {str(c.check_name) for c in checks if _contradiction(c)}
    supports = {str(c.check_name) for c in checks if _support(c)}
    observations: list[CorrelationObservation] = []

    fee = sorted(risks & {"fee_detector", "fee_request"})
    urgency = "urgency_channel" in risks
    if fee and urgency:
        observations.append(CorrelationObservation(
            observation_id="fee_and_urgency",
            title="Payment request combined with pressure signals",
            explanation=(
                "The fee check and urgency/channel check both reported risk "
                "signals. Review their individual evidence: the checks do "
                "not establish that the same sentence caused both findings."
            ),
            related_checks=(fee[0], "urgency_channel"),
            recommended_action=(
                "Do not send money or sensitive documents until the employer "
                "confirms the request through an independently obtained channel."
            ),
            limitation=(
                "These are rule-based signals, not proof of fraud. The urgency "
                "check may flag timing, a messaging channel, or another pattern; "
                "this correlation does not identify which one."
            ),
        ))

    if "email_domain" in contradictions and (fee or urgency):
        related = ["email_domain"] + fee + (["urgency_channel"] if urgency else [])
        observations.append(CorrelationObservation(
            observation_id="domain_conflict_with_risk",
            title="Domain contradiction alongside caution signals",
            explanation=(
                "The recruiter-domain check reported a contradiction and "
                "at least one separate check reported a risk signal."
            ),
            related_checks=tuple(related),
            recommended_action=(
                "Contact the organization using contact details obtained "
                "independently, not solely from the offer."
            ),
            limitation=(
                "A domain mismatch and risk signals do not conclusively "
                "establish impersonation or fraud."
            ),
            category="contradiction_and_risk",
        ))

    if supports and contradictions:
        observations.append(CorrelationObservation(
            observation_id="mixed_support_and_contradiction",
            title="Supporting checks do not cancel contradictions",
            explanation=(
                "The report contains both supporting findings and "
                "contradictions. Each addresses a limited aspect of the offer."
            ),
            related_checks=tuple(sorted(supports | contradictions)),
            recommended_action=(
                "Review each contradiction independently before relying on "
                "supporting findings."
            ),
            limitation=(
                "Supporting consistency is not authentication; this is not "
                "a numerical score or overall fraud verdict."
            ),
            category="mixed_evidence",
        ))

    return observations


def export_correlations(report: Any) -> list[dict]:
    """Return JSON-serializable correlation observations."""
    return [item.to_dict() for item in correlate_evidence(report)]
