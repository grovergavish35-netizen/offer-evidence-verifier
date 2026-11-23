
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
        r"\bpayment\s+within\s+\d+\s*(?:hours?|days?)\b",
    ),
    "Artificial urgency": (
        r"\blimited\s+time\b",
        r"\bact\s+now\b",
        r"\bwithin\s+\d+\s*(?:hours?|days?)\b",
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

NEGATIVE_CHANNEL_CONTEXT = re.compile(
    r"\b(?:no|never|without|do\s+not|don't|"
    r"not\s+through|not\s+via|not\s+on)\b",
    re.IGNORECASE,
)

NEGATIVE_PRESSURE_CONTEXT = re.compile(
    r"\b(?:no|never|without|do\s+not|don't|"
    r"not\s+required|not\s+necessary)\b",
    re.IGNORECASE,
)

CHANNELS = re.compile(
    r"\b(?:whatsapp|telegram)\b",
    re.IGNORECASE,
)

PRESSURE = re.compile(
    r"\b(?:pay\s+(?:now|immediately|today)|"
    r"transfer\s+(?:now|immediately|today)|"
    r"payment\s+within\s+\d+\s*(?:hours?|days?)|"
    r"limited\s+time|act\s+now|"
    r"within\s+\d+\s*(?:hours?|days?)|"
    r"respond\s+immediately|"
    r"offer\s+expires\s+(?:today|tomorrow))\b",
    re.IGNORECASE,
)

HIRING_PROMISE = re.compile(
    r"\b(?:guaranteed\s+job|"
    r"no\s+interview\s+required)\b",
    re.IGNORECASE,
)

def _sentences(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"[.!?;\n]+", text)
        if part.strip()
    ]

def _negated_before(
    sentence: str,
    start: int,
    pattern: re.Pattern,
) -> bool:
    before = sentence[:start]
    nearby = " ".join(before.split()[-6:])
    return bool(pattern.search(nearby))

def check_urgency_channel(claim: Claim) -> CheckResult:
    text = claim.value or ""
    signals = []

    for sentence in _sentences(text):
        for match in PRESSURE.finditer(sentence):
            if not _negated_before(
                sentence,
                match.start(),
                NEGATIVE_PRESSURE_CONTEXT,
            ):
                if re.search(
                    r"\bpay\b|\btransfer\b|\bpayment\b",
                    match.group(0),
                    re.IGNORECASE,
                ):
                    label = "Immediate payment pressure"
                else:
                    label = "Artificial urgency"

                if label not in signals:
                    signals.append(label)

        for match in CHANNELS.finditer(sentence):
            if not _negated_before(
                sentence,
                match.start(),
                NEGATIVE_CHANNEL_CONTEXT,
            ):
                label = "Messaging-app communication"
                if label not in signals:
                    signals.append(label)

        for match in HIRING_PROMISE.finditer(sentence):
            label = "Unusual hiring promise"
            if label not in signals:
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
                "These patterns may also appear in legitimate "
                "communications. Messaging apps and urgent "
                "deadlines are not proof of fraud. "
                "Verify the context independently."
            ),
        )

    return CheckResult(
        claim=claim,
        check_name="urgency_channel",
        finding=(
            "No affirmative urgency, messaging-channel "
            "or unusual hiring-promise patterns detected."
        ),
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=FindingType.UNKNOWN,
        confidence_note=(
            "Rule-based detection can miss indirect language. "
            "Absence of warnings does not verify the offer."
        ),
    )