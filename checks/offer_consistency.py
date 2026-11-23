
import re
from core.schemas import Claim, CheckResult, Verdict

FIELD_PATTERNS = {
    "company": r"(?im)^\s*(?:company|organization)[ \t]*:[ \t]*(.+)$",
    "role": r"(?im)^\s*(?:role|position|job title)[ \t]*:[ \t]*(.+)$",
    "joining_date": r"(?im)^\s*(?:joining date|start date)[ \t]*:[ \t]*(.+)$",
    "department": r"(?im)^\s*department[ \t]*:[ \t]*(.+)$",
    "reporting_manager": r"(?im)^\s*(?:reporting manager|manager)[ \t]*:[ \t]*(.+)$",
}


def check_offer_consistency(text: str) -> CheckResult:
    missing = []
    conflicts = []

    for field, pattern in FIELD_PATTERNS.items():
        matches = [
            value.strip()
            for value in re.findall(pattern, text)
            if value.strip()
        ]

        if not matches:
            missing.append(field)
        elif len({value.casefold() for value in matches}) > 1:
            conflicts.append(field)

    claim = Claim(
        claim_id="STRUCTURE",
        claim_type="offer_structure",
        value="Offer letter structure and field consistency",
    )

    if conflicts:
        return CheckResult(
            claim=claim,
            check_name="offer_consistency",
            finding="Conflicting values found in: " + ", ".join(conflicts),
            source="Submitted offer text",
            verdict=Verdict.INCONSISTENT,
            confidence_note="Conflicting fields require manual review.",
        )

    if missing:
        return CheckResult(
            claim=claim,
            check_name="offer_consistency",
            finding="Fields not found: " + ", ".join(missing),
            source="Submitted offer text",
            verdict=Verdict.COULD_NOT_VERIFY,
            confidence_note="Missing fields do not prove fraud.",
        )

    return CheckResult(
        claim=claim,
        check_name="offer_consistency",
        finding="All configured fields were found.",
        source="Submitted offer text",
        verdict=Verdict.COULD_NOT_VERIFY,
        confidence_note="Complete structure does not authenticate an offer.",
    )
