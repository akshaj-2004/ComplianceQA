import sys
import uuid
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from src.graph import workflow


def run_audit(url: str):
    # Generate a unique video ID for file and logging tracking
    video_id = str(uuid.uuid4())[:8]
    print(f"Starting audit for: {url} (ID: {video_id})")
    
    # Set up the initial state matching VideoAuditState
    initial_state = {
        "video_url": url,
        "video_id": video_id,
        "local_file_path": None,
        "video_metadata": {},
        "transcript": "",
        "ocr_text": [],
        "compliance_results": [],
        "final_status": "",
        "final_report": "",
        "errors": []
    }
    
    # Execute the LangGraph workflow
    result = workflow.invoke(initial_state)
    
    print("\n" + "=" * 50)
    print(f"AUDIT COMPLETE — STATUS: {result.get('final_status', 'UNKNOWN').upper()}")
    print("=" * 50)
    print("\nFINAL REPORT:")
    print(result.get("final_report", "No report generated."))
    
    if result.get("errors"):
        print("\nERRORS / WARNINGS:")
        for err in result["errors"]:
            print(f"- {err}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <youtube_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    run_audit(url)


if __name__ == "__main__":
    main()
