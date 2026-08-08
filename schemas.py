from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueFinding(BaseModel):
    category: str = Field(
        description="Type of issue e.g., 'SQL Injection', 'O(N^2) Complexity', 'Hardcoded Secret'"
    )
    line_number: Optional[int] = Field(
        default=None, 
        description="Line number in the code snippet where the issue is found"
    )
    severity: SeverityLevel = Field(
        description="Severity level of the issue: HIGH, MEDIUM, or LOW"
    )
    explanation: str = Field(
        description="Detailed explanation of why this code pattern is problematic"
    )
    suggested_fix: str = Field(
        description="Corrected code snippet fixing the issue"
    )

class AgentReviewResult(BaseModel):
    agent_name: str = Field(
        description="Name of the specialist agent e.g., 'Security Agent', 'Performance Agent'"
    )
    passed: bool = Field(
        description="True if no HIGH or MEDIUM issues were found, False otherwise"
    )
    findings: List[IssueFinding] = Field(
        default_factory=list,
        description="List of detected vulnerabilities or improvements"
    )