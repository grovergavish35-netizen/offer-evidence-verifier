
from core.schemas import Claim, Verdict
from checks.email_domain import check_email_domain


def make_claim(email):
    return Claim(
        claim_id="C001",
        claim_type="sender_email",
        value=email,
    )


def test_matching_domain():
    result = check_email_domain(
        make_claim("hr@example.com"),
        "example.com",
    )
    assert result.verdict == Verdict.VERIFIED


def test_free_email_mismatch():
    result = check_email_domain(
        make_claim("hr@gmail.com"),
        "example.com",
    )
    assert result.verdict == Verdict.INCONSISTENT


def test_lookalike_domain():
    result = check_email_domain(
        make_claim("hr@examp1e.com"),
        "example.com",
    )
    assert result.verdict == Verdict.INCONSISTENT


def test_unknown_official_domain():
    result = check_email_domain(
        make_claim("hr@unknown.com"),
    )
    assert result.verdict == Verdict.COULD_NOT_VERIFY


def test_invalid_email():
    result = check_email_domain(
        make_claim("not-an-email"),
        "example.com",
    )
    assert result.verdict == Verdict.COULD_NOT_VERIFY
