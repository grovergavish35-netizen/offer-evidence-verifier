
import re

from core.schemas import Claim, CheckResult, Verdict


FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "rediffmail.com",
}


def check_email_domain(
    email_claim: Claim,
    official_domain: str | None = None,
) -> CheckResult:
    """
    Compare a supplied email with a trusted official domain.

    official_domain must come from an independent trusted
    source, never from the offer text itself.
    """

    email = email_claim.value.strip().lower()

    if not re.fullmatch(
        r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
        email,
    ):
        return CheckResult(
            claim=email_claim,
            check_name="email_domain",
            finding="Invalid email format.",
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note="Email format could not be parsed.",
        )

    sender_domain = email.rsplit("@", 1)[1]

    if not official_domain:
        return CheckResult(
            claim=email_claim,
            check_name="email_domain",
            finding=(
                f"Sender domain: {sender_domain}. "
                "Official company domain is not available."
            ),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note=(
                "No independently verified company domain "
                "was supplied for comparison."
            ),
        )

    trusted_domain = official_domain.strip().lower().strip(".")

    # Remove optional @ or URL-style input only if already
    # normalized by the caller. Here we expect a bare domain.
    if not re.fullmatch(
        r"[a-z0-9.-]+\.[a-z]{2,}",
        trusted_domain,
    ):
        return CheckResult(
            claim=email_claim,
            check_name="email_domain",
            finding="Official domain input is invalid.",
            source=None,
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note="Trusted domain must be validated.",
        )

    if sender_domain == trusted_domain:
        return CheckResult(
            claim=email_claim,
            check_name="email_domain",
            finding="Sender email domain matches the official domain.",
            source="Trusted official-domain reference",
            verdict=Verdict.VERIFIED,
            confidence_note=(
                "Only domain consistency was verified. "
                "The offer and sender identity are not authenticated."
            ),
        )

    if sender_domain in FREE_EMAIL_DOMAINS:
        finding = (
            f"Sender uses free email provider {sender_domain}, "
            f"not official domain {trusted_domain}."
        )
    else:
        finding = (
            f"Sender domain {sender_domain} differs from "
            f"official domain {trusted_domain}."
        )

    return CheckResult(
        claim=email_claim,
        check_name="email_domain",
        finding=finding,
        source="Trusted official-domain reference",
        verdict=Verdict.INCONSISTENT,
        confidence_note=(
            "Mismatch is a warning, not proof of fraud. "
            "Third-party recruiters may be authorized."
        ),
    )
