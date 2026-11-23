
from core.pipeline import verify_offer
from core.schemas import Verdict


def test_full_pipeline():
    text = """
    Company: ABC Technologies
    Role: Software Developer Intern
    Email: hr@gmail.com
    Registration fee: Rs 1499
    """

    report = verify_offer(text, official_domain="example.com")

    assert len(report.claims) == 4
    assert len(report.checks) == 2

    assert all(
        result.verdict == Verdict.INCONSISTENT
        for result in report.checks
    )

    assert len(report.safe_steps) == 3


def test_unknown_domain():
    report = verify_offer(
        "Email: hr@unknown.com"
    )

    assert report.checks[0].verdict == (
        Verdict.COULD_NOT_VERIFY
    )
