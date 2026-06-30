import os
import logging
import yt_dlp

from ..config import BASE_DIR
from ..utils.whisper_model import get_whisper_model

logger = logging.getLogger("ComplianceQA")

# Default directory for downloaded videos
VIDEOS_DIR = os.path.join(BASE_DIR, "data", "videos")


class VideoIndexerService:
    """Service for downloading, transcribing, and extracting text from YouTube videos."""

    def __init__(self, videos_dir: str = VIDEOS_DIR):
        """Initializes the service.

        Args:
            videos_dir: Directory where downloaded videos are stored.
                        Defaults to data/videos/ at the project root.
        """
        self.videos_dir = videos_dir
        os.makedirs(self.videos_dir, exist_ok=True)

    def download_video(self, url: str, output_path: str) -> str:
        """Downloads a YouTube video from url and saves it to output_path.

        If output_path is just a filename (e.g. 'video.mp4'), it is placed
        inside self.videos_dir (data/videos/) automatically.

        Args:
            url: The YouTube video URL.
            output_path: Path or filename to save the downloaded video as.

        Returns:
            The local file path of the downloaded video.
        """
        # If output_path is just a filename, put it under videos_dir
        if not os.path.isabs(output_path) and os.path.dirname(output_path) == "":
            output_path = os.path.join(self.videos_dir, output_path)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        ydl_opts = {
            "format": "best",        # Need video+audio for both transcription and OCR
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "overwrites": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        logger.info(f"Downloaded video to {output_path}")
        return output_path

    def transcribe(self, local_path: str) -> str:
        """Transcribes audio from a local video file using OpenAI Whisper.

        Args:
            local_path: Path to the local video file.

        Returns:
            The full transcript text.

        Raises:
            FileNotFoundError: If the local_path does not exist.
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Video file not found: {local_path}")

        model = get_whisper_model()
        result = model.transcribe(local_path)
        transcript = result["text"].strip()

        logger.info(f"Transcription complete ({len(transcript)} chars)")
        return transcript

    def extract_ocr(self, local_path: str, frame_interval_sec: int = 2) -> list[str]:
        """Extracts on-screen text from video frames using OpenCV + Gemini Vision.

        Samples one frame every `frame_interval_sec` seconds, encodes it as
        base64, and sends it to Google Gemini to extract visible text.
        Duplicate and empty results are filtered.

        Args:
            local_path: Path to the local video file.
            frame_interval_sec: Seconds between sampled frames (default: 2).

        Returns:
            A list of unique OCR text strings extracted from video frames.

        Raises:
            FileNotFoundError: If the local_path does not exist.
        """
        import base64
        import cv2
        from langchain_core.messages import HumanMessage
        from ..utils import llm

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Video file not found: {local_path}")

        cap = cv2.VideoCapture(local_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {local_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            logger.warning("Could not determine FPS, defaulting to 30")
            fps = 30.0

        # Calculate how many frames to skip between OCR samples
        frame_interval = int(fps * frame_interval_sec)
        frame_count = 0
        seen_texts = set()
        ocr_results = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # Encode the frame as a JPEG base64 string
                _, buffer = cv2.imencode(".jpg", frame)
                image_base64 = base64.b64encode(buffer).decode("utf-8")

                # Send the frame to Gemini to extract on-screen text
                message = HumanMessage(content=[
                    {
                        "type": "text",
                        "text": (
                            "Extract all visible on-screen text from this video frame. "
                            "Return only the raw text, nothing else. "
                            "If there is no visible text, return exactly: NO_TEXT"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ])

                response = llm.invoke([message])
                text = response.content.strip()

                if text and text != "NO_TEXT" and text not in seen_texts:
                    seen_texts.add(text)
                    ocr_results.append(text)

            frame_count += 1

        cap.release()
        logger.info(f"OCR extraction complete ({len(ocr_results)} unique text blocks)")
        return ocr_results

    def cleanup(self, local_path: str) -> None:
        """Removes a downloaded video file after processing.

        Args:
            local_path: Path to the file to delete.
        """
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Cleaned up temp file: {local_path}")