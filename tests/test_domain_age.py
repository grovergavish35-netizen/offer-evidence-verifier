
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from core.schemas import Claim, FindingType, Verdict
from checks.domain_age import check_domain_age


def make_claim() -> Claim:
    return Claim(
        claim_id="DOMAIN_TEST",
        claim_type="recruiter_domain",
        value="hr@example.com",
    )


def test_recent_domain():
    registration_date = (
        datetime.now(timezone.utc) - timedelta(days=5)
    )

    with (
        patch(
            "checks.domain_age.get_registration_date",
            return_value=registration_date,
        ),
        patch(
            "checks.domain_age.get_mx_records",
            return_value=["mail.example.com."],
        ),
    ):
        result = check_domain_age(
            make_claim(),
            "example.com",
        )

    assert result.check_name == "domain_age"
    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL
    assert "example.com" in result.finding


def test_old_domain():
    registration_date = (
        datetime.now(timezone.utc) - timedelta(days=365)
    )

    with (
        patch(
            "checks.domain_age.get_registration_date",
            return_value=registration_date,
        ),
        patch(
            "checks.domain_age.get_mx_records",
            return_value=[],
        ),
    ):
        result = check_domain_age(
            make_claim(),
            "example.com",
        )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN


def test_registration_date_unavailable():
    with (
        patch(
            "checks.domain_age.get_registration_date",
            return_value=None,
        ),
        patch(
            "checks.domain_age.get_mx_records",
            return_value=None,
        ),
    ):
        result = check_domain_age(
            make_claim(),
            "example.com",
        )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN
    assert "unavailable" in result.finding.lower()


def test_invalid_domain():
    result = check_domain_age(
        make_claim(),
        "invalid-domain",
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN


def test_future_registration_date():
    registration_date = (
        datetime.now(timezone.utc) + timedelta(days=10)
    )

    with (
        patch(
            "checks.domain_age.get_registration_date",
            return_value=registration_date,
        ),
        patch(
            "checks.domain_age.get_mx_records",
            return_value=[],
        ),
    ):
        result = check_domain_age(
            make_claim(),
            "example.com",
        )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN

