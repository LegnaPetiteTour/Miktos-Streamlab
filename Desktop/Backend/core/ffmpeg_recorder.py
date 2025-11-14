"""
FFmpeg Recorder for ISO Track Recording

Manages FFmpeg processes for recording individual isolated audio/video sources.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """FFmpeg process states"""

    IDLE = "idle"
    STARTING = "starting"
    RECORDING = "recording"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class FFmpegProcess:
    """
    Represents a running FFmpeg process.

    Attributes:
        process_id: Unique process identifier
        source_name: Source being recorded
        output_path: Output file path
        state: Current process state
        process: Asyncio subprocess
        start_time: Process start timestamp
        error: Error message if failed
    """

    process_id: str
    source_name: str
    output_path: Path
    state: ProcessState = ProcessState.IDLE
    process: Optional[asyncio.subprocess.Process] = None
    start_time: Optional[float] = None
    error: Optional[str] = None

    def is_running(self) -> bool:
        """Check if process is running"""
        return (
            self.process is not None
            and self.process.returncode is None
        )


class FFmpegRecorder:
    """
    Manages FFmpeg recording processes for ISO tracks.

    Features:
    - Start/stop individual track recording
    - Process monitoring
    - Error recovery
    - Resource management
    """

    def __init__(self) -> None:
        """Initialize FFmpeg recorder"""
        self.processes: Dict[str, FFmpegProcess] = {}
        self.logger = logging.getLogger(__name__)

    async def start_track_recording(
        self,
        track_id: str,
        source_url: str,
        output_path: Path,
        format_settings: Dict,
    ) -> bool:
        """
        Start recording a single track.

        Args:
            track_id: Unique track identifier
            source_url: Source URL/device to record from
            output_path: Output file path
            format_settings: FFmpeg format settings

        Returns:
            True if started successfully
        """
        try:
            if track_id in self.processes:
                self.logger.warning(
                    f"Track {track_id} already recording"
                )
                return False

            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                source_url, output_path, format_settings
            )

            self.logger.info(
                f"Starting FFmpeg for track {track_id}: {' '.join(cmd)}"
            )

            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Create process record
            ffmpeg_proc = FFmpegProcess(
                process_id=track_id,
                source_name=source_url,
                output_path=output_path,
                state=ProcessState.RECORDING,
                process=process,
                start_time=asyncio.get_event_loop().time(),
            )

            self.processes[track_id] = ffmpeg_proc

            # Start monitoring task
            asyncio.create_task(
                self._monitor_process(track_id)
            )

            self.logger.info(f"Track {track_id} recording started")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to start track {track_id}: {e}"
            )
            return False

    async def stop_track_recording(self, track_id: str) -> bool:
        """
        Stop recording a single track.

        Args:
            track_id: Track identifier

        Returns:
            True if stopped successfully
        """
        try:
            if track_id not in self.processes:
                self.logger.warning(
                    f"Track {track_id} not recording"
                )
                return False

            ffmpeg_proc = self.processes[track_id]

            if not ffmpeg_proc.is_running():
                self.logger.warning(
                    f"Track {track_id} process not running"
                )
                return False

            # Send termination signal
            ffmpeg_proc.state = ProcessState.STOPPING
            ffmpeg_proc.process.terminate()  # type: ignore[union-attr]

            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    ffmpeg_proc.process.wait(),  # type: ignore[union-attr]
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                # Force kill if doesn't stop gracefully
                self.logger.warning(
                    f"Track {track_id} didn't stop gracefully, killing"
                )
                ffmpeg_proc.process.kill()  # type: ignore[union-attr]
                await ffmpeg_proc.process.wait()  # type: ignore[union-attr]

            ffmpeg_proc.state = ProcessState.STOPPED
            self.logger.info(f"Track {track_id} recording stopped")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to stop track {track_id}: {e}"
            )
            return False

    async def stop_all_tracks(self) -> None:
        """Stop all recording tracks"""
        track_ids = list(self.processes.keys())

        for track_id in track_ids:
            await self.stop_track_recording(track_id)

    def get_process_state(
        self, track_id: str
    ) -> Optional[ProcessState]:
        """Get state of specific process"""
        if track_id not in self.processes:
            return None

        return self.processes[track_id].state

    def is_recording(self, track_id: str) -> bool:
        """Check if specific track is recording"""
        if track_id not in self.processes:
            return False

        ffmpeg_proc = self.processes[track_id]
        return (
            ffmpeg_proc.state == ProcessState.RECORDING
            and ffmpeg_proc.is_running()
        )

    async def _monitor_process(self, track_id: str) -> None:
        """Monitor FFmpeg process for errors"""
        try:
            ffmpeg_proc = self.processes[track_id]

            if not ffmpeg_proc.process:
                return

            # Wait for process to complete
            returncode = await ffmpeg_proc.process.wait()

            # Check if stopped intentionally
            if ffmpeg_proc.state == ProcessState.STOPPING:
                ffmpeg_proc.state = ProcessState.STOPPED
                return

            # Process ended unexpectedly
            if returncode != 0:
                # Read error output
                stderr = (
                    await ffmpeg_proc.process.stderr.read()  # type: ignore[union-attr]
                )
                error_msg = stderr.decode("utf-8", errors="ignore")

                ffmpeg_proc.state = ProcessState.ERROR
                ffmpeg_proc.error = error_msg

                self.logger.error(
                    f"Track {track_id} failed: {error_msg}"
                )
            else:
                ffmpeg_proc.state = ProcessState.STOPPED
                self.logger.info(f"Track {track_id} completed")

        except Exception as e:
            self.logger.error(
                f"Monitor failed for track {track_id}: {e}"
            )

            if track_id in self.processes:
                self.processes[track_id].state = ProcessState.ERROR
                self.processes[track_id].error = str(e)

    def _build_ffmpeg_command(
        self,
        source_url: str,
        output_path: Path,
        format_settings: Dict,
    ) -> list:
        """Build FFmpeg command line"""
        cmd = ["ffmpeg"]

        # Input settings
        if "input_format" in format_settings:
            cmd.extend(["-f", format_settings["input_format"]])

        cmd.extend(["-i", source_url])

        # Video settings
        if "video_codec" in format_settings:
            cmd.extend(["-c:v", format_settings["video_codec"]])

        if "resolution" in format_settings:
            cmd.extend(["-s", format_settings["resolution"]])

        if "fps" in format_settings:
            cmd.extend(["-r", str(format_settings["fps"])])

        if "video_bitrate" in format_settings:
            cmd.extend(["-b:v", format_settings["video_bitrate"]])

        # Audio settings
        if "audio_codec" in format_settings:
            cmd.extend(["-c:a", format_settings["audio_codec"]])

        if "audio_bitrate" in format_settings:
            cmd.extend(["-b:a", format_settings["audio_bitrate"]])

        if "audio_sample_rate" in format_settings:
            cmd.extend(["-ar", str(format_settings["audio_sample_rate"])])

        # Output format
        if "format" in format_settings:
            cmd.extend(["-f", format_settings["format"]])

        # Overwrite output file
        cmd.append("-y")

        # Output path
        cmd.append(str(output_path))

        return cmd
