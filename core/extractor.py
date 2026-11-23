
import re

from core.schemas import Claim


def extract_claims(text: str) -> list[Claim]:
    """
    Extract basic claims from an internship/job offer.

    This is a deterministic fallback extractor.
    No LLM or external API is used.
    """
    claims = []
    counter = 1

    def add_claim(claim_type: str, value: str, raw: str):
        nonlocal counter
        claims.append(
            Claim(
                claim_id=f"C{counter:03d}",
                claim_type=claim_type,
                value=value.strip(),
                raw_text=raw.strip(),
            )
        )
        counter += 1

    # Extract email addresses
    emails = re.findall(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )

    for email in dict.fromkeys(emails):
        add_claim("sender_email", email, email)

    # Extract company name from explicit labels
    company_match = re.search(
        r"(?:Company|Organization)\s*:\s*([^\n\r]+)",
        text,
        re.IGNORECASE,
    )

    if company_match:
        add_claim(
            "company_name",
            company_match.group(1),
            company_match.group(0),
        )

    # Extract role from explicit labels
    role_match = re.search(
        r"(?:Role|Position|Job Title)\s*:\s*([^\n\r]+)",
        text,
        re.IGNORECASE,
    )

    if role_match:
        add_claim(
            "role",
            role_match.group(1),
            role_match.group(0),
        )

    # Extract fee requests
    fee_pattern = (
        r"(?:registration fee|security deposit|training fee)"
        r"[^\n\r]{0,80}"
    )

    fee_match = re.search(
        fee_pattern,
        text,
        re.IGNORECASE,
    )

    if fee_match:
        add_claim(
            "fee_request",
            fee_match.group(0),
            fee_match.group(0),
        )

    return claims
