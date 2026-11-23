
from unittest.mock import patch

from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)
from core.pipeline import verify_offer
from checks.fee_detector import check_fee_request
from checks.urgency_channel import check_urgency_channel
from checks.domain_age import check_domain_age

def make_claim(text):
    return Claim(
        claim_id="TEST",
        claim_type="offer_text",
        value=text,
    )

def test_no_registration_fee():
    result = check_fee_request(
        make_claim("No registration fee required")
    )
    assert result.finding_type == FindingType.UNKNOWN

def test_fee_not_required():
    result = check_fee_request(
        make_claim("Registration fee is not required")
    )
    assert result.finding_type == FindingType.UNKNOWN

def test_positive_fee_request():
    result = check_fee_request(
        make_claim("Pay registration fee of Rs 2000")
    )
    assert result.finding_type == FindingType.RISK_SIGNAL
    assert result.verdict == Verdict.COULD_NOT_VERIFY

def test_security_deposit():
    result = check_fee_request(
        make_claim("Submit security deposit today")
    )
    assert result.finding_type == FindingType.RISK_SIGNAL

def test_whatsapp_is_risk_not_contradiction():
    result = check_urgency_channel(
        make_claim("Contact us on WhatsApp")
    )
    assert result.finding_type == FindingType.RISK_SIGNAL
    assert result.verdict == Verdict.COULD_NOT_VERIFY

def test_no_urgency():
    result = check_urgency_channel(
        make_claim("Your interview is scheduled")
    )
    assert result.finding_type == FindingType.UNKNOWN

def test_pipeline_fee_warning():
    report = verify_offer(
        "Company: Example Tech\n"
        "Role: Developer\n"
        "Pay registration fee of Rs 2000"
    )

    assert any(
        check.check_name == "fee_detector"
        and check.finding_type == FindingType.RISK_SIGNAL
        for check in report.checks
    )

def test_pipeline_no_fee_warning():
    report = verify_offer(
        "Company: Example Tech\n"
        "Role: Developer\n"
        "No registration fee required"
    )

    assert not any(
        check.check_name == "fee_detector"
        and check.finding_type == FindingType.RISK_SIGNAL
        for check in report.checks
    )

def test_new_domain_is_risk_signal():
    from datetime import datetime, timedelta, timezone

    recent_date = (
        datetime.now(timezone.utc) - timedelta(days=5)
    )

    with (
        patch(
            "checks.domain_age.get_registration_date",
            return_value=recent_date,
        ),
        patch(
            "checks.domain_age.get_mx_records",
            return_value=[],
        ),
    ):
        result = check_domain_age(
            make_claim("hr@example.com"),
            "example.com",
        )

    assert result.finding_type == FindingType.RISK_SIGNAL
    assert result.verdict == Verdict.COULD_NOT_VERIFY