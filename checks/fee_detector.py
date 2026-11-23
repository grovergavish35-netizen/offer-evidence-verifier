
import re

from core.schemas import Claim, CheckResult, Verdict


FEE_TERMS = (
    "registration fee",
    "security deposit",
    "training fee",
    "processing fee",
    "joining fee",
    "verification fee",
)

PAYMENT_TERMS = (
    "pay",
    "payment",
    "deposit",
    "transfer",
    "send money",
)


def check_fee_request(claim: Claim) -> CheckResult:
    """
    Detect whether a claim contains a payment request.

    This check only identifies a risk signal.
    It cannot determine whether an offer is fraudulent.
    """
    text = claim.value.lower()

    matched_fees = [
        term for term in FEE_TERMS if term in text
    ]

    payment_requested = bool(
        re.search(
            r"\b(?:pay|payment|deposit|transfer)\b",
            text,
        )
    ) or "send money" in text

    if matched_fees:
        return CheckResult(
            claim=claim,
            check_name="fee_detector",
            finding=(
                "Potential employment-related fee detected: "
                + ", ".join(matched_fees)
            ),
            source="Submitted offer text",
            verdict=Verdict.INCONSISTENT,
            confidence_note=(
                "A fee request is a risk indicator, "
                "not proof of fraud."
            ),
        )

    if payment_requested:
        return CheckResult(
            claim=claim,
            check_name="fee_detector",
            finding="Payment-related wording detected.",
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "Payment context is unclear. "
                "Manual review is recommended."
            ),
        )

    return CheckResult(
        claim=claim,
        check_name="fee_detector",
        finding="No recognized fee request in this claim.",
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        confidence_note=(
            "No detected fee wording does not establish "
            "that an offer is genuine."
        ),
    )
