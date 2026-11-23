
from core.privacy import mask_sensitive_data


def test_mask_phone():
    text = "Contact: 9876543210"
    result = mask_sensitive_data(text)
    assert "9876543210" not in result


def test_mask_aadhaar_like():
    text = "Aadhaar: 1234 5678 9012"
    result = mask_sensitive_data(text)
    assert "1234 5678 9012" not in result


def test_mask_pan():
    text = "PAN: ABCDE1234F"
    result = mask_sensitive_data(text)
    assert "ABCDE1234F" not in result


def test_mask_bank_account():
    text = "Account Number: 123456789012"
    result = mask_sensitive_data(text)
    assert "123456789012" not in result


def test_preserve_offer_details():
    text = "Company: ABC Technologies\nRole: Developer Intern"
    assert mask_sensitive_data(text) == text
