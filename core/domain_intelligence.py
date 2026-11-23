
import ipaddress
import re

import tldextract

from core.schemas import Claim, CheckResult, Verdict
from checks.domain_age import check_domain_age

# ==========================================
# CONFIGURATION
# ==========================================

EXTRACTOR = tldextract.TLDExtract(
    suffix_list_urls=()
)

DOMAIN_RE = re.compile(
    r"^[a-z0-9.-]+$",
    re.IGNORECASE,
)

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "rediffmail.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
}

# ==========================================
# DOMAIN VALIDATION
# ==========================================

def normalize_domain(value: str) -> str:
    """
    Validate a domain and return its
    registrable domain.

    Example:
    careers.example.co.uk -> example.co.uk
    """

    value = value.strip().lower().rstrip(".")

    if not value:
        raise ValueError("Domain is empty.")

    if len(value) > 253:
        raise ValueError("Domain is too long.")

    if not DOMAIN_RE.fullmatch(value):
        raise ValueError("Invalid domain format.")

    try:
        ipaddress.ip_address(value)

    except ValueError:
        pass

    else:
        raise ValueError(
            "IP addresses are not supported."
        )

    labels = value.split(".")

    for label in labels:
        if (
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
        ):
            raise ValueError("Invalid domain labels.")

    extracted = EXTRACTOR(value)

    if not extracted.domain or not extracted.suffix:
        raise ValueError(
            "A public registrable domain is required."
        )

    return (
        f"{extracted.domain}."
        f"{extracted.suffix}"
    )

# ==========================================
# DOMAIN INTELLIGENCE
# ==========================================

def check_recruiter_domain_intelligence(
    email: str,
) -> CheckResult:
    """
    Analyze the registrable domain of a
    recruiter email using RDAP and DNS.

    Free email providers are skipped because
    their domain age cannot establish the
    identity of an individual recruiter.
    """

    claim = Claim(
        claim_id="DOMAIN_INTEL",
        claim_type="recruiter_domain",
        value=email,
    )

    email = email.strip().lower()

    # --------------------------------------
    # EMAIL VALIDATION
    # --------------------------------------

    if not re.fullmatch(
        r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
        email,
    ):
        return CheckResult(
            claim=claim,
            check_name="domain_intelligence",
            finding="Invalid recruiter email.",
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "Domain intelligence was not performed."
            ),
        )

    # --------------------------------------
    # EXTRACT REGISTRABLE DOMAIN
    # --------------------------------------

    try:
        email_domain = email.rsplit("@", 1)[1]

        domain = normalize_domain(
            email_domain
        )

    except ValueError as exc:
        return CheckResult(
            claim=claim,
            check_name="domain_intelligence",
            finding=str(exc),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "Recruiter domain could not be validated."
            ),
        )

    # --------------------------------------
    # SKIP FREE EMAIL PROVIDERS
    # --------------------------------------

    if domain in FREE_EMAIL_DOMAINS:
        return CheckResult(
            claim=claim,
            check_name="domain_intelligence",
            finding=(
                f"{domain} is a shared email provider. "
                "Its registration age cannot establish "
                "whether the recruiter is legitimate."
            ),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "No RDAP/DNS lookup was performed. "
                "Verify the recruiter directly through "
                "the company's official contact channel."
            ),
        )

    # --------------------------------------
    # PERFORM RDAP + DNS CHECK
    # --------------------------------------

    try:
        result = check_domain_age(
            claim=claim,
            domain=domain,
        )

        return result

    except Exception:
        return CheckResult(
            claim=claim,
            check_name="domain_intelligence",
            finding=(
                f"Domain intelligence unavailable "
                f"for {domain}."
            ),
            source=None,
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "External lookup failed. "
                "No authenticity conclusion can be made."
            ),
        )