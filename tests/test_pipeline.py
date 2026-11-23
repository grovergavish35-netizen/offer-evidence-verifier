from core.pipeline import verify_offer
from core.schemas import Verdict


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
        result.check_name for result in report.checks
    }

    assert check_names == {
        "email_domain",
        "fee_detector",
        "urgency_channel",
        "offer_consistency",
    }

    assert any(
        result.verdict == Verdict.INCONSISTENT
        for result in report.checks
    )


def test_unknown_domain():
    report = verify_offer("Email: hr@unknown.com")

    email_result = next(
        result for result in report.checks
        if result.check_name == "email_domain"
    )

    assert email_result.verdict == Verdict.COULD_NOT_VERIFY


def test_no_false_authentication():
    text = """
    Company: ABC Technologies
    Role: Software Developer Intern
    Joining Date: 15 December 2026
    Department: Engineering
    Reporting Manager: Rahul Sharma
    """

    report = verify_offer(text)

    structure_result = next(
        result for result in report.checks
        if result.check_name == "offer_consistency"
    )

    assert structure_result.verdict == Verdict.COULD_NOT_VERIFY

