"""
Transcription Service - Wraps existing transcription module

This service provides a clean interface to your existing Whisper-based
transcription functionality.
"""

import sys
import logging
from typing import List, Optional, Any
from pathlib import Path

# Add existing backend to path
BACKEND_PATH = '/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend'
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

try:
    from core.transcription import Transcriber, TranscriptFormat
    TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    Transcriber = None
    TranscriptFormat = None
    TRANSCRIPTION_AVAILABLE = False
    logging.warning(f"Transcription module not available: {e}")

from config import get_config

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Unified transcription service for live and recorded content.
    
    This wraps your existing Whisper-based transcription system
    and provides a clean interface for the Hub.
    
    Example:
        ```python
        service = TranscriptionService()
        
        # Transcribe a recorded file
        transcript = await service.transcribe_file(
            "/path/to/recording.mp4",
            languages=["en", "fr"]
        )
        
        # Export transcript
        srt_path = await service.export_transcript(
            transcript,
            format="srt",
            output_path="/path/to/output.srt"
        )
        ```
    """
    
    def __init__(self):
        if not TRANSCRIPTION_AVAILABLE:
            raise RuntimeError("Transcription module not available - check backend installation")
        
        config = get_config()
        
        self._transcriber = Transcriber(
            model_size=config.transcription.model_size,
            use_gpu=config.transcription.use_gpu,
        )
        
        self._default_language = config.transcription.default_language
        self._supported_languages = config.transcription.supported_languages
        
        logger.info(
            f"Transcription service initialized "
            f"(model={config.transcription.model_size}, gpu={config.transcription.use_gpu})"
        )
    
    async def transcribe_file(
        self,
        file_path: str,
        languages: Optional[List[str]] = None,
        output_format: str = "text",
    ) -> Any:
        """
        Transcribe a recorded audio/video file.
        
        Args:
            file_path: Path to media file
            languages: Languages to transcribe (e.g., ["en", "fr"])
            output_format: "text", "json", "srt", "vtt"
            
        Returns:
            Transcription result in requested format
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use default language if none specified
        if not languages:
            languages = [self._default_language]
        
        # Validate languages
        for lang in languages:
            if lang not in self._supported_languages:
                logger.warning(f"Language '{lang}' not in supported list, but will attempt")
        
        logger.info(f"Transcribing file: {file_path} (languages: {languages})")
        
        try:
            # Call existing transcriber
            result = await self._transcriber.transcribe_file(
                file_path=file_path,
                language=languages[0],  # Primary language
                task="transcribe",  # or "translate" for translation
            )
            
            # Format result
            if output_format == "json":
                return result
            elif output_format == "text":
                return result.get("text", "")
            elif output_format in ["srt", "vtt"]:
                return self._format_as_subtitle(result, output_format)
            else:
                return result
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    async def transcribe_live(
        self,
        audio_stream,
        languages: Optional[List[str]] = None,
        callback: Optional[callable] = None,
    ) -> Any:
        """
        Transcribe audio stream in real-time.
        
        Args:
            audio_stream: Audio input stream
            languages: Languages to transcribe
            callback: Function to call with transcript chunks
            
        Returns:
            Stream of transcript chunks
        """
        if not languages:
            languages = [self._default_language]
        
        logger.info(f"Starting live transcription (languages: {languages})")
        
        try:
            # Call existing transcriber's live mode
            # Note: This requires implementing streaming support in your transcriber
            async for chunk in self._transcriber.transcribe_stream(
                audio_stream,
                language=languages[0],
            ):
                if callback:
                    callback(chunk)
                yield chunk
                
        except Exception as e:
            logger.error(f"Live transcription failed: {e}", exc_info=True)
            raise
    
    async def export_transcript(
        self,
        transcript: Any,
        format: str,
        output_path: str,
    ) -> str:
        """
        Export transcript to file.
        
        Args:
            transcript: Transcript data
            format: "srt", "vtt", "txt", "json"
            output_path: Where to save the file
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting transcript to: {output_path} (format: {format})")
        
        try:
            if format == "srt":
                content = self._format_as_subtitle(transcript, "srt")
            elif format == "vtt":
                content = self._format_as_subtitle(transcript, "vtt")
            elif format == "txt":
                content = transcript.get("text", str(transcript))
            elif format == "json":
                import json
                content = json.dumps(transcript, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Transcript exported successfully")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            raise
    
    def _format_as_subtitle(self, transcript: dict, format: str) -> str:
        """
        Format transcript as SRT or VTT subtitles.
        
        Args:
            transcript: Transcript with segments
            format: "srt" or "vtt"
            
        Returns:
            Formatted subtitle string
        """
        segments = transcript.get("segments", [])
        
        if format == "srt":
            return self._to_srt(segments)
        elif format == "vtt":
            return self._to_vtt(segments)
        else:
            raise ValueError(f"Unsupported subtitle format: {format}")
    
    def _to_srt(self, segments: List[dict]) -> str:
        """Convert segments to SRT format"""
        lines = []
        for i, segment in enumerate(segments, start=1):
            start = self._format_timestamp(segment["start"], srt=True)
            end = self._format_timestamp(segment["end"], srt=True)
            text = segment["text"].strip()
            
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")  # Blank line between segments
        
        return "\n".join(lines)
    
    def _to_vtt(self, segments: List[dict]) -> str:
        """Convert segments to WebVTT format"""
        lines = ["WEBVTT", ""]
        
        for segment in segments:
            start = self._format_timestamp(segment["start"], srt=False)
            end = self._format_timestamp(segment["end"], srt=False)
            text = segment["text"].strip()
            
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float, srt: bool = True) -> str:
        """Format timestamp for subtitles"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if srt:
            # SRT format: 00:00:00,000
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")
        else:
            # VTT format: 00:00:00.000
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self._supported_languages.copy()
    
    def is_available(self) -> bool:
        """Check if transcription service is available"""
        return TRANSCRIPTION_AVAILABLE
