
from datetime import datetime, timezone
from urllib.parse import urlparse

import dns.resolver
import requests

from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"

def normalize_domain(domain: str) -> str:
    return domain.strip().lower().rstrip(".")

def get_rdap_server(domain: str) -> str | None:
    tld = domain.rsplit(".", 1)[-1]

    response = requests.get(
        BOOTSTRAP_URL,
        timeout=8,
    )
    response.raise_for_status()

    data = response.json()

    for tlds, servers in data.get("services", []):
        if tld in [item.lower() for item in tlds]:
            for server in servers:
                parsed = urlparse(server)

                if (
                    parsed.scheme == "https"
                    and parsed.hostname
                    and not parsed.username
                    and not parsed.password
                ):
                    return server

    return None

def get_registration_date(domain: str):
    server = get_rdap_server(domain)

    if not server:
        return None

    url = server.rstrip("/") + "/domain/" + domain

    response = requests.get(
        url,
        timeout=8,
        headers={"Accept": "application/rdap+json"},
        allow_redirects=False,
    )
    response.raise_for_status()

    data = response.json()

    for event in data.get("events", []):
        if event.get("eventAction") == "registration":
            date_string = event.get("eventDate")

            if date_string:
                result = datetime.fromisoformat(
                    date_string.replace("Z", "+00:00")
                )

                if result.tzinfo is None:
                    result = result.replace(
                        tzinfo=timezone.utc
                    )

                return result

    return None

def get_mx_records(domain: str):
    try:
        answers = dns.resolver.resolve(
            domain,
            "MX",
            lifetime=5,
        )
        return [str(answer.exchange) for answer in answers]

    except dns.resolver.NoAnswer:
        return []

    except dns.exception.DNSException:
        return None

def check_domain_age(
    claim: Claim,
    domain: str,
) -> CheckResult:

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
            finding_type=FindingType.UNKNOWN,
            confidence_note="Domain could not be validated.",
        )

    try:
        registration_date = get_registration_date(domain)
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ):
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
            source=BOOTSTRAP_URL,
            verdict=Verdict.COULD_NOT_VERIFY,
            finding_type=FindingType.UNKNOWN,
            confidence_note=(
                "Registration evidence was unavailable. "
                "MX records do not authenticate the sender."
            ),
        )

    age_days = (
        datetime.now(timezone.utc) - registration_date
    ).days

    if age_days < 0:
        return CheckResult(
            claim=claim,
            check_name="domain_age",
            finding="Registration date is in the future.",
            source=BOOTSTRAP_URL,
            verdict=Verdict.COULD_NOT_VERIFY,
            finding_type=FindingType.UNKNOWN,
            confidence_note=(
                "Registration data requires manual review."
            ),
        )

    finding = (
        f"Domain {domain} registered on "
        f"{registration_date.date()}. "
        f"Age: {age_days} days. "
        f"MX records: {mx_records}"
    )

    if age_days < 30:
        finding_type = FindingType.RISK_SIGNAL
        note = (
            "Recently registered domain is a caution signal, "
            "not proof of fraud or a contradiction."
        )
    else:
        finding_type = FindingType.UNKNOWN
        note = (
            "Domain age alone cannot verify an offer "
            "or the sender's identity."
        )

    return CheckResult(
        claim=claim,
        check_name="domain_age",
        finding=finding,
        source=BOOTSTRAP_URL,
        verdict=Verdict.COULD_NOT_VERIFY,
        finding_type=finding_type,
        confidence_note=note,
    )

