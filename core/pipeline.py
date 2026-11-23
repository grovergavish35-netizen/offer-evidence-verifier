
from uuid import uuid4

from core.extractor import extract_claims
from core.schemas import (
    Claim,
    FindingType,
    VerificationReport,
    Verdict,
)

from checks.email_domain import check_email_domain
from checks.fee_detector import check_fee_request
from checks.urgency_channel import check_urgency_channel
from checks.offer_consistency import check_offer_consistency

from core.domain_intelligence import (
    check_recruiter_domain_intelligence,
)

def verify_offer(
    text: str,
    official_domain: str | None = None,
    enable_domain_intelligence: bool = False,
) -> VerificationReport:

    claims = extract_claims(text)
    results = []

    for claim in claims:
        if claim.claim_type == "sender_email":
            email_result = check_email_domain(
                claim,
                official_domain,
            )

            # A matching reference domain is limited
            # supporting evidence, not proof of authenticity.
            if email_result.verdict == Verdict.VERIFIED:
                email_result.finding_type = (
                    FindingType.SUPPORTING_EVIDENCE
                )
            elif email_result.verdict == Verdict.INCONSISTENT:
                email_result.finding_type = (
                    FindingType.CONTRADICTION
                )

            results.append(email_result)

            if enable_domain_intelligence:
                domain_result = (
                    check_recruiter_domain_intelligence(
                        claim.value
                    )
                )

                # Young domain = risk signal,
                # not a contradiction.
                if domain_result.verdict == Verdict.INCONSISTENT:
                    domain_result.verdict = (
                        Verdict.COULD_NOT_VERIFY
                    )
                    domain_result.finding_type = (
                        FindingType.RISK_SIGNAL
                    )

                results.append(domain_result)

    full_text_claim = Claim(
        claim_id="FULL_TEXT",
        claim_type="offer_text",
        value=text,
    )

    fee_result = check_fee_request(full_text_claim)
    results.append(fee_result)

    urgency_result = check_urgency_channel(
        full_text_claim
    )
    results.append(urgency_result)

    consistency_result = check_offer_consistency(text)

    if consistency_result.verdict == Verdict.INCONSISTENT:
        consistency_result.finding_type = (
            FindingType.CONTRADICTION
        )

    results.append(consistency_result)

    has_fee_warning = (
        fee_result.finding_type == FindingType.RISK_SIGNAL
    )

    has_domain_issue = any(
        result.check_name in (
            "email_domain",
            "domain_age",
            "domain_intelligence",
        )
        and result.finding_type in (
            FindingType.RISK_SIGNAL,
            FindingType.CONTRADICTION,
        )
        for result in results
    )

    safe_steps = [
        (
            "Verify the employer through a website or "
            "phone number found independently."
        ),
        (
            "Do not share passwords, Aadhaar, PAN "
            "or bank details with unverified contacts."
        ),
        (
            "Review each finding in context. "
            "Warning signals do not prove fraud."
        ),
    ]

    if has_domain_issue:
        safe_steps.insert(
            0,
            (
                "Confirm the recruiter through the "
                "employer's independently verified channel."
            ),
        )

    if has_fee_warning:
        safe_steps.insert(
            0,
            (
                "Do not pay recruitment fees until "
                "the request is independently verified."
            ),
        )

    return VerificationReport(
        report_id=str(uuid4()),
        claims=claims,
        checks=results,
        safe_steps=safe_steps,
    )


