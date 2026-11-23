
import re


def mask_sensitive_data(text: str) -> str:
    """Mask common Indian personal identifiers."""

    # Aadhaar-like 12-digit numbers
    text = re.sub(
        r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)",
        "[AADHAAR-LIKE NUMBER REDACTED]",
        text,
    )

    # PAN-like identifiers
    text = re.sub(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        "[PAN-LIKE NUMBER REDACTED]",
        text,
        flags=re.IGNORECASE,
    )

    # Indian mobile numbers
    text = re.sub(
        r"(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{9}(?!\d)",
        "[PHONE REDACTED]",
        text,
    )

    # Explicitly labeled bank account numbers
    text = re.sub(
        r"(?i)\b(account\s*(?:number|no\.?|#)\s*:\s*)\d{9,18}\b",
        r"\1[BANK ACCOUNT REDACTED]",
        text,
    )

    return text
