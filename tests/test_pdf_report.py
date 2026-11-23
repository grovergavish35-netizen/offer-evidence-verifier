
from datetime import datetime, timezone
from io import BytesIO

import pdfplumber
import pytest

from core.pdf_report import generate_evidence_pdf
from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    VerificationReport,
    Verdict,
)


def sample_report():
    claim = Claim(
        claim_id="TEST_1",
        claim_type="fee_request",
        value="Pay registration fee of Rs 2000",
    )

    check = CheckResult(
        claim=claim,
        check_name="fee_detector",
        finding=(
            "Potential recruitment payment request detected."
        ),
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=FindingType.RISK_SIGNAL,
        confidence_note=(
            "Payment request is a caution signal."
        ),
    )

    return VerificationReport(
        report_id="TEST-REPORT-001",
        created_at=datetime(
            2026, 11, 23, 12, 0,
            tzinfo=timezone.utc,
        ),
        claims=[claim],
        checks=[check],
        safe_steps=[
            "Verify the employer independently.",
            "Do not pay recruitment fees without verification.",
        ],
    )


def extract_text(pdf_bytes):
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        return "\n".join(
            page.extract_text() or ""
            for page in pdf.pages
        )


def test_pdf_has_valid_signature():
    result = generate_evidence_pdf(sample_report())

    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF-")
    assert len(result) > 1000


def test_pdf_contains_report_id():
    result = generate_evidence_pdf(sample_report())
    text = extract_text(result)

    assert "TEST-REPORT-001" in text


def test_pdf_contains_finding():
    result = generate_evidence_pdf(sample_report())
    text = extract_text(result)

    assert "Potential recruitment payment" in text
    assert "Risk Signal" in text


def test_pdf_contains_safe_steps():
    result = generate_evidence_pdf(sample_report())
    text = extract_text(result)

    assert "Verify the employer independently" in text


def test_pdf_contains_disclaimer():
    result = generate_evidence_pdf(sample_report())
    text = extract_text(result)

    assert "decision support" in text.lower()


def test_pdf_masks_phone_number():
    report = sample_report()

    report.checks[0].finding = (
        "Recruiter phone: 9876543210"
    )

    result = generate_evidence_pdf(report)
    text = extract_text(result)

    assert "9876543210" not in text
    assert "PHONE REDACTED" in text


def test_pdf_handles_empty_checks():
    report = VerificationReport(
        report_id="EMPTY-001",
        claims=[],
        checks=[],
        safe_steps=[],
    )

    result = generate_evidence_pdf(report)
    text = extract_text(result)

    assert "No checks were available" in text


def test_pdf_rejects_invalid_input():
    with pytest.raises(TypeError):
        generate_evidence_pdf({"report_id": "wrong"})


def test_pdf_handles_special_characters():
    report = sample_report()

    report.checks[0].finding = (
        "Company <Example> & recruiter verification"
    )

    result = generate_evidence_pdf(report)
    text = extract_text(result)

    assert "recruiter verification" in text


def test_pdf_multiple_pages():
    report = sample_report()

    original = report.checks[0]

    report.checks = [
        original.model_copy(
            update={
                "finding": (
                    f"Finding number {index}: "
                    "Manual verification is required."
                )
            }
        )
        for index in range(35)
    ]

    result = generate_evidence_pdf(report)

    with pdfplumber.open(BytesIO(result)) as pdf:
        assert len(pdf.pages) > 1
