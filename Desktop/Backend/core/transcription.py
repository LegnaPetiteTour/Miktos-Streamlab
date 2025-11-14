"""
AI Transcription Module
Handles bilingual (EN/FR) transcription using OpenAI Whisper.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta

# Optional dependencies - only required when using transcription features
try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None
    torch = None


logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A segment of transcribed text"""
    start: float  # seconds
    end: float  # seconds
    text: str
    language: str
    confidence: float = 1.0

    def to_srt_format(self, index: int) -> str:
        """Convert to SRT subtitle format"""
        start_time = str(timedelta(seconds=self.start)).split('.')[0] + ',000'
        end_time = str(timedelta(seconds=self.end)).split('.')[0] + ',000'

        return f"{index}\n{start_time} --> {end_time}\n{self.text}\n"

    def to_vtt_format(self) -> str:
        """Convert to WebVTT format"""
        start_time = str(timedelta(seconds=self.start))
        end_time = str(timedelta(seconds=self.end))

        return f"{start_time} --> {end_time}\n{self.text}\n"


@dataclass
class Transcript:
    """Complete transcript with metadata"""
    segments: List[TranscriptSegment]
    language: str
    duration: float
    detected_languages: List[str]

    def get_text(self, language: Optional[str] = None) -> str:
        """Get full text, optionally filtered by language"""
        if language:
            segments = [s for s in self.segments if s.language == language]
        else:
            segments = self.segments

        return '\n'.join(s.text for s in segments)

    def export_srt(self, output_path: Path, language: Optional[str] = None):
        """Export to SRT subtitle format"""
        segments = self.segments
        if language:
            segments = [s for s in segments if s.language == language]

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(segment.to_srt_format(i))
                f.write('\n')

        logger.info(f"Exported SRT to {output_path}")

    def export_vtt(self, output_path: Path, language: Optional[str] = None):
        """Export to WebVTT format"""
        segments = self.segments
        if language:
            segments = [s for s in segments if s.language == language]

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n\n')
            for segment in segments:
                f.write(segment.to_vtt_format())
                f.write('\n')

        logger.info(f"Exported VTT to {output_path}")

    def export_txt(self, output_path: Path, language: Optional[str] = None):
        """Export to plain text"""
        text = self.get_text(language)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        logger.info(f"Exported TXT to {output_path}")


class TranscriptionEngine:
    """
    Handles bilingual transcription using Whisper

    Features:
    - Automatic language detection (EN/FR)
    - Multi-language transcription
    - Multiple export formats (SRT, VTT, TXT)
    - Timestamp synchronization
    """

    SUPPORTED_MODELS = ['tiny', 'base', 'small', 'medium', 'large']

    def __init__(self, model_size: str = 'base', device: Optional[str] = None):
        """
        Initialize transcription engine

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda, cpu, or auto-detect)
        """
        if not WHISPER_AVAILABLE:
            raise ImportError(
                "Whisper and Torch are required for transcription. "
                "Install with: pip install openai-whisper torch"
            )

        if model_size not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model must be one of {self.SUPPORTED_MODELS}")

        self.model_size = model_size

        # Determine device
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device

        logger.info(f"Initializing Whisper {model_size} model on {device}...")
        self.model = whisper.load_model(model_size, device=device)
        logger.info("Whisper model loaded")

    def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        detect_language: bool = True
    ) -> Transcript:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio/video file
            language: Force specific language (en, fr, or None for auto)
            detect_language: Enable automatic language detection

        Returns:
            Transcript object
        """
        logger.info(f"Transcribing {audio_path.name}...")

        # Transcribe
        result = self.model.transcribe(
            str(audio_path),
            language=language,
            task='transcribe',
            fp16=self.device == 'cuda',
            verbose=False
        )

        # Detect languages in segments
        detected_languages = set()
        segments = []

        for seg in result['segments']:
            # Detect language (simplified - Whisper doesn't expose per-segment language well)
            seg_language = result.get('language', 'unknown')
            detected_languages.add(seg_language)

            segment = TranscriptSegment(
                start=seg['start'],
                end=seg['end'],
                text=seg['text'].strip(),
                language=seg_language
            )
            segments.append(segment)

        transcript = Transcript(
            segments=segments,
            language=result.get('language', 'unknown'),
            duration=result.get('duration', 0),
            detected_languages=list(detected_languages)
        )

        logger.info(f"Transcription complete: {len(segments)} segments, "
                   f"languages: {', '.join(detected_languages)}")

        return transcript

    def transcribe_bilingual(
        self,
        audio_path: Path,
        export_dir: Optional[Path] = None
    ) -> Tuple[Transcript, Dict[str, Path]]:
        """
        Transcribe and export bilingual content

        Args:
            audio_path: Path to audio/video file
            export_dir: Directory to export files (optional)

        Returns:
            (transcript, exported_files_dict)
        """
        # Transcribe with auto language detection
        transcript = self.transcribe_file(audio_path, language=None)

        exported_files = {}

        if export_dir:
            export_dir.mkdir(parents=True, exist_ok=True)
            base_name = audio_path.stem

            # Export full transcript in all formats
            transcript.export_srt(export_dir / f"{base_name}_full.srt")
            transcript.export_vtt(export_dir / f"{base_name}_full.vtt")
            transcript.export_txt(export_dir / f"{base_name}_full.txt")

            exported_files['full'] = {
                'srt': export_dir / f"{base_name}_full.srt",
                'vtt': export_dir / f"{base_name}_full.vtt",
                'txt': export_dir / f"{base_name}_full.txt",
            }

            # Export language-specific transcripts if multiple languages detected
            if len(transcript.detected_languages) > 1:
                for lang in transcript.detected_languages:
                    transcript.export_srt(export_dir / f"{base_name}_{lang}.srt", language=lang)
                    transcript.export_vtt(export_dir / f"{base_name}_{lang}.vtt", language=lang)
                    transcript.export_txt(export_dir / f"{base_name}_{lang}.txt", language=lang)

                    exported_files[lang] = {
                        'srt': export_dir / f"{base_name}_{lang}.srt",
                        'vtt': export_dir / f"{base_name}_{lang}.vtt",
                        'txt': export_dir / f"{base_name}_{lang}.txt",
                    }

        return transcript, exported_files

    def get_model_info(self) -> Dict:
        """Get information about loaded model"""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'languages': self.model.available_languages,
        }


def transcribe_stream_recording(
    recording_path: Path,
    output_dir: Path,
    model_size: str = 'base'
) -> Dict[str, Path]:
    """
    Convenience function to transcribe a stream recording

    Args:
        recording_path: Path to recorded stream
        output_dir: Directory for transcripts
        model_size: Whisper model size

    Returns:
        Dictionary of exported file paths
    """
    engine = TranscriptionEngine(model_size=model_size)
    transcript, files = engine.transcribe_bilingual(recording_path, output_dir)

    return files
