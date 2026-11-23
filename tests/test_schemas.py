
from core.schemas import (
    Claim,
    CheckResult,
    VerificationReport,
    Verdict,
)


def test_verification_report():
    claim = Claim(
        claim_id="C001",
        claim_type="registration_fee",
        value="1499 INR",
        raw_text="Pay Rs 1499 registration fee",
    )

    check = CheckResult(
        claim=claim,
        check_name="fee_detector",
        finding="Registration fee requested",
        source="Submitted offer text",
        verdict=Verdict.INCONSISTENT,
        confidence_note=(
            "Fee request is a risk signal, not proof of fraud."
        ),
    )

    report = VerificationReport(
        report_id="R001",
        claims=[claim],
        checks=[check],
        safe_steps=["Do not pay before independent verification"],
    )

    assert report.checks[0].verdict == Verdict.INCONSISTENT
    assert report.claims[0].claim_id == "C001"
    assert len(report.safe_steps) == 1
