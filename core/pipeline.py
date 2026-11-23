
from uuid import uuid4

from core.extractor import extract_claims
from core.schemas import VerificationReport
from checks.email_domain import check_email_domain
from checks.fee_detector import check_fee_request


def verify_offer(
    text: str,
    official_domain: str | None = None,
) -> VerificationReport:
    """
    Run deterministic verification checks on offer text.

    official_domain must be independently verified.
    Never derive it from the submitted offer itself.
    """
    claims = extract_claims(text)
    results = []

    for claim in claims:
        if claim.claim_type == "sender_email":
            results.append(
                check_email_domain(claim, official_domain)
            )

        elif claim.claim_type == "fee_request":
            results.append(check_fee_request(claim))

    return VerificationReport(
        report_id=str(uuid4()),
        claims=claims,
        checks=results,
        safe_steps=[
            "Do not pay recruitment or registration fees "
            "before independent verification.",
            "Do not share Aadhaar, PAN, bank details or "
            "other sensitive documents yet.",
            "Contact the company using contact details "
            "from its independently verified website.",
        ],
    )
