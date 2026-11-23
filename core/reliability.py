
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlsplit

import tldextract


class EvidenceKind(str, Enum):
    SUPPORTING = "supporting_evidence"
    CONTRADICTION = "contradiction"
    RISK = "risk_signal"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Evidence:
    check_name: str
    kind: EvidenceKind
    finding: str
    source: str
    limitation: str


_EXTRACTOR = tldextract.TLDExtract(
    suffix_list_urls=()
)

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
    "rediffmail.com",
}

FEE_PATTERN = re.compile(
    r"\b(?:registration|training|processing|"
    r"joining|onboarding)\s+fees?\b"
    r"|\bsecurity\s+deposit\b",
    re.IGNORECASE,
)

PAYMENT_ACTION = re.compile(
    r"\b(?:pay|send|transfer|deposit|submit|"
    r"make\s+(?:a\s+)?payment|"
    r"payment\s+(?:is\s+)?required)\b",
    re.IGNORECASE,
)

NEGATION_BEFORE = re.compile(
    r"\b(?:no|never|without|zero|"
    r"do\s+not|don't|not\s+required)\b",
    re.IGNORECASE,
)

NEGATION_AFTER = re.compile(
    r"^\s*(?:is\s+|are\s+|will\s+be\s+)?"
    r"(?:not\s+required|not\s+charged|"
    r"waived|prohibited|forbidden)",
    re.IGNORECASE,
)

CHANNEL_PATTERN = re.compile(
    r"\b(?:whatsapp|telegram)\b",
    re.IGNORECASE,
)

CHANNEL_NEGATION = re.compile(
    r"\b(?:do\s+not|don't|never|no|"
    r"without|not\s+through|not\s+via)\b",
    re.IGNORECASE,
)

URGENCY_PATTERN = re.compile(
    r"\b(?:pay\s+(?:now|immediately|today)|"
    r"transfer\s+(?:now|immediately|today)|"
    r"limited\s+time|"
    r"within\s+24\s+hours|"
    r"offer\s+expires\s+(?:today|tomorrow))\b",
    re.IGNORECASE,
)


def normalize_domain(value: Optional[str]) -> Optional[str]:
    """
    Accepts a domain, email or HTTP(S) URL.

    Returns a normalized hostname.

    Rejects:
    - URLs containing usernames or passwords
    - Unsupported URL schemes
    - Explicit ports in plain domain inputs
    - Invalid domain syntax
    """

    if not value or not isinstance(value, str):
        return None

    candidate = value.strip().lower()

    if not candidate:
        return None

    if any(char.isspace() for char in candidate):
        return None

    # IMPORTANT:
    # Parse URLs before checking for email addresses.
    # Otherwise user:pass@example.com inside a URL
    # could be incorrectly interpreted as an email.

    if "://" in candidate:
        try:
            parsed = urlsplit(candidate)

            if parsed.scheme not in ("http", "https"):
                return None

            if parsed.username is not None:
                return None

            if parsed.password is not None:
                return None

            if not parsed.hostname:
                return None

            candidate = parsed.hostname

        except ValueError:
            return None

    elif "@" in candidate:
        # Treat as an email address only if it has
        # exactly one @ and no URL-like path.

        if candidate.count("@") != 1:
            return None

        local_part, domain_part = candidate.rsplit(
            "@", 1
        )

        if not local_part or not domain_part:
            return None

        if any(
            char in candidate
            for char in ("/", "\\", "?", "#")
        ):
            return None

        candidate = domain_part

    else:
        # Plain domain or domain/path input.
        candidate = candidate.split("/", 1)[0]

        if ":" in candidate:
            return None

        if any(
            char in candidate
            for char in ("?", "#", "\\")
        ):
            return None

    candidate = candidate.rstrip(".")

    if not candidate or len(candidate) > 253:
        return None

    labels = candidate.split(".")

    if len(labels) < 2:
        return None

    for label in labels:
        if not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
            label,
        ):
            return None

    extracted = _EXTRACTOR(candidate)

    if not extracted.domain or not extracted.suffix:
        return None

    return candidate


def registrable_domain(hostname: str) -> Optional[str]:
    normalized = normalize_domain(hostname)

    if not normalized:
        return None

    extracted = _EXTRACTOR(normalized)

    if not extracted.domain or not extracted.suffix:
        return None

    return (
        f"{extracted.domain}.{extracted.suffix}"
    )


def compare_recruiter_domain(
    recruiter_email: str,
    official_domain: Optional[str],
) -> Evidence:

    source = (
        "Recruiter email in submitted offer; "
        "user-supplied official domain"
    )

    if not official_domain:
        return Evidence(
            "recruiter_domain",
            EvidenceKind.UNKNOWN,
            "No independently confirmed employer domain supplied.",
            source,
            "Employer identity cannot be established "
            "from the offer alone.",
        )

    if not isinstance(recruiter_email, str):
        return Evidence(
            "recruiter_domain",
            EvidenceKind.UNKNOWN,
            "Recruiter email is missing or malformed.",
            source,
            "A valid email address is required.",
        )

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+",
        recruiter_email.strip(),
    ):
        return Evidence(
            "recruiter_domain",
            EvidenceKind.UNKNOWN,
            "Recruiter email is missing or malformed.",
            source,
            "A valid email address is required "
            "for domain comparison.",
        )

    recruiter = normalize_domain(recruiter_email)
    official = normalize_domain(official_domain)

    if not recruiter or not official:
        return Evidence(
            "recruiter_domain",
            EvidenceKind.UNKNOWN,
            "Domain comparison could not be completed.",
            source,
            "One or both domain inputs are invalid.",
        )

    recruiter_root = registrable_domain(recruiter)
    official_root = registrable_domain(official)

    if recruiter_root in FREE_EMAIL_DOMAINS:
        return Evidence(
            "recruiter_domain",
            EvidenceKind.RISK,
            "Recruiter uses a public email provider "
            "rather than the supplied employer domain.",
            source,
            "Legitimate recruiters may use external "
            "addresses. This is not proof of fraud.",
        )

    if recruiter == official:
        return Evidence(
            "recruiter_domain",
            EvidenceKind.SUPPORTING,
            "Recruiter email domain exactly matches "
            "the supplied employer domain.",
            source,
            "The employer domain was supplied by the user. "
            "This does not authenticate the sender.",
        )

    if recruiter_root == official_root:
        return Evidence(
            "recruiter_domain",
            EvidenceKind.SUPPORTING,
            "Recruiter and employer domains share the "
            "same registrable domain.",
            source,
            "Subdomain consistency is limited supporting "
            "evidence, not proof of authorization.",
        )

    return Evidence(
        "recruiter_domain",
        EvidenceKind.CONTRADICTION,
        "Recruiter domain does not match the "
        "supplied employer domain.",
        source,
        "Third-party recruitment agencies can be "
        "legitimate. Verify the relationship independently.",
    )


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[.!?;\n]+", text)
        if item.strip()
    ]


def _fee_is_negated(
    sentence: str,
    match: re.Match,
) -> bool:

    before = sentence[:match.start()]
    after = sentence[match.end():]

    before_words = before.split()
    nearby_before = " ".join(before_words[-5:])

    if NEGATION_BEFORE.search(nearby_before):
        return True

    if NEGATION_AFTER.search(after):
        return True

    return False


def evaluate_recruitment_fee(text: str) -> Evidence:
    source = "Submitted offer text"

    for sentence in _sentences(text):
        for match in FEE_PATTERN.finditer(sentence):

            if _fee_is_negated(sentence, match):
                continue

            before = sentence[:match.start()]
            after = sentence[match.end():]

            if (
                PAYMENT_ACTION.search(before)
                or PAYMENT_ACTION.search(after)
            ):
                return Evidence(
                    "recruitment_fee",
                    EvidenceKind.RISK,
                    "Recruitment-related payment request detected: "
                    + match.group(0),
                    source,
                    "A payment request is a caution signal. "
                    "It does not establish fraud.",
                )

    return Evidence(
        "recruitment_fee",
        EvidenceKind.UNKNOWN,
        "No affirmative recruitment payment "
        "request identified by these rules.",
        source,
        "Rule-based analysis can miss indirect or "
        "unusual payment language.",
    )


def evaluate_channel_pressure(text: str) -> Evidence:
    source = "Submitted offer text"

    for sentence in _sentences(text):

        channel = CHANNEL_PATTERN.search(sentence)

        if channel:
            before = sentence[:channel.start()]
            nearby = " ".join(before.split()[-5:])

            if not CHANNEL_NEGATION.search(nearby):
                return Evidence(
                    "communication_channel",
                    EvidenceKind.RISK,
                    "Offer mentions communication through "
                    + channel.group(0),
                    source,
                    "Messaging platforms can be used "
                    "legitimately. Verify the recruiter "
                    "through independent channels.",
                )

        urgency = URGENCY_PATTERN.search(sentence)

        if urgency:
            before = sentence[:urgency.start()]
            nearby = " ".join(before.split()[-5:])

            if not NEGATION_BEFORE.search(nearby):
                return Evidence(
                    "urgency_pressure",
                    EvidenceKind.RISK,
                    "Potential urgency or payment pressure: "
                    + urgency.group(0),
                    source,
                    "Urgency wording alone does not "
                    "prove fraud.",
                )

    return Evidence(
        "communication_channel",
        EvidenceKind.UNKNOWN,
        "No affirmative channel or urgency "
        "signal identified by these rules.",
        source,
        "Absence of detected patterns does not "
        "establish authenticity.",
    )

