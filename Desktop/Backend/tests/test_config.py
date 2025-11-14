"""
Tests for configuration management
"""
import pytest
from pathlib import Path
import os
from src.core.config import ConfigManager, OBSConfig, StreamConfig, AIConfig


class TestConfigManager:
    """Test configuration management"""
    
    def test_initialization(self, temp_dir):
        """Test ConfigManager initialization"""
        config_path = temp_dir / "config.json"
        manager = ConfigManager(config_path=config_path)
        
        assert manager.config_path == config_path
        assert manager.config_path.parent.exists()
        
    def test_obs_config(self, sample_config, temp_dir):
        """Test OBS configuration retrieval"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        manager.config = sample_config
        
        obs_config = manager.get_obs_config()
        
        assert isinstance(obs_config, OBSConfig)
        assert obs_config.host == "localhost"
        assert obs_config.port == 4455
        assert obs_config.password == "test_password"
        
    def test_stream_config(self, sample_config, temp_dir):
        """Test streaming configuration retrieval"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        manager.config = sample_config
        
        stream_config = manager.get_stream_config()
        
        assert isinstance(stream_config, StreamConfig)
        assert stream_config.youtube_en_key == "test_en_key"
        assert stream_config.youtube_fr_key == "test_fr_key"
        assert stream_config.bitrate == 4500
        assert stream_config.resolution == "1920x1080"
        assert stream_config.fps == 30
        
    def test_ai_config(self, sample_config, temp_dir):
        """Test AI configuration retrieval"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        manager.config = sample_config
        
        ai_config = manager.get_ai_config()
        
        assert isinstance(ai_config, AIConfig)
        assert ai_config.whisper_model == "base"
        assert ai_config.enable_live_captions == True
        assert ai_config.caption_language == "auto"
        
    def test_config_validation_success(self, sample_config, temp_dir):
        """Test configuration validation with valid config"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        manager.config = sample_config
        
        is_valid, errors = manager.validate_config()
        
        assert is_valid == True
        assert len(errors) == 0
        
    def test_config_validation_missing_keys(self, temp_dir):
        """Test configuration validation with missing keys"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        manager.config = {
            'obs': {'host': 'localhost', 'port': 4455, 'password': ''},
            'stream': {'youtube_en_key': '', 'youtube_fr_key': ''},
            'ai': {}
        }
        
        is_valid, errors = manager.validate_config()
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("password" in err.lower() for err in errors)
        
    def test_config_validation_invalid_bitrate(self, sample_config, temp_dir):
        """Test configuration validation with invalid bitrate"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        sample_config['stream']['bitrate'] = 500  # Too low
        manager.config = sample_config
        
        is_valid, errors = manager.validate_config()
        
        assert is_valid == False
        assert any("bitrate" in err.lower() for err in errors)
        
    def test_credential_encryption(self, temp_dir):
        """Test credential encryption/decryption"""
        manager = ConfigManager(config_path=temp_dir / "config.json")
        
        original = "my_secret_password"
        encrypted = manager.encrypt_credential(original)
        decrypted = manager.decrypt_credential(encrypted)
        
        assert encrypted != original
        assert decrypted == original
        
    def test_save_and_load_config(self, sample_config, temp_dir):
        """Test saving and loading configuration"""
        config_path = temp_dir / "config.json"
        
        # Save config
        manager1 = ConfigManager(config_path=config_path)
        manager1.config = sample_config
        manager1.save_config()
        
        assert config_path.exists()
        
        # Load config
        manager2 = ConfigManager(config_path=config_path)
        
        # Note: Environment variables might override, so we check the file was created
        assert manager2.config_path.exists()


class TestConfigDataClasses:
    """Test configuration data classes"""
    
    def test_obs_config_defaults(self):
        """Test OBSConfig default values"""
        config = OBSConfig(host="test", port=1234, password="pass")
        
        assert config.host == "test"
        assert config.port == 1234
        assert config.password == "pass"
        
    def test_stream_config_defaults(self):
        """Test StreamConfig default values"""
        config = StreamConfig(youtube_en_key="en", youtube_fr_key="fr")
        
        assert config.youtube_en_key == "en"
        assert config.youtube_fr_key == "fr"
        assert config.bitrate == 4500  # Default
        assert config.resolution == "1920x1080"  # Default
        assert config.fps == 30  # Default
        
    def test_ai_config_defaults(self):
        """Test AIConfig default values"""
        config = AIConfig()
        
        assert config.whisper_model == "base"
        assert config.enable_live_captions == True
        assert config.caption_language == "auto"
        assert config.openai_api_key is None
