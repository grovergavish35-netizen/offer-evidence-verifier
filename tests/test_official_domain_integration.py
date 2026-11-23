
from core.pipeline import verify_offer
from core.schemas import FindingType, Verdict

def get_email_result(report):
    matches = [
        result
        for result in report.checks
        if result.check_name == "email_domain"
    ]

    assert len(matches) == 1
    return matches[0]

def test_matching_official_domain():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@example.com"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    result = get_email_result(report)

    assert result.verdict == Verdict.VERIFIED
    assert result.finding_type == FindingType.SUPPORTING_EVIDENCE

def test_mismatched_official_domain():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@examp1e.com"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    result = get_email_result(report)

    assert result.verdict == Verdict.INCONSISTENT
    assert result.finding_type == FindingType.CONTRADICTION
    assert (
        "does not match" in result.finding.lower()
        or "differs" in result.finding.lower()
    )

def test_missing_official_domain():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@example.com"
    )

    report = verify_offer(text)

    result = get_email_result(report)

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN

def test_free_email_provider_mismatch():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: recruiter@gmail.com"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    result = get_email_result(report)

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL

def test_subdomain_of_official_domain():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@careers.example.com"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    result = get_email_result(report)

    assert result.verdict == Verdict.VERIFIED
    assert result.finding_type == FindingType.SUPPORTING_EVIDENCE

def test_lookalike_subdomain():
    text = (
        "Company: Example Technologies\n"
        "Role: Developer Intern\n"
        "Email: hr@example.com.evil.org"
    )

    report = verify_offer(
        text,
        official_domain="example.com",
    )

    result = get_email_result(report)

    assert result.verdict == Verdict.INCONSISTENT
    assert result.finding_type == FindingType.CONTRADICTION
