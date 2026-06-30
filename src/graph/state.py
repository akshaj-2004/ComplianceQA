import operator
from typing import Annotated, Optional, Any, TypedDict, Dict

from ..schemas import ComplianceIssue

class VideoAuditState(TypedDict):
    """Defines the data schema for langgraph execution content"""
    video_url: str
    video_id: str
    local_file_path: Optional[str]
    video_metadata: Dict[str, Any]
    transcript: str
    ocr_text: list[str]
    compliance_results: Annotated[list[ComplianceIssue], operator.add]
    final_status: str
    final_report: str
    errors: Annotated[list[str], operator.add]