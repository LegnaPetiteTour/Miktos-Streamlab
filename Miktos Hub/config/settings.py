"""
Configuration Management for Miktos Hub

Centralized settings for all Hub components.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OBSConfig:
    """OBS Studio connection settings"""
    host: str = "localhost"
    port: int = 4455
    password: str = "DmMpVONSo86VU3Eh"
    auto_connect: bool = True
    canvas_width: int = 1920
    canvas_height: int = 1080
    auto_create_scenes: bool = True


@dataclass
class PathConfig:
    """File system paths"""
    # Existing backend directory
    backend_dir: Path = Path(
        "/Users/atorrella/Desktop/Miktos Streamlab/Desktop/Backend")

    # Output directories
    recordings_dir: Path = Path(
        "/Users/atorrella/Desktop/Miktos Streamlab/recordings")
    transcripts_dir: Path = Path(
        "/Users/atorrella/Desktop/Miktos Streamlab/transcripts")
    exports_dir: Path = Path(
        "/Users/atorrella/Desktop/Miktos Streamlab/exports")

    # Log directory
    logs_dir: Path = Path("/Users/atorrella/Desktop/Miktos Streamlab/logs")

    def __post_init__(self):
        """Ensure all directories exist"""
        for dir_attr in [
            "recordings_dir",
            "transcripts_dir",
            "exports_dir",
                "logs_dir"]:
            directory = getattr(self, dir_attr)
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class CameraConfig:
    """Camera discovery and registration settings"""
    enable_mdns_discovery: bool = True
    mdns_service_name: str = "_miktos-camera._tcp.local."
    default_srt_port: int = 8888
    default_port: int = 8554
    health_check_interval_seconds: float = 5.0
    connection_timeout_seconds: float = 30.0
    auto_register_discovered: bool = True


@dataclass
class StreamingConfig:
    """Streaming settings"""
    default_bitrate_kbps: int = 6000
    default_fps: int = 30
    default_keyframe_interval_seconds: int = 2
    enable_hardware_encoding: bool = True

    # Failover settings
    enable_failover: bool = True
    failover_threshold_failures: int = 3
    failover_recovery_threshold: int = 5


@dataclass
class ProcessingConfig:
    """Audio/video processing settings"""
    enable_audio_enhancement: bool = True
    enable_video_enhancement: bool = True

    # Audio settings
    target_lufs: float = -16.0  # Broadcast standard
    audio_sample_rate: int = 48000
    audio_channels: int = 2

    # Video settings
    enable_gpu_acceleration: bool = True
    gpu_device_id: int = 0


@dataclass
class TranscriptionConfig:
    """Transcription service settings"""
    enabled: bool = True
    default_language: str = "en"
    supported_languages: list = field(
        default_factory=lambda: ["en", "fr", "es"]
    )
    model_size: str = "medium"  # tiny, base, small, medium, large
    use_gpu: bool = True


@dataclass
class APIConfig:
    """API server settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    enable_cors: bool = True
    allowed_origins: list = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173"])


@dataclass
class HubConfig:
    """Main Hub configuration"""
    # Component configs
    obs: OBSConfig = field(default_factory=OBSConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    transcription: TranscriptionConfig = field(
        default_factory=TranscriptionConfig)
    api: APIConfig = field(default_factory=APIConfig)

    # General settings
    log_level: str = "INFO"
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> "HubConfig":
        """
        Create configuration from environment variables

        Supported env vars:
        - HUB_LOG_LEVEL
        - HUB_DEBUG
        - OBS_HOST
        - OBS_PORT
        - OBS_PASSWORD
        - API_HOST
        - API_PORT
        """
        config = cls()

        # General
        if log_level := os.getenv("HUB_LOG_LEVEL"):
            config.log_level = log_level
        if debug := os.getenv("HUB_DEBUG"):
            config.debug_mode = debug.lower() in ["true", "1", "yes"]

        # OBS
        if obs_host := os.getenv("OBS_HOST"):
            config.obs.host = obs_host
        if obs_port := os.getenv("OBS_PORT"):
            config.obs.port = int(obs_port)
        if obs_password := os.getenv("OBS_PASSWORD"):
            config.obs.password = obs_password

        # API
        if api_host := os.getenv("API_HOST"):
            config.api.host = api_host
        if api_port := os.getenv("API_PORT"):
            config.api.port = int(api_port)

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "obs": {
                "host": self.obs.host,
                "port": self.obs.port,
                "auto_connect": self.obs.auto_connect,
            },
            "paths": {
                "backend_dir": str(self.paths.backend_dir),
                "recordings_dir": str(self.paths.recordings_dir),
                "transcripts_dir": str(self.paths.transcripts_dir),
                "exports_dir": str(self.paths.exports_dir),
                "logs_dir": str(self.paths.logs_dir),
            },
            "camera": {
                "enable_mdns_discovery": self.camera.enable_mdns_discovery,
                "default_srt_port": self.camera.default_srt_port,
            },
            "streaming": {
                "default_bitrate_kbps": self.streaming.default_bitrate_kbps,
                "default_fps": self.streaming.default_fps,
                "enable_failover": self.streaming.enable_failover,
            },
            "processing": {
                "enable_audio_enhancement": (
                    self.processing.enable_audio_enhancement
                ),
                "enable_video_enhancement": (
                    self.processing.enable_video_enhancement
                ),
                "enable_gpu_acceleration": (
                    self.processing.enable_gpu_acceleration
                ),
            },
            "transcription": {
                "enabled": self.transcription.enabled,
                "default_language": self.transcription.default_language,
                "model_size": self.transcription.model_size,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
            },
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
        }


# Singleton instance
_config_instance: Optional[HubConfig] = None


def get_config() -> HubConfig:
    """Get the global Hub configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = HubConfig.from_env()
    return _config_instance


def reload_config() -> HubConfig:
    """Reload configuration from environment"""
    global _config_instance
    _config_instance = HubConfig.from_env()
    return _config_instance
