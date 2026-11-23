
from core.schemas import Claim, FindingType, Verdict
from checks.email_domain import check_email_domain

def make_email_claim(email):
    return Claim(
        claim_id="TEST_EMAIL",
        claim_type="sender_email",
        value=email,
    )

def test_matching_email_domain():
    result = check_email_domain(
        make_email_claim("hr@example.com"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.VERIFIED
    assert result.finding_type == FindingType.SUPPORTING_EVIDENCE

def test_matching_subdomain():
    result = check_email_domain(
        make_email_claim("hr@careers.example.com"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.VERIFIED
    assert result.finding_type == FindingType.SUPPORTING_EVIDENCE

def test_mismatched_domain():
    result = check_email_domain(
        make_email_claim("hr@examp1e.com"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.INCONSISTENT
    assert result.finding_type == FindingType.CONTRADICTION

def test_free_email_mismatch():
    result = check_email_domain(
        make_email_claim("recruiter@gmail.com"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL

def test_missing_official_domain():
    result = check_email_domain(
        make_email_claim("hr@example.com"),
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN

def test_invalid_email():
    result = check_email_domain(
        make_email_claim("not-an-email"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN

def test_invalid_official_domain():
    result = check_email_domain(
        make_email_claim("hr@example.com"),
        official_domain="not-a-domain",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN

def test_lookalike_domain():
    result = check_email_domain(
        make_email_claim("hr@example.com.evil.org"),
        official_domain="example.com",
    )

    assert result.verdict == Verdict.INCONSISTENT
    assert result.finding_type == FindingType.CONTRADICTION
