from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ComplianceIssue(BaseModel):
    category: str
    description: str
    severity: str
    timestamp: Optional[str]


# A wrapper so the LLM returns a list of issues + a final summary report
class AuditResult(BaseModel):
    compliance_results: list[ComplianceIssue] = Field(description="List of compliance issues found in the video")
    final_status: str = Field(description="'pass' if no high/medium issues found, else 'fail' or 'needs_review'")
    final_report: str = Field(description="A concise summary markdown report auditing the video content.")


class ComplianceIssueResponse(BaseModel):
    id: int
    category: str
    description: str
    severity: str
    timestamp: Optional[str]

    model_config = {"from_attributes": True}


class VideoAuditResponse(BaseModel):
    id: str
    video_url: str
    video_id: str
    transcript: Optional[str]
    ocr_text: Optional[list[str]]
    final_status: str
    final_report: Optional[str]
    errors: Optional[list[str]]
    created_at: datetime
    updated_at: datetime
    compliance_results: list[ComplianceIssueResponse]

    model_config = {"from_attributes": True}


class AuditStartRequest(BaseModel):
    video_url: str = Field(..., description="The YouTube URL to audit")


class AuditStartResponse(BaseModel):
    video_id: str
    status: str
    message: str

