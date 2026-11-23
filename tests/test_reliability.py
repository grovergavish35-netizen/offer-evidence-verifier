
import pytest

from core.reliability import (
    EvidenceKind,
    normalize_domain,
    registrable_domain,
    compare_recruiter_domain,
    evaluate_recruitment_fee,
    evaluate_channel_pressure,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Example.COM", "example.com"),
        ("hr@example.com", "example.com"),
        ("https://careers.example.com/jobs", "careers.example.com"),
        ("example.com.", "example.com"),
        ("not-a-domain", None),
        ("https://example.com.evil.org", "example.com.evil.org"),
        ("https://user:pass@example.com", None),
        ("example.com:8080", None),
        ("", None),
    ],
)
def test_normalize_domain(value, expected):
    assert normalize_domain(value) == expected


def test_registrable_domain():
    assert (
        registrable_domain("careers.example.co.uk")
        == "example.co.uk"
    )


def test_exact_domain_match():
    result = compare_recruiter_domain(
        "hr@example.com",
        "example.com",
    )

    assert result.kind == EvidenceKind.SUPPORTING


def test_subdomain_match():
    result = compare_recruiter_domain(
        "hr@careers.example.com",
        "example.com",
    )

    assert result.kind == EvidenceKind.SUPPORTING


def test_different_domain():
    result = compare_recruiter_domain(
        "hr@fake-example.com",
        "example.com",
    )

    assert result.kind == EvidenceKind.CONTRADICTION


def test_lookalike_domain():
    result = compare_recruiter_domain(
        "hr@example.com.evil.org",
        "example.com",
    )

    assert result.kind == EvidenceKind.CONTRADICTION


def test_public_email_provider():
    result = compare_recruiter_domain(
        "recruiter@gmail.com",
        "example.com",
    )

    assert result.kind == EvidenceKind.RISK


def test_missing_official_domain():
    result = compare_recruiter_domain(
        "hr@example.com",
        None,
    )

    assert result.kind == EvidenceKind.UNKNOWN


def test_invalid_email():
    result = compare_recruiter_domain(
        "not-an-email",
        "example.com",
    )

    assert result.kind == EvidenceKind.UNKNOWN


@pytest.mark.parametrize(
    "text",
    [
        "No registration fee required.",
        "Registration fee is not required.",
        "We do not charge training fees.",
        "There is no security deposit.",
        "No payment is needed for joining.",
    ],
)
def test_negated_fees_are_not_risk(text):
    result = evaluate_recruitment_fee(text)

    assert result.kind == EvidenceKind.UNKNOWN


@pytest.mark.parametrize(
    "text",
    [
        "Pay registration fee of Rs 2000.",
        "Submit security deposit before joining.",
        "Transfer training fee today.",
        "Please pay processing fee.",
    ],
)
def test_affirmative_fee_requests_are_risk(text):
    result = evaluate_recruitment_fee(text)

    assert result.kind == EvidenceKind.RISK


def test_fee_mention_without_payment_request():
    result = evaluate_recruitment_fee(
        "Our recruitment fee policy is available online."
    )

    assert result.kind == EvidenceKind.UNKNOWN


def test_mixed_fee_statements():
    result = evaluate_recruitment_fee(
        "No registration fee required. "
        "Pay security deposit of Rs 3000."
    )

    assert result.kind == EvidenceKind.RISK


def test_whatsapp_mention():
    result = evaluate_channel_pressure(
        "Contact our recruiter on WhatsApp."
    )

    assert result.kind == EvidenceKind.RISK


def test_negated_whatsapp():
    result = evaluate_channel_pressure(
        "No WhatsApp interviews are conducted."
    )

    assert result.kind == EvidenceKind.UNKNOWN


def test_urgency():
    result = evaluate_channel_pressure(
        "Pay immediately to confirm your position."
    )

    assert result.kind == EvidenceKind.RISK


def test_no_urgency():
    result = evaluate_channel_pressure(
        "Your interview is scheduled for Monday."
    )

    assert result.kind == EvidenceKind.UNKNOWN


def test_sources_and_limitations_present():
    result = compare_recruiter_domain(
        "hr@fake-example.com",
        "example.com",
    )

    assert result.source.strip()
    assert result.limitation.strip()


def test_genuine_style_offer():
    text = (
        "Company: Example Technologies\n"
        "Role: Software Intern\n"
        "No registration fee required.\n"
        "No WhatsApp interviews are conducted."
    )

    assert (
        evaluate_recruitment_fee(text).kind
        == EvidenceKind.UNKNOWN
    )

    assert (
        evaluate_channel_pressure(text).kind
        == EvidenceKind.UNKNOWN
    )


def test_suspicious_style_offer():
    text = (
        "Company: Example Technologies\n"
        "Pay registration fee of Rs 2500 immediately.\n"
        "Contact HR on WhatsApp."
    )

    assert (
        evaluate_recruitment_fee(text).kind
        == EvidenceKind.RISK
    )

    assert (
        evaluate_channel_pressure(text).kind
        == EvidenceKind.RISK
    )
