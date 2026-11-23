
from core.extractor import extract_claims


def test_extract_claims():
    text = """
    Company: ABC Technologies
    Role: Software Developer Intern
    Email: hr.abc.recruitment@gmail.com
    Registration fee: Rs 1499
    """

    claims = extract_claims(text)

    claim_types = [claim.claim_type for claim in claims]

    assert "sender_email" in claim_types
    assert "company_name" in claim_types
    assert "role" in claim_types
    assert "fee_request" in claim_types

    assert len(claims) == 4
