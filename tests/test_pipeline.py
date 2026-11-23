
from core.pipeline import verify_offer
from core.schemas import FindingType, Verdict

EXPECTED_CHECKS = {
    "email_domain",
    "fee_detector",
    "urgency_channel",
    "offer_consistency",
}

def test_full_pipeline():
    text = """
Company: ABC Technologies
Role: Software Developer Intern
Email: hr@gmail.com
Registration fee: Rs 1499
Pay within 24 hours.
"""

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    assert len(report.claims) == 4
    assert len(report.checks) == 4

    check_names = {
        result.check_name
        for result in report.checks
    }

    assert check_names == EXPECTED_CHECKS

    email_result = next(
        result
        for result in report.checks
        if result.check_name == "email_domain"
    )

    assert email_result.verdict == Verdict.COULD_NOT_VERIFY
    assert email_result.finding_type == FindingType.RISK_SIGNAL

    fee_result = next(
        result
        for result in report.checks
        if result.check_name == "fee_detector"
    )

    assert fee_result.finding_type == FindingType.RISK_SIGNAL

    assert report.safe_steps

def test_pipeline_detects_lookalike_domain():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Developer Intern\n"
            "Email: hr@examp1e.com\n"
        ),
        official_domain="example.com",
    )

    email_results = [
        result
        for result in report.checks
        if result.check_name == "email_domain"
    ]

    assert len(email_results) == 1

    result = email_results[0]

    assert result.verdict == Verdict.INCONSISTENT
    assert result.finding_type == FindingType.CONTRADICTION

def test_pipeline_matching_domain():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Developer Intern\n"
            "Email: hr@example.com\n"
        ),
        official_domain="example.com",
    )

    email_result = next(
        result
        for result in report.checks
        if result.check_name == "email_domain"
    )

    assert email_result.verdict == Verdict.VERIFIED
    assert (
        email_result.finding_type
        == FindingType.SUPPORTING_EVIDENCE
    )

def test_pipeline_without_official_domain():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Developer Intern\n"
            "Email: hr@example.com\n"
        )
    )

    email_result = next(
        result
        for result in report.checks
        if result.check_name == "email_domain"
    )

    assert email_result.verdict == Verdict.COULD_NOT_VERIFY
    assert email_result.finding_type == FindingType.UNKNOWN

def test_pipeline_safe_steps():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Role: Developer Intern\n"
            "Email: recruiter@gmail.com\n"
            "Pay registration fee of Rs 2500.\n"
        ),
        official_domain="example.com",
    )

    assert report.safe_steps

    assert any(
        "payment" in step.lower()
        or "fees" in step.lower()
        for step in report.safe_steps
    )

def test_pipeline_report_id_unique():
    first = verify_offer(
        "Company: Example Technologies"
    )

    second = verify_offer(
        "Company: Example Technologies"
    )

    assert first.report_id != second.report_id

def test_pipeline_has_no_false_authenticity_claim():
    report = verify_offer(
        (
            "Company: Example Technologies\n"
            "Email: hr@example.com\n"
        ),
        official_domain="example.com",
    )

    assert report.disclaimer

    assert any(
        result.check_name == "email_domain"
        and result.finding_type
        == FindingType.SUPPORTING_EVIDENCE
        for result in report.checks
    )

