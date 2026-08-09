from pydantic import BaseModel, Field
from typing import List

class LineAnnotation(BaseModel):
    path: str = Field(description="Relative path of the audited file, e.g., 'sample.py'")
    line: int = Field(description="Line number in the diff where the issue exists")
    comment: str = Field(description="Specific feedback, security risk, or fix suggestion for this line")

class PRReviewPayload(BaseModel):
    overall_score: int = Field(description="Overall health score from 0 to 100")
    summary: str = Field(description="High-level review summary in Markdown")
    annotations: List[LineAnnotation] = Field(description="List of inline line annotations")