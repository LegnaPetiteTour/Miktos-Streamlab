"""
Tests for AI transcription
"""
import pytest
from pathlib import Path
from src.core.transcription import TranscriptSegment, Transcript


class TestTranscriptSegment:
    """Test TranscriptSegment dataclass"""
    
    def test_segment_creation(self):
        """Test creating transcript segment"""
        segment = TranscriptSegment(
            start=0.0,
            end=5.0,
            text="Hello world",
            language="en",
            confidence=0.95
        )
        
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.text == "Hello world"
        assert segment.language == "en"
        assert segment.confidence == 0.95
        
    def test_srt_format(self):
        """Test SRT format conversion"""
        segment = TranscriptSegment(
            start=0.0,
            end=5.0,
            text="Test subtitle",
            language="en"
        )
        
        srt = segment.to_srt_format(index=1)
        
        assert "1\n" in srt
        assert "Test subtitle" in srt
        assert "-->" in srt
        
    def test_vtt_format(self):
        """Test WebVTT format conversion"""
        segment = TranscriptSegment(
            start=0.0,
            end=5.0,
            text="Test subtitle",
            language="en"
        )
        
        vtt = segment.to_vtt_format()
        
        assert "Test subtitle" in vtt
        assert "-->" in vtt


class TestTranscript:
    """Test Transcript class"""
    
    def test_transcript_creation(self, sample_transcript_segments):
        """Test creating transcript"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        assert len(transcript.segments) == 3
        assert transcript.language == "en"
        assert transcript.duration == 10.0
        assert "en" in transcript.detected_languages
        assert "fr" in transcript.detected_languages
        
    def test_get_full_text(self, sample_transcript_segments):
        """Test getting full transcript text"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        text = transcript.get_text()
        
        assert "Hello, this is a test." in text
        assert "Bonjour, ceci est un test." in text
        assert "This is bilingual content." in text
        
    def test_get_filtered_text(self, sample_transcript_segments):
        """Test getting language-filtered text"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        # Get only English
        en_text = transcript.get_text(language="en")
        assert "Hello, this is a test." in en_text
        assert "Bonjour" not in en_text
        
        # Get only French
        fr_text = transcript.get_text(language="fr")
        assert "Bonjour, ceci est un test." in fr_text
        assert "Hello" not in fr_text
        
    def test_export_srt(self, sample_transcript_segments, temp_dir):
        """Test exporting to SRT format"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        output_file = temp_dir / "test.srt"
        transcript.export_srt(output_file)
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "Hello, this is a test." in content
        assert "Bonjour, ceci est un test." in content
        
    def test_export_srt_filtered(self, sample_transcript_segments, temp_dir):
        """Test exporting filtered SRT"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        output_file = temp_dir / "test_en.srt"
        transcript.export_srt(output_file, language="en")
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "Hello, this is a test." in content
        assert "Bonjour" not in content
        
    def test_export_vtt(self, sample_transcript_segments, temp_dir):
        """Test exporting to VTT format"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        output_file = temp_dir / "test.vtt"
        transcript.export_vtt(output_file)
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "WEBVTT" in content
        assert "Hello, this is a test." in content
        
    def test_export_txt(self, sample_transcript_segments, temp_dir):
        """Test exporting to plain text"""
        transcript = Transcript(
            segments=sample_transcript_segments,
            language="en",
            duration=10.0,
            detected_languages=["en", "fr"]
        )
        
        output_file = temp_dir / "test.txt"
        transcript.export_txt(output_file)
        
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert "Hello, this is a test." in content
        assert "Bonjour, ceci est un test." in content
