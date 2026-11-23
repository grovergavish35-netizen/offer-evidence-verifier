
import re

from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)


FEE_TERMS = (
    r"registration\s+fee",
    r"security\s+deposit",
    r"training\s+fee",
    r"processing\s+fee",
    r"joining\s+fee",
    r"onboarding\s+fee",
)

FEE_PATTERN = re.compile(
    r"\b(?:" + "|".join(FEE_TERMS) + r")\b",
    re.IGNORECASE,
)

NEGATION_WORDS = re.compile(
    r"\b(?:no|zero|without|never|not|"
    r"don't|do not|won't|will not)\b",
    re.IGNORECASE,
)

NEGATION_AFTER = re.compile(
    r"^\s*(?:is\s+|will\s+be\s+)?"
    r"(?:not\s+required|waived|not\s+charged)",
    re.IGNORECASE,
)


def is_negated_fee(text: str, match: re.Match) -> bool:
    """
    Detect whether a fee phrase is negated.

    Examples:
    - No registration fee required
    - Registration fee is not required
    - Without training fee
    """

    before = text[max(0, match.start() - 80):match.start()]
    after = text[match.end():match.end() + 50]

    # Limit context to the same sentence or line.
    before = re.split(r"[.!?\n;]", before)[-1]
    after = re.split(r"[.!?\n;]", after)[0]

    # Check negation immediately before the fee term.
    before_words = before.strip().split()
    nearby_before = " ".join(before_words[-5:])

    negation_before = bool(
        NEGATION_WORDS.search(nearby_before)
    )

    # Check negation immediately after the fee term.
    negation_after = bool(
        NEGATION_AFTER.search(after)
    )

    return negation_before or negation_after


def check_fee_request(claim: Claim) -> CheckResult:
    """
    Detect recruitment fee requests while avoiding
    false positives from explicitly negated fee terms.
    """

    text = claim.value or ""

    matches = list(FEE_PATTERN.finditer(text))

    if not matches:
        return CheckResult(
            claim=claim,
            check_name="fee_detector",
            finding="No recognized recruitment fee term detected.",
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            finding_type=FindingType.UNKNOWN,
            confidence_note=(
                "No detected fee term does not establish "
                "that the offer is safe."
            ),
        )

    positive_terms = []
    negated_terms = []

    for match in matches:
        if is_negated_fee(text, match):
            negated_terms.append(match.group(0))
        else:
            positive_terms.append(match.group(0))

    if positive_terms:
        return CheckResult(
            claim=claim,
            check_name="fee_detector",
            finding=(
                "Potential recruitment payment request: "
                + ", ".join(positive_terms)
            ),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            finding_type=FindingType.RISK_SIGNAL,
            confidence_note=(
                "A recruitment payment request is a caution "
                "signal, not proof of fraud. Verify the "
                "employer's payment policy independently."
            ),
        )

    return CheckResult(
        claim=claim,
        check_name="fee_detector",
        finding=(
            "Fee-related wording appears to deny "
            "or waive a payment requirement: "
            + ", ".join(negated_terms)
        ),
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=FindingType.UNKNOWN,
        confidence_note=(
            "Negation was detected using rule-based text "
            "analysis. Review the complete sentence manually."
        ),
    )

