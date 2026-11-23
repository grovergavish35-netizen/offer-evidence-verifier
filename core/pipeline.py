
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
    """
    Run explainable offer-evidence checks.

    Findings describe available evidence, not a
    definitive determination of fraud or authenticity.
    """

    claims = extract_claims(text)
    results = []

    # ----------------------------------------------
    # Recruiter email checks
    # ----------------------------------------------

    checked_emails = set()

    for claim in claims:
        if claim.claim_type != "sender_email":
            continue

        email = (claim.value or "").strip().lower()

        # Avoid duplicate checks for repeated addresses.
        if email in checked_emails:
            continue

        checked_emails.add(email)

        email_result = check_email_domain(
            claim,
            official_domain,
        )

        results.append(email_result)

        # Optional domain intelligence remains opt-in.
        if enable_domain_intelligence:
            domain_result = (
                check_recruiter_domain_intelligence(
                    claim.value
                )
            )

            # Domain age and network intelligence
            # cannot establish fraud by themselves.
            if domain_result.verdict == Verdict.INCONSISTENT:
                domain_result.verdict = (
                    Verdict.COULD_NOT_VERIFY
                )
                domain_result.finding_type = (
                    FindingType.RISK_SIGNAL
                )

            results.append(domain_result)

    # ----------------------------------------------
    # Full-text checks
    # ----------------------------------------------

    full_text_claim = Claim(
        claim_id="FULL_TEXT",
        claim_type="offer_text",
        value=text,
    )

    # Use full text so fee negations remain visible.
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

    # ----------------------------------------------
    # Safe guidance
    # ----------------------------------------------

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

    has_channel_warning = (
        urgency_result.finding_type
        == FindingType.RISK_SIGNAL
    )

    safe_steps = [
        (
            "Verify the employer using a website or "
            "telephone number found independently "
            "of the submitted offer."
        ),
        (
            "Do not share passwords, Aadhaar, PAN "
            "or banking details with unverified contacts."
        ),
        (
            "Review every finding in context. "
            "Risk signals do not prove fraud, and "
            "supporting checks do not certify authenticity."
        ),
    ]

    if has_domain_issue:
        safe_steps.insert(
            0,
            (
                "Confirm the recruiter's identity and "
                "authorization through an independently "
                "verified employer channel."
            ),
        )

    if has_channel_warning:
        safe_steps.insert(
            0,
            (
                "Confirm unusual communication requests "
                "and urgent deadlines through the "
                "employer's official recruitment channel."
            ),
        )

    if has_fee_warning:
        safe_steps.insert(
            0,
            (
                "Do not make recruitment-related payments "
                "until the request has been independently "
                "verified."
            ),
        )

    return VerificationReport(
        report_id=str(uuid4()),
        claims=claims,
        checks=results,
        safe_steps=safe_steps,
    )


