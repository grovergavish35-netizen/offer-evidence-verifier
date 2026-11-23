
from uuid import uuid4

from core.extractor import extract_claims
from core.schemas import Claim, VerificationReport, Verdict

from checks.email_domain import check_email_domain
from checks.fee_detector import check_fee_request
from checks.urgency_channel import check_urgency_channel
from checks.offer_consistency import check_offer_consistency


def verify_offer(
    text: str,
    official_domain: str | None = None,
) -> VerificationReport:

    claims = extract_claims(text)
    results = []

    # Email and fee checks
    for claim in claims:
        if claim.claim_type == "sender_email":
            results.append(
                check_email_domain(claim, official_domain)
            )

        elif claim.claim_type == "fee_request":
            results.append(check_fee_request(claim))

    # Full offer text check
    text_claim = Claim(
        claim_id="FULL_TEXT",
        claim_type="offer_text",
        value=text,
    )

    results.append(check_urgency_channel(text_claim))

    # Offer structure check
    results.append(check_offer_consistency(text))

    has_fee_warning = any(
        result.check_name == "fee_detector"
        and result.verdict == Verdict.INCONSISTENT
        for result in results
    )

    safe_steps = [
        "Verify recruiter details through the official company website.",
        "Do not share Aadhaar, PAN, passwords or bank details.",
        "Review all inconsistent findings before accepting the offer.",
    ]

    if has_fee_warning:
        safe_steps.insert(
            0,
            "Do not pay recruitment fees without independent verification.",
        )

    return VerificationReport(
        report_id=str(uuid4()),
        claims=claims,
        checks=results,
        safe_steps=safe_steps,
    )

