"""
Export Service - Video editing and export for social media

This service provides FFmpeg-based video editing capabilities for
cutting clips, resizing to different aspect ratios, adding captions,
and exporting for social platforms.
"""

import logging
import asyncio
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum

from config import get_config

logger = logging.getLogger(__name__)


class AspectRatio(Enum):
    """Standard aspect ratios for different platforms"""
    LANDSCAPE = "16:9"      # YouTube, Facebook, Twitter horizontal
    VERTICAL = "9:16"       # TikTok, Instagram Reels, YouTube Shorts
    SQUARE = "1:1"          # Instagram Feed, LinkedIn
    PORTRAIT = "4:5"        # Instagram Feed alternative


class ExportQuality(Enum):
    """Export quality presets"""
    LOW = "low"              # 720p, 2 Mbps
    MEDIUM = "medium"        # 1080p, 5 Mbps
    HIGH = "high"            # 1080p, 8 Mbps
    ULTRA = "ultra"          # 4K, 20 Mbps


class ExportStatus(Enum):
    """Export job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportJob:
    """An export job"""
    id: str
    input_file: Path
    output_file: Path

    # Settings
    aspect_ratio: AspectRatio
    quality: ExportQuality
    add_captions: bool
    caption_file: Optional[Path] = None

    # Status
    status: ExportStatus = ExportStatus.QUEUED
    progress_percent: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ClipRequest:
    """Request to cut a clip from a video"""
    input_file: Path
    start_time: float  # seconds
    end_time: float    # seconds
    output_file: Optional[Path] = None


@dataclass
class ResizeRequest:
    """Request to resize video to different aspect ratio"""
    input_file: Path
    target_aspect: AspectRatio
    quality: ExportQuality = ExportQuality.HIGH
    output_file: Optional[Path] = None


@dataclass
class CaptionRequest:
    """Request to add captions to video"""
    input_file: Path
    caption_file: Path  # SRT or VTT format
    output_file: Optional[Path] = None

    # Caption styling
    font_name: str = "Arial"
    font_size: int = 24
    font_color: str = "white"
    outline_color: str = "black"
    outline_width: int = 2


class PlatformPreset:
    """Export presets for different platforms"""

    YOUTUBE_HORIZONTAL = {
        "aspect": AspectRatio.LANDSCAPE,
        "resolution": (1920, 1080),
        "bitrate": 8000,
        "audio_bitrate": 192,
    }

    YOUTUBE_SHORTS = {
        "aspect": AspectRatio.VERTICAL,
        "resolution": (1080, 1920),
        "bitrate": 6000,
        "audio_bitrate": 192,
    }

    TIKTOK = {
        "aspect": AspectRatio.VERTICAL,
        "resolution": (1080, 1920),
        "bitrate": 6000,
        "audio_bitrate": 192,
    }

    INSTAGRAM_REEL = {
        "aspect": AspectRatio.VERTICAL,
        "resolution": (1080, 1920),
        "bitrate": 6000,
        "audio_bitrate": 192,
    }

    INSTAGRAM_FEED = {
        "aspect": AspectRatio.SQUARE,
        "resolution": (1080, 1080),
        "bitrate": 5000,
        "audio_bitrate": 192,
    }

    FACEBOOK = {
        "aspect": AspectRatio.LANDSCAPE,
        "resolution": (1280, 720),
        "bitrate": 4000,
        "audio_bitrate": 128,
    }


class ExportService:
    """
    Video export and editing service.

    Provides FFmpeg-based editing capabilities for cutting clips,
    resizing to different aspect ratios, adding captions, and
    exporting optimized videos for social media platforms.

    Example:
        ```python
        service = ExportService()

        # Cut a clip
        clip = await service.cut_clip(
            input_file=Path("/recordings/show.mp4"),
            start_time=120.0,  # 2 minutes
            end_time=150.0,    # 2:30
        )

        # Resize for TikTok
        tiktok_video = await service.resize_for_platform(
            input_file=clip,
            platform="tiktok",
        )

        # Add captions
        with_captions = await service.add_captions(
            input_file=tiktok_video,
            caption_file=Path("/transcripts/captions.srt"),
        )

        print(f"Final video: {with_captions}")
        ```
    """

    def __init__(self):
        config = get_config()

        # Export directory
        self._exports_dir = Path(config.paths.exports_dir)
        self._exports_dir.mkdir(parents=True, exist_ok=True)

        # Check FFmpeg availability
        self._ffmpeg_available = self._check_ffmpeg()
        if not self._ffmpeg_available:
            logger.warning(
                "FFmpeg not found - export functionality will be limited")

        # Job queue and tracking
        self._job_queue: List[ExportJob] = []
        self._active_jobs: Dict[str, ExportJob] = {}
        self._completed_jobs: Dict[str, ExportJob] = {}

        logger.info(
            f"Export service initialized (directory: {
                self._exports_dir})")

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"FFmpeg check failed: {e}")
            return False

    async def cut_clip(
        self,
        input_file: Path,
        start_time: float,
        end_time: float,
        output_file: Optional[Path] = None,
    ) -> Path:
        """
        Cut a clip from a video.

        Args:
            input_file: Source video file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_file: Output path (auto-generated if None)

        Returns:
            Path to the cut clip
        """
        logger.info(
            f"Cutting clip: {input_file.name} "
            f"[{start_time:.1f}s - {end_time:.1f}s]"
        )

        if not self._ffmpeg_available:
            raise RuntimeError("FFmpeg not available")

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Generate output path if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self._exports_dir / f"clip_{timestamp}.mp4"

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Build FFmpeg command
            duration = end_time - start_time

            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss", str(start_time),  # Start time
                "-i", str(input_file),   # Input
                "-t", str(duration),     # Duration
                "-c", "copy",            # Copy codecs (fast)
                str(output_file),
            ]

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error = stderr.decode()
                logger.error(f"FFmpeg failed: {error}")
                raise RuntimeError(f"FFmpeg failed: {error}")

            logger.info(f"Clip created: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to cut clip: {e}", exc_info=True)
            raise

    async def resize_video(
        self,
        input_file: Path,
        target_aspect: AspectRatio,
        quality: ExportQuality = ExportQuality.HIGH,
        output_file: Optional[Path] = None,
    ) -> Path:
        """
        Resize video to target aspect ratio.

        Args:
            input_file: Source video
            target_aspect: Target aspect ratio
            quality: Export quality
            output_file: Output path (auto-generated if None)

        Returns:
            Path to resized video
        """
        logger.info(
            f"Resizing video: {input_file.name} to {target_aspect.value}"
        )

        if not self._ffmpeg_available:
            raise RuntimeError("FFmpeg not available")

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Generate output path if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            aspect_name = target_aspect.value.replace(":", "x")
            output_file = self._exports_dir / \
                f"resized_{aspect_name}_{timestamp}.mp4"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Get target resolution
            resolution = self._get_resolution(target_aspect, quality)
            width, height = resolution

            # Get video bitrate
            bitrate = self._get_bitrate(quality)

            # Build FFmpeg command with smart cropping/padding
            # This uses the scale and pad filters to fit the video
            # into the target aspect ratio without distortion

            if target_aspect == AspectRatio.LANDSCAPE:
                scale_filter = (
                    f"scale={width}:{height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                )
            elif target_aspect == AspectRatio.VERTICAL:
                scale_filter = (
                    f"scale={width}:{height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                )
            elif target_aspect == AspectRatio.SQUARE:
                scale_filter = (
                    f"scale={width}:{height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                )
            else:  # PORTRAIT
                scale_filter = (
                    f"scale={width}:{height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
                )

            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(input_file),
                "-vf", scale_filter,
                "-c:v", "libx264",
                "-preset", "medium",
                "-b:v", f"{bitrate}k",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_file),
            ]

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error = stderr.decode()
                logger.error(f"FFmpeg failed: {error}")
                raise RuntimeError(f"FFmpeg failed: {error}")

            logger.info(f"Video resized: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to resize video: {e}", exc_info=True)
            raise

    async def add_captions(
        self,
        input_file: Path,
        caption_file: Path,
        output_file: Optional[Path] = None,
        font_name: str = "Arial",
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black",
        outline_width: int = 2,
    ) -> Path:
        """
        Add burned-in captions to video.

        Args:
            input_file: Source video
            caption_file: SRT or VTT caption file
            output_file: Output path (auto-generated if None)
            font_name: Font name
            font_size: Font size
            font_color: Font color
            outline_color: Outline color
            outline_width: Outline width

        Returns:
            Path to video with captions
        """
        logger.info(
            f"Adding captions: {
                caption_file.name} to {
                input_file.name}")

        if not self._ffmpeg_available:
            raise RuntimeError("FFmpeg not available")

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if not caption_file.exists():
            raise FileNotFoundError(f"Caption file not found: {caption_file}")

        # Generate output path if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self._exports_dir / f"captioned_{timestamp}.mp4"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Build subtitle filter
            subtitle_filter = (
                f"subtitles='{caption_file}':"
                f"force_style='FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H{self._color_to_hex(font_color)},"
                f"OutlineColour=&H{self._color_to_hex(outline_color)},"
                f"Outline={outline_width}'"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(input_file),
                "-vf", subtitle_filter,
                "-c:v", "libx264",
                "-preset", "medium",
                "-c:a", "copy",  # Copy audio (no re-encode)
                str(output_file),
            ]

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error = stderr.decode()
                logger.error(f"FFmpeg failed: {error}")
                raise RuntimeError(f"FFmpeg failed: {error}")

            logger.info(f"Captions added: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to add captions: {e}", exc_info=True)
            raise

    async def resize_for_platform(
        self,
        input_file: Path,
        platform: str,
        output_file: Optional[Path] = None,
    ) -> Path:
        """
        Resize video using platform-specific preset.

        Args:
            input_file: Source video
            platform: Platform name (youtube, tiktok, instagram, etc.)
            output_file: Output path (auto-generated if None)

        Returns:
            Path to optimized video
        """
        platform_lower = platform.lower()

        # Get preset
        if platform_lower in ["youtube", "youtube_horizontal"]:
            preset = PlatformPreset.YOUTUBE_HORIZONTAL
        elif platform_lower in ["youtube_shorts", "shorts"]:
            preset = PlatformPreset.YOUTUBE_SHORTS
        elif platform_lower == "tiktok":
            preset = PlatformPreset.TIKTOK
        elif platform_lower in ["instagram_reel", "reels"]:
            preset = PlatformPreset.INSTAGRAM_REEL
        elif platform_lower in ["instagram_feed", "instagram"]:
            preset = PlatformPreset.INSTAGRAM_FEED
        elif platform_lower == "facebook":
            preset = PlatformPreset.FACEBOOK
        else:
            raise ValueError(f"Unknown platform: {platform}")

        logger.info(f"Optimizing for {platform}")

        # Generate output path if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                self._exports_dir /
                f"{platform_lower}_{timestamp}.mp4"
            )

        # Resize using preset settings
        resolution = preset["resolution"]
        width: int = resolution[0]  # type: ignore
        height: int = resolution[1]  # type: ignore
        bitrate = preset["bitrate"]
        audio_bitrate = preset["audio_bitrate"]

        try:
            scale_filter = (
                f"scale={width}:{height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(input_file),
                "-vf", scale_filter,
                "-c:v", "libx264",
                "-preset", "medium",
                "-b:v", f"{bitrate}k",
                "-c:a", "aac",
                "-b:a", f"{audio_bitrate}k",
                str(output_file),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error = stderr.decode()
                raise RuntimeError(f"FFmpeg failed: {error}")

            logger.info(f"Optimized for {platform}: {output_file}")
            return output_file

        except Exception as e:
            logger.error(
                f"Failed to optimize for platform: {e}",
                exc_info=True)
            raise

    def _get_resolution(
        self,
        aspect: AspectRatio,
        quality: ExportQuality,
    ) -> Tuple[int, int]:
        """Get resolution for aspect ratio and quality"""
        if quality == ExportQuality.LOW:
            base = 720
        elif quality in [ExportQuality.MEDIUM, ExportQuality.HIGH]:
            base = 1080
        else:  # ULTRA
            base = 2160

        if aspect == AspectRatio.LANDSCAPE:
            return (int(base * 16 / 9), base)
        elif aspect == AspectRatio.VERTICAL:
            return (base, int(base * 16 / 9))
        elif aspect == AspectRatio.SQUARE:
            return (base, base)
        else:  # PORTRAIT
            return (int(base * 4 / 5), base)

    def _get_bitrate(self, quality: ExportQuality) -> int:
        """Get video bitrate for quality level"""
        return {
            ExportQuality.LOW: 2000,
            ExportQuality.MEDIUM: 5000,
            ExportQuality.HIGH: 8000,
            ExportQuality.ULTRA: 20000,
        }[quality]

    def _color_to_hex(self, color: str) -> str:
        """Convert color name to FFmpeg hex format"""
        colors = {
            "white": "FFFFFF",
            "black": "000000",
            "yellow": "FFFF00",
            "red": "FF0000",
            "blue": "0000FF",
            "green": "00FF00",
        }
        return colors.get(color.lower(), "FFFFFF")

    def is_available(self) -> bool:
        """Check if FFmpeg is available"""
        return self._ffmpeg_available

    def set_exports_directory(self, directory: Path) -> None:
        """
        Set the exports output directory.

        Args:
            directory: New exports directory
        """
        directory.mkdir(parents=True, exist_ok=True)
        self._exports_dir = directory
        logger.info(f"Exports directory set to: {directory}")
