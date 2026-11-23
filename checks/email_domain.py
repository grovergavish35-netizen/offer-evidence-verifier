
from core.schemas import (
    Claim,
    CheckResult,
    FindingType,
    Verdict,
)

from core.reliability import (
    EvidenceKind,
    compare_recruiter_domain,
)

def check_email_domain(
    email_claim: Claim,
    official_domain: str | None = None,
) -> CheckResult:
    """
    Compare recruiter email with an independently
    confirmed employer domain.

    Domain consistency is not sender authentication.
    """

    evidence = compare_recruiter_domain(
        recruiter_email=email_claim.value or "",
        official_domain=official_domain,
    )

    if evidence.kind == EvidenceKind.SUPPORTING:
        verdict = Verdict.VERIFIED
        finding_type = FindingType.SUPPORTING_EVIDENCE

    elif evidence.kind == EvidenceKind.CONTRADICTION:
        verdict = Verdict.INCONSISTENT
        finding_type = FindingType.CONTRADICTION

    elif evidence.kind == EvidenceKind.RISK:
        verdict = Verdict.COULD_NOT_VERIFY
        finding_type = FindingType.RISK_SIGNAL

    else:
        verdict = Verdict.COULD_NOT_VERIFY
        finding_type = FindingType.UNKNOWN

    return CheckResult(
        claim=email_claim,
        check_name="email_domain",
        finding=evidence.finding,
        source=evidence.source,
        verdict=verdict,
        finding_type=finding_type,
        confidence_note=evidence.limitation,
    )