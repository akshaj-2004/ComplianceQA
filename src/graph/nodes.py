import os
import logging
from typing import Dict, Any

from .state import ComplianceIssue, VideoAuditState
from ..services import VideoIndexerService
from ..utils import qdrant_cloud, llm, embedding_model
from ..schemas import AuditResult

logger = logging.getLogger("ComplianceQA")
logging.basicConfig(level=logging.INFO)


# NODES

def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Downloads the YouTube video and extracts transcript + OCR locally.
    """
    video_url = state["video_url"]
    video_id_input = state["video_id"]

    logger.info(f"------[Node: Indexer] Processing: {video_url}")

    # Use video_id to avoid colliding temp files
    local_filename = f"{video_id_input}.mp4"

    try:
        vi_service = VideoIndexerService()

        # Step 1: Download video via yt-dlp
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_video(video_url, output_path=local_filename)
        else:
            raise ValueError("Please provide a valid YouTube URL")

        logger.info(f"Download complete: {local_path}")

        # Step 2: Transcribe locally with Whisper
        transcript = vi_service.transcribe(local_path)
        logger.info(f"Transcription complete ({len(transcript)} chars)")

        # Step 3: Extract on-screen text via OCR
        ocr_text = vi_service.extract_ocr(local_path)

        # Cleanup temp file
        vi_service.cleanup(local_path)

        logger.info("------[Node: Indexer] Done")
        return {
            "video_id": video_id_input,
            "local_file_path": local_path,
            "transcript": transcript,
            "ocr_text": ocr_text,
        }

    except Exception as e:
        logger.error(f"[Node: Indexer] Error: {e}")
        return {
            "errors": [f"Indexer error: {str(e)}"],
        }


def retrieval_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Queries Qdrant for relevant compliance guidelines based on the transcript and OCR text.
    """
    logger.info("------[Node: Retrieval] Querying compliance database")
    
    transcript = state.get("transcript", "")
    ocr_text = state.get("ocr_text", [])

    if not transcript and not ocr_text:
        logger.warning("[Node: Retrieval] No transcript or OCR text found in state.")
        return {"video_metadata": {"rules": ""}}

    query_text = f"{transcript} {' '.join(ocr_text)}"
    try:
        query_vector = embedding_model.embed_query(query_text)
        
        # Search Qdrant using the correct client search API
        results = qdrant_cloud.search(
            collection_name="compliance_docs",
            query_vector=query_vector,
            limit=5
        )

        retrieved_rules = []
        for hit in results:
            content = hit.payload.get("page_content", "")
            source = hit.payload.get("source", "Unknown source")
            page = hit.payload.get("page", 0)
            retrieved_rules.append(f"Source: {source} (Page {page + 1}):\n{content}")

        search_results = "\n\n---\n\n".join(retrieved_rules)
        logger.info(f"[Node: Retrieval] Retrieved {len(retrieved_rules)} compliance rules")
        
        return {
            "video_metadata": {"rules": search_results}
        }
    except Exception as e:
        logger.error(f"[Node: Retrieval] Error: {e}")
        return {
            "errors": [f"Retrieval error: {str(e)}"],
            "video_metadata": {"rules": ""}
        }


def compliance_auditor_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Compares the video transcript and OCR text against retrieved compliance rules using Gemini.
    """
    logger.info("------[Node: Auditor] Auditing video content against rules")
    
    transcript = state.get("transcript", "")
    ocr_text = state.get("ocr_text", [])
    video_metadata = state.get("video_metadata", {})
    rules = video_metadata.get("rules", "")

    if not transcript:
        logger.info("[Node: Auditor] No transcript available. Skipping audit.")
        return {
            "compliance_results": [],
            "final_status": "fail",
            "final_report": "Audit skipped as no video transcript was generated."
        }

    system_prompt = """You are a senior brand compliance auditor. 
Your task is to analyze the video transcript and OCR text against the official regulatory rules provided.

OFFICIAL REGULATORY RULES:
{rules}

VIDEO TRANSCRIPT:
{transcript}

VIDEO ON-SCREEN TEXT (OCR):
{ocr_text}

Compare the video content against the rules. Identify any clear violations (e.g. missing disclosure for sponsor content, misleading claims, or formatting violations). 
For each violation, categorize the severity ('low', 'medium', 'high') and record a timestamp if mentioned.
"""

    formatted_prompt = system_prompt.format(
        rules=rules if rules else "No specific rules retrieved.",
        transcript=transcript,
        ocr_text=", ".join(ocr_text) if ocr_text else "None"
    )

    try:
        structured_llm = llm.with_structured_output(AuditResult)
        audit_output: AuditResult = structured_llm.invoke(formatted_prompt)
        
        return {
            "compliance_results": audit_output.compliance_results,
            "final_status": audit_output.final_status,
            "final_report": audit_output.final_report
        }
    except Exception as e:
        logger.error(f"[Node: Auditor] Error: {e}")
        return {
            "errors": [f"Auditor error: {str(e)}"],
            "compliance_results": []
        }


def report_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Formats the compliance results and errors into a final user-ready report.
    """
    logger.info("------[Node: Report] Generating final report")
    
    compliance_results = state.get("compliance_results", [])
    errors = state.get("errors", [])
    final_status = state.get("final_status", "pass" if not compliance_results else "needs_review")
    final_report = state.get("final_report", "")

    if not final_report:
        if not compliance_results:
            final_report = "# Compliance Report\n\nNo compliance issues were identified in this video."
            final_status = "pass"
        else:
            final_report = f"# Compliance Report\n\n**Status:** {final_status.upper()}\n\n## Identified Issues\n"
            for issue in compliance_results:
                timestamp_str = f" at {issue.timestamp}" if issue.timestamp else ""
                final_report += f"- **[{issue.severity.upper()}]** {issue.category}{timestamp_str}: {issue.description}\n"
    
    # Append errors to final report if any occurred
    if errors:
        final_report += "\n\n## Execution Errors & Warnings\n"
        for error in errors:
            final_report += f"- {error}\n"
        if final_status == "pass":
            final_status = "needs_review"

    return {
        "final_status": final_status,
        "final_report": final_report
    }