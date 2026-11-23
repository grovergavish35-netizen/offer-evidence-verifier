
from unittest.mock import patch

import pytest

from core.domain_intelligence import (
    normalize_domain,
    check_recruiter_domain_intelligence,
)
from core.pipeline import verify_offer
from core.schemas import Claim, CheckResult, Verdict


def test_normal_domain():
    assert normalize_domain("example.com") == "example.com"


def test_subdomain():
    assert (
        normalize_domain("careers.example.co.uk")
        == "example.co.uk"
    )


def test_reject_url():
    with pytest.raises(ValueError):
        normalize_domain("https://example.com")


def test_reject_email():
    with pytest.raises(ValueError):
        normalize_domain("hr@example.com")


def test_reject_ip():
    with pytest.raises(ValueError):
        normalize_domain("192.168.1.1")


def test_reject_invalid_domain():
    with pytest.raises(ValueError):
        normalize_domain("not-a-domain")


def test_free_email_skips_network():
    with patch(
        "core.domain_intelligence.check_domain_age"
    ) as mock_check:

        result = check_recruiter_domain_intelligence(
            "hr@gmail.com"
        )

        assert result.verdict == Verdict.COULD_NOT_VERIFY
        mock_check.assert_not_called()


def test_domain_checker_receives_correct_arguments():
    fake_result = CheckResult(
        claim=Claim(
            claim_id="DOMAIN_INTEL",
            claim_type="recruiter_domain",
            value="hr@example.com",
        ),
        check_name="domain_age",
        finding="Mock registration evidence",
        source="Mock RDAP source",
        verdict=Verdict.COULD_NOT_VERIFY,
        confidence_note="Test result only.",
    )

    with patch(
        "core.domain_intelligence.check_domain_age",
        return_value=fake_result,
    ) as mock_check:

        result = check_recruiter_domain_intelligence(
            "hr@mail.example.com"
        )

        assert result.finding == "Mock registration evidence"
        assert mock_check.call_args.kwargs["domain"] == "example.com"


def test_pipeline_skips_network_by_default():
    with patch(
        "core.pipeline.check_recruiter_domain_intelligence"
    ) as mock_check:

        verify_offer(
            "Company: Example\nEmail: hr@example.com"
        )

        mock_check.assert_not_called()


def test_pipeline_runs_opt_in_check():
    fake_result = CheckResult(
        claim=Claim(
            claim_id="DOMAIN_INTEL",
            claim_type="recruiter_domain",
            value="hr@example.com",
        ),
        check_name="domain_age",
        finding="Mock RDAP finding",
        source="Mock RDAP source",
        verdict=Verdict.COULD_NOT_VERIFY,
        confidence_note="Test only.",
    )

    with patch(
        "core.pipeline.check_recruiter_domain_intelligence",
        return_value=fake_result,
    ) as mock_check:

        report = verify_offer(
            "Company: Example\nEmail: hr@example.com",
            enable_domain_intelligence=True,
        )

        mock_check.assert_called_once_with(
            "hr@example.com"
        )

        assert any(
            result.check_name == "domain_age"
            for result in report.checks
        )
