
from core.schemas import Claim, Verdict
from checks.fee_detector import check_fee_request


def make_claim(text):
    return Claim(
        claim_id="C002",
        claim_type="fee_request",
        value=text,
    )


def test_registration_fee():
    result = check_fee_request(
        make_claim("Registration fee: Rs 1499")
    )
    assert result.verdict == Verdict.INCONSISTENT


def test_security_deposit():
    result = check_fee_request(
        make_claim("Pay security deposit of Rs 5000")
    )
    assert result.verdict == Verdict.INCONSISTENT


def test_training_fee():
    result = check_fee_request(
        make_claim("Training fee is mandatory")
    )
    assert result.verdict == Verdict.INCONSISTENT


def test_unclear_payment():
    result = check_fee_request(
        make_claim("Payment details will be shared later")
    )
    assert result.verdict == Verdict.COULD_NOT_VERIFY


def test_no_fee():
    result = check_fee_request(
        make_claim("Internship stipend is Rs 25000")
    )
    assert result.verdict == Verdict.COULD_NOT_VERIFY
