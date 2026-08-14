from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class FindingItem(BaseModel):
    title: str = Field(..., description="Vulnerability title (e.g., SQL Injection, Resource Leak)")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW, or INFO")
    category: str = Field("General", description="Vulnerability category (e.g., Injection, Resource Management)")
    line: Optional[int] = Field(None, description="Line number in the submitted code where the issue starts")
    vulnerable_code: Optional[str] = Field(None, description="Specific vulnerable snippet")
    explanation: str = Field(..., description="Clear explanation of the flaw")
    impact: str = Field("", description="Security and operational impact")
    recommendation: str = Field(..., description="Remediation steps")
    related_policy: Optional[str] = Field(None, description="Matched corporate rule or policy")
    confidence: float = Field(0.95, description="Confidence score between 0.0 and 1.0")

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v):
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}:
                return v_upper
            if "CRIT" in v_upper:
                return "CRITICAL"
            if "HIGH" in v_upper:
                return "HIGH"
            if "MED" in v_upper:
                return "MEDIUM"
            if "LOW" in v_upper:
                return "LOW"
        return "MEDIUM"

class SecurityAuditPayload(BaseModel):
    summary: str = Field(..., description="Executive summary of the security posture in plain text (no raw JSON)")
    health_score: Optional[int] = Field(None, description="Integer score between 0 and 100")
    findings: List[FindingItem] = Field(default_factory=list, description="List of identified findings")
    refactored_code: str = Field("", description="Clean, complete, runnable Python source code without markdown fences")
    refactor_notes: str = Field("", description="Summary of applied refactoring steps")

# Backwards compatibility alias
PRReviewPayload = SecurityAuditPayload