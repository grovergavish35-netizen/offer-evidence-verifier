
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    VERIFIED = "Verified"
    INCONSISTENT = "Inconsistent"
    COULD_NOT_VERIFY = "Couldn't verify"


class Claim(BaseModel):
    claim_id: str
    claim_type: str
    value: str
    raw_text: Optional[str] = None


class CheckResult(BaseModel):
    claim: Claim
    check_name: str
    finding: str
    source: Optional[str] = None
    verdict: Verdict
    confidence_note: str


class VerificationReport(BaseModel):
    report_id: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    claims: list[Claim] = Field(default_factory=list)
    checks: list[CheckResult] = Field(default_factory=list)
    safe_steps: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This report provides decision support, "
        "not a final determination of authenticity or fraud."
    )
