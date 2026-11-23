
from core.schemas import Claim, FindingType, Verdict
from checks.fee_detector import check_fee_request


def make_claim(text: str) -> Claim:
    return Claim(
        claim_id="FEE_TEST",
        claim_type="fee_request",
        value=text,
    )


def test_registration_fee():
    result = check_fee_request(
        make_claim("Pay registration fee of Rs 2000")
    )

    assert result.check_name == "fee_detector"
    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL


def test_security_deposit():
    result = check_fee_request(
        make_claim("Submit security deposit of Rs 5000")
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL


def test_training_fee():
    result = check_fee_request(
        make_claim("Pay training fee before joining")
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.RISK_SIGNAL


def test_no_registration_fee():
    result = check_fee_request(
        make_claim("No registration fee required")
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN


def test_fee_not_required():
    result = check_fee_request(
        make_claim("Registration fee is not required")
    )

    assert result.finding_type == FindingType.UNKNOWN


def test_no_fee_mentioned():
    result = check_fee_request(
        make_claim("Your interview is scheduled tomorrow")
    )

    assert result.verdict == Verdict.COULD_NOT_VERIFY
    assert result.finding_type == FindingType.UNKNOWN


def test_mixed_fee_statements():
    result = check_fee_request(
        make_claim(
            "No registration fee required. "
            "Pay security deposit of Rs 3000."
        )
    )

    assert result.finding_type == FindingType.RISK_SIGNAL

