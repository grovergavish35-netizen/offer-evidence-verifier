
from unittest.mock import patch

from core.pipeline import verify_offer
from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)

def find_check(report, name):
    """Find a verification check by its name."""

    matches = [
        result
        for result in report.checks
        if result.check_name == name
    ]

    available = [
        result.check_name
        for result in report.checks
    ]

    assert len(matches) == 1, (
        f"Expected one check named {name!r}. "
        f"Found {len(matches)}. "
        f"Available checks: {available}"
    )

    return matches[0]

def find_fee_check(report):
    """
    Find the fee detector result without assuming
    that its check_name is 'fee_request'.
    """

    matches = [
        result
        for result in report.checks
        if any(
            keyword in result.check_name.lower()
            for keyword in (
                "fee",
                "payment",
                "deposit",
            )
        )
    ]

    available = [
        result.check_name
        for result in report.checks
    ]

    assert len(matches) == 1, (
        "Expected exactly one fee-related check. "
        f"Found {len(matches)}. "
        f"Available checks: {available}"
    )

    return matches[0]

# -------------------------------------------
# Email domain reliability tests
# -------------------------------------------

def test_matching_recruiter_domain():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Software Intern\n"
            "Recruiter: hr@example.com\n"
        ),
        official_domain="example.com",
    )

    result = find_check(report, "email_domain")

    assert result.verdict == Verdict.VERIFIED
    assert (
        result.finding_type
        == FindingType.SUPPORTING_EVIDENCE
    )

def test_subdomain_is_supported():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Recruiter: hr@careers.example.com\n"
        ),
        official_domain="example.com",
    )

    result = find_check(report, "email_domain")

    assert result.verdict == Verdict.VERIFIED
    assert (
        result.finding_type
        == FindingType.SUPPORTING_EVIDENCE
    )

def test_lookalike_domain_is_contradiction():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Recruiter: hr@example.com.evil.org\n"
        ),
        official_domain="example.com",
    )

    result = find_check(report, "email_domain")

    assert result.verdict == Verdict.INCONSISTENT
    assert (
        result.finding_type
        == FindingType.CONTRADICTION
    )

def test_public_email_is_risk_not_contradiction():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Recruiter: recruiter@gmail.com\n"
        ),
        official_domain="example.com",
    )

    result = find_check(report, "email_domain")

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert (
        result.finding_type
        == FindingType.RISK_SIGNAL
    )

def test_missing_official_domain_is_unknown():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Recruiter: hr@example.com\n"
        )
    )

    result = find_check(report, "email_domain")

    assert (
        result.finding_type
        == FindingType.UNKNOWN
    )

# -------------------------------------------
# Urgency and communication tests
# -------------------------------------------

def test_negated_whatsapp_not_risk():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Software Intern\n"
            "No WhatsApp interviews are conducted.\n"
        )
    )

    result = find_check(
        report,
        "urgency_channel",
    )

    assert (
        result.finding_type
        == FindingType.UNKNOWN
    )

def test_affirmative_whatsapp_is_risk():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Contact HR on WhatsApp.\n"
        )
    )

    result = find_check(
        report,
        "urgency_channel",
    )

    assert (
        result.finding_type
        == FindingType.RISK_SIGNAL
    )

def test_immediate_payment_pressure():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Pay immediately to confirm your seat.\n"
        )
    )

    result = find_check(
        report,
        "urgency_channel",
    )

    assert (
        result.finding_type
        == FindingType.RISK_SIGNAL
    )

# -------------------------------------------
# Recruitment fee tests
# -------------------------------------------

def test_negated_fee_not_risk():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "No registration fee required.\n"
        )
    )

    result = find_fee_check(report)

    assert (
        result.finding_type
        != FindingType.RISK_SIGNAL
    ), (
        "A negated fee statement should not "
        "automatically generate a fee risk."
    )

def test_payment_request_is_risk():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Pay registration fee of Rs 2500.\n"
        )
    )

    result = find_fee_check(report)

    assert (
        result.finding_type
        == FindingType.RISK_SIGNAL
    ), (
        "An affirmative recruitment fee request "
        "should generate a risk signal."
    )

# -------------------------------------------
# Domain intelligence tests
# -------------------------------------------

def test_domain_intelligence_disabled_by_default():
    with patch(
        "core.pipeline.check_recruiter_domain_intelligence"
    ) as mock_intelligence:

        verify_offer(
            (
                "Company: Example Technologies\n"
                "Recruiter: hr@example.com\n"
            ),
            enable_domain_intelligence=False,
        )

        mock_intelligence.assert_not_called()

def test_domain_intelligence_enabled():
    fake_claim = Claim(
        claim_id="TEST_DOMAIN",
        claim_type="sender_email",
        value="hr@example.com",
    )

    fake_result = CheckResult(
        claim=fake_claim,
        check_name="domain_intelligence",
        finding="Domain intelligence unavailable.",
        source="Mock RDAP/DNS lookup",
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=FindingType.UNKNOWN,
        confidence_note="Network lookup not performed.",
    )

    with patch(
        "core.pipeline.check_recruiter_domain_intelligence",
        return_value=fake_result,
    ) as mock_intelligence:

        report = verify_offer(
            (
                "Company: Example Technologies\n"
                "Recruiter: hr@example.com\n"
            ),
            enable_domain_intelligence=True,
        )

        mock_intelligence.assert_called_once()

    assert any(
        result.check_name == "domain_intelligence"
        for result in report.checks
    )

# -------------------------------------------
# Safe steps and report structure
# -------------------------------------------

def test_safe_steps_generated():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Software Intern\n"
        )
    )

    assert report.safe_steps

    assert all(
        isinstance(step, str) and step.strip()
        for step in report.safe_steps
    )

def test_report_has_required_checks():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Recruiter: hr@example.com\n"
            "Role: Software Intern\n"
        ),
        official_domain="example.com",
    )

    check_names = {
        result.check_name
        for result in report.checks
    }

    assert "email_domain" in check_names
    assert "urgency_channel" in check_names

    assert any(
        any(
            keyword in name.lower()
            for keyword in ("fee", "payment", "deposit")
        )
        for name in check_names
    )

def test_report_has_unique_id():
    first = verify_offer(
        "Company: Example Technologies"
    )

    second = verify_offer(
        "Company: Example Technologies"
    )

    assert first.report_id
    assert second.report_id
    assert first.report_id != second.report_id