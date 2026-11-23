
from core.schemas import Verdict
from checks.offer_consistency import check_offer_consistency


def test_missing_fields():
    text = """
    Company: ABC Technologies
    Role: Software Developer Intern
    """

    result = check_offer_consistency(text)

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert "joining_date" in result.finding


def test_conflicting_company_names():
    text = """
    Company: ABC Technologies
    Company: XYZ Solutions
    Role: Software Developer Intern
    """

    result = check_offer_consistency(text)

    assert result.verdict == Verdict.INCONSISTENT
    assert "company" in result.finding


def test_complete_offer_structure():
    text = """
    Company: ABC Technologies
    Role: Software Developer Intern
    Joining Date: 15 December 2026
    Department: Engineering
    Reporting Manager: Rahul Sharma
    """

    result = check_offer_consistency(text)

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert "All configured fields" in result.finding


def test_duplicate_same_company():
    text = """
    Company: ABC Technologies
    Company: ABC Technologies
    Role: Software Developer Intern
    """

    result = check_offer_consistency(text)

    assert result.verdict == Verdict.COULD_NOT_VERIFY
