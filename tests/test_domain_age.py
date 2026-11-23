
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from core.schemas import Claim, Verdict
from checks.domain_age import check_domain_age


def make_claim():
    return Claim(
        claim_id="C003",
        claim_type="sender_email",
        value="hr@example.com",
    )


@patch("checks.domain_age.get_mx_records")
@patch("checks.domain_age.get_registration_date")
def test_recent_domain(mock_date, mock_mx):
    mock_date.return_value = (
        datetime.now(timezone.utc) - timedelta(days=10)
    )
    mock_mx.return_value = ["mail.example.com"]

    result = check_domain_age(
        make_claim(),
        "example.com",
    )

    assert result.verdict == Verdict.INCONSISTENT


@patch("checks.domain_age.get_mx_records")
@patch("checks.domain_age.get_registration_date")
def test_old_domain(mock_date, mock_mx):
    mock_date.return_value = (
        datetime.now(timezone.utc) - timedelta(days=1000)
    )
    mock_mx.return_value = ["mail.example.com"]

    result = check_domain_age(
        make_claim(),
        "example.com",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY


@patch("checks.domain_age.get_mx_records")
@patch("checks.domain_age.get_registration_date")
def test_missing_registration(mock_date, mock_mx):
    mock_date.return_value = None
    mock_mx.return_value = None

    result = check_domain_age(
        make_claim(),
        "example.com",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY


def test_invalid_domain():
    result = check_domain_age(
        make_claim(),
        "not-a-domain",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
