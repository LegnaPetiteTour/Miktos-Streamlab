"""
Configuration Management Module
Handles all application configuration with validation and type safety.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuration for streaming settings"""
    youtube_en_key: str
    youtube_fr_key: str
    bitrate: int = 4500
    resolution: str = "1920x1080"
    fps: int = 30
    audio_bitrate: int = 128


@dataclass
class OBSConfig:
    """Configuration for OBS connection"""
    host: str = "localhost"
    port: int = 4455
    password: str = ""


@dataclass
class AIConfig:
    """Configuration for AI features"""
    whisper_model: str = "base"
    enable_live_captions: bool = True
    caption_language: str = "auto"
    openai_api_key: Optional[str] = None


class ConfigManager:
    """
    Manages application configuration with encryption and validation.

    Features:
    - Environment variable loading
    - Credential encryption
    - Configuration validation
    - Hot-reload support
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".miktos" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption key
        self._setup_encryption()

        # Load configuration
        self.config = self._load_config()

    def _setup_encryption(self):
        """Setup encryption for sensitive credentials"""
        key_file = self.config_path.parent / ".key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(key_file, 0o600)

        self.cipher = Fernet(key)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment"""
        config = {}

        # Load from file if exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)

        # Override with environment variables
        config['obs'] = {
            'host': os.getenv('OBS_HOST', config.get('obs', {}).get('host', 'localhost')),
            'port': int(os.getenv('OBS_PORT', config.get('obs', {}).get('port', 4455))),
            'password': os.getenv('OBS_PASSWORD', config.get('obs', {}).get('password', '')),
        }

        config['stream'] = {
            'youtube_en_key': os.getenv('YOUTUBE_EN_KEY', ''),
            'youtube_fr_key': os.getenv('YOUTUBE_FR_KEY', ''),
            'bitrate': int(os.getenv('STREAM_BITRATE', 4500)),
            'resolution': os.getenv('STREAM_RESOLUTION', '1920x1080'),
            'fps': int(os.getenv('STREAM_FPS', 30)),
            'audio_bitrate': int(os.getenv('AUDIO_BITRATE', 128)),
        }

        config['ai'] = {
            'whisper_model': os.getenv('WHISPER_MODEL', 'base'),
            'enable_live_captions': os.getenv('ENABLE_CAPTIONS', 'true').lower() == 'true',
            'caption_language': os.getenv('CAPTION_LANG', 'auto'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
        }

        return config

    def get_obs_config(self) -> OBSConfig:
        """Get OBS configuration"""
        obs_data = self.config.get('obs', {})
        return OBSConfig(**obs_data)

    def get_stream_config(self) -> StreamConfig:
        """Get streaming configuration"""
        stream_data = self.config.get('stream', {})
        return StreamConfig(**stream_data)

    def get_ai_config(self) -> AIConfig:
        """Get AI configuration"""
        ai_data = self.config.get('ai', {})
        return AIConfig(**ai_data)

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Configuration saved to {self.config_path}")

    def encrypt_credential(self, value: str) -> str:
        """Encrypt a credential"""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_credential(self, encrypted_value: str) -> str:
        """Decrypt a credential"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate configuration
        Returns: (is_valid, error_messages)
        """
        errors = []

        # Check OBS config
        obs = self.get_obs_config()
        if not obs.password:
            errors.append("OBS password not configured")

        # Check streaming config
        stream = self.get_stream_config()
        if not stream.youtube_en_key:
            errors.append("YouTube EN stream key not configured")
        if not stream.youtube_fr_key:
            errors.append("YouTube FR stream key not configured")

        if stream.bitrate < 1000 or stream.bitrate > 10000:
            errors.append(f"Invalid bitrate: {stream.bitrate} (should be 1000-10000)")

        return len(errors) == 0, errors


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get or create global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
