
from datetime import datetime, timezone
from urllib.parse import urlparse

import dns.resolver
import requests

from core.schemas import Claim, CheckResult, Verdict


BOOTSTRAP_URL = (
    "https://data.iana.org/rdap/dns.json"
)


def normalize_domain(domain: str) -> str:
    """Accept a bare domain and normalize its casing."""
    return domain.strip().lower().rstrip(".")


def get_rdap_server(domain: str) -> str | None:
    """Find the RDAP server for the domain's TLD."""
    tld = domain.rsplit(".", 1)[-1]

    response = requests.get(
        BOOTSTRAP_URL,
        timeout=8,
    )
    response.raise_for_status()

    data = response.json()

    for tlds, servers in data.get("services", []):
        if tld in [item.lower() for item in tlds]:
            if servers:
                return servers[0]

    return None


def get_registration_date(domain: str):
    """Read registration date from RDAP if available."""
    server = get_rdap_server(domain)

    if not server:
        return None

    # Only use HTTPS RDAP services.
    if urlparse(server).scheme != "https":
        return None

    url = server.rstrip("/") + "/domain/" + domain

    response = requests.get(
        url,
        timeout=8,
        headers={"Accept": "application/rdap+json"},
    )
    response.raise_for_status()

    data = response.json()

    for event in data.get("events", []):
        if event.get("eventAction") == "registration":
            date_string = event.get("eventDate")

            if date_string:
                return datetime.fromisoformat(
                    date_string.replace("Z", "+00:00")
                )

    return None


def get_mx_records(domain: str):
    """Return MX records, or None if lookup fails."""
    try:
        answers = dns.resolver.resolve(
            domain,
            "MX",
            lifetime=5,
        )
        return [str(answer.exchange) for answer in answers]

    except dns.resolver.NoAnswer:
        return []

    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.Timeout,
        dns.resolver.NoNameservers,
    ):
        return None


def check_domain_age(
    claim: Claim,
    domain: str,
) -> CheckResult:
    """Return evidence about domain registration and DNS."""
    domain = normalize_domain(domain)

    if (
        not domain
        or "/" in domain
        or "@" in domain
        or "." not in domain
    ):
        return CheckResult(
            claim=claim,
            check_name="domain_age",
            finding="Invalid domain input.",
            source=None,
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note="Domain could not be validated.",
        )

    try:
        registration_date = get_registration_date(domain)
    except (requests.RequestException, ValueError, KeyError):
        registration_date = None

    mx_records = get_mx_records(domain)

    if registration_date is None:
        return CheckResult(
            claim=claim,
            check_name="domain_age",
            finding=(
                f"Registration date unavailable for {domain}. "
                f"MX records: {mx_records}"
            ),
            source="https://lookup.icann.org/en",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "Registration data was unavailable. "
                "No domain-age conclusion can be made."
            ),
        )

    now = datetime.now(timezone.utc)
    age_days = (now - registration_date).days

    if age_days < 0:
        return CheckResult(
            claim=claim,
            check_name="domain_age",
            finding="Registration date is in the future.",
            source="https://lookup.icann.org/en",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note="Registration data is inconsistent.",
        )

    finding = (
        f"Domain {domain} registered on "
        f"{registration_date.date()}. "
        f"Age: {age_days} days. "
        f"MX records: {mx_records}"
    )

    if age_days < 30:
        verdict = Verdict.INCONSISTENT
        note = (
            "Recently registered domain is a risk signal, "
            "not proof of fraud."
        )
    else:
        verdict = Verdict.COULD_NOT_VERIFY
        note = (
            "Domain age alone cannot verify an offer "
            "or sender authenticity."
        )

    return CheckResult(
        claim=claim,
        check_name="domain_age",
        finding=finding,
        source="https://lookup.icann.org/en",
        verdict=verdict,
        confidence_note=note,
    )
