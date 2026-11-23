
import re

from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)

PATTERNS = {
    "Immediate payment pressure": (
        r"\bpay\s+immediately\b",
        r"\bpay\s+now\b",
        r"\bpayment\s+within\s+\d+\s*(hours?|days?)\b",
    ),
    "Artificial urgency": (
        r"\blimited\s+time\b",
        r"\bact\s+now\b",
        r"\bwithin\s+\d+\s*(hours?|days?)\b",
        r"\brespond\s+immediately\b",
    ),
    "Messaging-app communication": (
        r"\bwhatsapp\b",
        r"\btelegram\b",
    ),
    "Unusual hiring promise": (
        r"\bguaranteed\s+job\b",
        r"\bno\s+interview\s+required\b",
    ),
}

def check_urgency_channel(claim: Claim) -> CheckResult:
    text = claim.value or ""
    signals = []

    for label, expressions in PATTERNS.items():
        if any(
            re.search(expression, text, re.IGNORECASE)
            for expression in expressions
        ):
            signals.append(label)

    if signals:
        return CheckResult(
            claim=claim,
            check_name="urgency_channel",
            finding=(
                "Potential caution signals: "
                + "; ".join(signals)
            ),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            finding_type=FindingType.RISK_SIGNAL,
            confidence_note=(
                "These patterns can also occur in legitimate "
                "communications. They are not proof of fraud. "
                "Review the context and verify independently."
            ),
        )

    return CheckResult(
        claim=claim,
        check_name="urgency_channel",
        finding=(
            "No recognized urgency or communication "
            "warning patterns detected."
        ),
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=FindingType.UNKNOWN,
        confidence_note=(
            "Absence of these patterns does not verify an offer."
        ),
    )
