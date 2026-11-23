
import re
from dataclasses import dataclass, asdict
from typing import Optional

from core.schemas import VerificationReport

@dataclass(frozen=True)
class EvidenceTrace:
    check_name: str
    finding_type: str
    finding: str
    evidence_text: Optional[str]
    line_number: Optional[int]
    source: str
    reason: str
    limitation: str
    trace_status: str

    def to_dict(self) -> dict:
        return asdict(self)

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

FEE_PATTERN = re.compile(
    r"\b(?:registration|processing|training|"
    r"joining|onboarding)\s+fees?\b"
    r"|\bsecurity\s+deposit\b"
    r"|\bpay\s+(?:rs\.?|inr|₹|\d)",
    re.IGNORECASE,
)

URGENCY_PATTERN = re.compile(
    r"\b(?:whatsapp|telegram|"
    r"pay\s+(?:now|immediately|today)|"
    r"limited\s+time|act\s+now|"
    r"respond\s+immediately|"
    r"within\s+\d+\s*(?:hours?|days?)|"
    r"guaranteed\s+job|"
    r"no\s+interview\s+required)\b",
    re.IGNORECASE,
)

def _enum_value(value) -> str:
    return str(getattr(value, "value", value))

def _text_lines(text: str) -> list[tuple[int, str]]:
    return [
        (number, line.strip())
        for number, line in enumerate(
            text.splitlines(), start=1
        )
        if line.strip()
    ]

def _find_email_evidence(
    text: str,
    claim_value: str,
) -> tuple[Optional[str], Optional[int]]:
    if not claim_value:
        return None, None

    for number, line in _text_lines(text):
        for match in EMAIL_PATTERN.finditer(line):
            if match.group(0).lower() == claim_value.lower():
                return line, number

    return None, None

def _find_pattern_evidence(
    text: str,
    pattern: re.Pattern,
    require_non_negated: bool = False,
) -> tuple[Optional[str], Optional[int]]:

    for number, line in _text_lines(text):
        for match in pattern.finditer(line):
            if require_non_negated:
                before = line[:match.start()]
                nearby = " ".join(before.split()[-6:])

                if re.search(
                    r"\b(?:no|never|without|"
                    r"do\s+not|don't)\b",
                    nearby,
                    re.IGNORECASE,
                ):
                    continue

            return line, number

    return None, None

def _find_claim_evidence(
    text: str,
    claim,
) -> tuple[Optional[str], Optional[int]]:

    if claim is None:
        return None, None

    claim_type = getattr(claim, "claim_type", "")
    value = str(getattr(claim, "value", "") or "")

    if claim_type == "sender_email":
        return _find_email_evidence(text, value)

    if claim_type == "offer_text":
        return None, None

    if value and len(value) <= 300:
        for number, line in _text_lines(text):
            if value.lower() in line.lower():
                return line, number

    return None, None

def _find_evidence(
    text: str,
    check,
) -> tuple[Optional[str], Optional[int]]:

    name = str(check.check_name).lower()

    if name == "email_domain":
        return _find_claim_evidence(
            text,
            check.claim,
        )

    if name in ("fee_detector", "fee_request"):
        return _find_pattern_evidence(
            text,
            FEE_PATTERN,
        )

    if name == "urgency_channel":
        return _find_pattern_evidence(
            text,
            URGENCY_PATTERN,
            require_non_negated=True,
        )

    if name in ("domain_intelligence", "domain_age"):
        return _find_claim_evidence(
            text,
            check.claim,
        )

    if name == "offer_consistency":
        # A consistency check can depend on multiple
        # statements. Do not invent a single source line.
        return None, None

    return _find_claim_evidence(
        text,
        check.claim,
    )

def build_evidence_traces(
    text: str,
    report: VerificationReport,
) -> list[EvidenceTrace]:
    """
    Add source-text trace information to report checks.

    This function does not modify verdicts or findings.

    A matched line is a candidate source reference,
    not proof that the checker relied exclusively
    on that line.
    """

    traces = []

    for check in report.checks:
        finding_type = _enum_value(
            check.finding_type
        )

        evidence_text, line_number = _find_evidence(
            text,
            check,
        )

        source = str(
            getattr(check, "source", None)
            or "Source not specified"
        )

        finding = str(
            getattr(check, "finding", "") or ""
        )

        limitation = str(
            getattr(check, "confidence_note", "")
            or "No limitation supplied by this check."
        )

        if evidence_text is not None:
            trace_status = "candidate_line_match"
        else:
            trace_status = "not_line_traced"

        if finding_type == "risk_signal":
            reason = (
                "The verification rule identified "
                "a potential caution signal."
            )

        elif finding_type == "contradiction":
            reason = (
                "The verification rule identified "
                "an inconsistency with the supplied "
                "reference or other offer information."
            )

        elif finding_type == "supporting_evidence":
            reason = (
                "The verification rule found "
                "limited supporting consistency."
            )

        else:
            reason = (
                "The available evidence was insufficient "
                "for a stronger conclusion."
            )

        traces.append(
            EvidenceTrace(
                check_name=check.check_name,
                finding_type=finding_type,
                finding=finding,
                evidence_text=evidence_text,
                line_number=line_number,
                source=source,
                reason=reason,
                limitation=limitation,
                trace_status=trace_status,
            )
        )

    return traces

def export_evidence_traces(
    text: str,
    report: VerificationReport,
) -> list[dict]:
    return [
        trace.to_dict()
        for trace in build_evidence_traces(
            text,
            report,
        )
    ]