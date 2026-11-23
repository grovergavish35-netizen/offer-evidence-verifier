
import re

from core.schemas import Claim, CheckResult, Verdict


PATTERNS = {
    "urgent_deadline": [
        r"\bwithin\s+\d+\s*(?:hours?|hrs?|days?)\b",
        r"\bpay\s+(?:immediately|today|now)\b",
        r"\blimited\s+time\b",
        r"\bfinal\s+warning\b",
    ],
    "messaging_channel": [
        r"\bwhatsapp\b",
        r"\btelegram\b",
    ],
    "guaranteed_job": [
        r"\bguaranteed\s+(?:job|placement|selection)\b",
        r"\b100%\s+(?:guaranteed\s+)?(?:job|placement|selection)\b",
    ],
    "no_interview": [
        r"\bno\s+interview\s+(?:required|needed)\b",
        r"\bwithout\s+(?:any\s+)?interview\b",
    ],
}


def check_urgency_channel(claim: Claim) -> CheckResult:
    text = claim.value.lower()
    detected = []

    for category, patterns in PATTERNS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            detected.append(category)

    if not detected:
        return CheckResult(
            claim=claim,
            check_name="urgency_channel",
            finding="No configured warning patterns detected.",
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "Absence of warning patterns does not "
                "verify the offer."
            ),
        )

    return CheckResult(
        claim=claim,
        check_name="urgency_channel",
        finding=(
            "Detected recruitment warning signals: "
            + ", ".join(detected)
        ),
        source="Submitted offer text",
        verdict=Verdict.INCONSISTENT,
        confidence_note=(
            "These are risk signals, not proof of fraud. "
            "Messaging apps alone do not indicate fraud."
        ),
    )
