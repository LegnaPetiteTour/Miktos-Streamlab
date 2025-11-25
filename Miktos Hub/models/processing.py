"""
Media Processing Models

Defines audio and video processors that can be chained in a pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import uuid


class ProcessorType(Enum):
    """Types of media processors"""
    # Audio processors
    NOISE_REDUCTION = "noise_reduction"
    AUDIO_NORMALIZE = "audio_normalize"
    COMPRESSOR = "compressor"
    LIMITER = "limiter"
    EQ = "eq"
    GATE = "gate"
    REVERB = "reverb"

    # Video processors
    COLOR_CORRECTION = "color_correction"
    EXPOSURE_ADJUST = "exposure_adjust"
    SHARPENING = "sharpening"
    DENOISE = "denoise"
    STABILIZATION = "stabilization"
    FACE_DETECTION = "face_detection"
    AUTO_FRAMING = "auto_framing"
    SUPER_RESOLUTION = "super_resolution"


@dataclass
class MediaProcessor:
    """
    Base class for all media processors.

    Processors are stackable - they can be chained in a pipeline.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: ProcessorType = ProcessorType.NOISE_REDUCTION

    # State
    enabled: bool = True

    # Configuration (processor-specific)
    config: Dict[str, Any] = field(default_factory=dict)

    # Processing stats
    frames_processed: int = 0
    processing_time_ms: float = 0.0

    def reset_stats(self):
        """Reset processing statistics"""
        self.frames_processed = 0
        self.processing_time_ms = 0.0


@dataclass
class AudioProcessor(MediaProcessor):
    """
    Audio-specific processor.

    Example configurations:

        # Noise reduction
        AudioProcessor(
            name="Remove Background Noise",
            type=ProcessorType.NOISE_REDUCTION,
            config={
                "strength": 0.5,  # 0.0 - 1.0
                "model": "rnnoise",  # "rnnoise", "nvidia_broadcast"
            }
        )

        # Normalize/Loudness
        AudioProcessor(
            name="Normalize Audio",
            type=ProcessorType.AUDIO_NORMALIZE,
            config={
                "target_lufs": -16.0,  # Broadcast standard
                "true_peak_limit": -1.0,  # dBTP
            }
        )

        # Compressor
        AudioProcessor(
            name="Compress Dynamic Range",
            type=ProcessorType.COMPRESSOR,
            config={
                "threshold": -20.0,  # dB
                "ratio": 3.0,  # 3:1
                "attack": 5.0,  # ms
                "release": 50.0,  # ms
            }
        )
    """

    # Audio-specific settings
    sample_rate: int = 48000
    channels: int = 2  # Stereo

    def supports_mono(self) -> bool:
        """Check if processor supports mono audio"""
        return self.type in [
            ProcessorType.NOISE_REDUCTION,
            ProcessorType.AUDIO_NORMALIZE,
            ProcessorType.GATE,
        ]


@dataclass
class VideoProcessor(MediaProcessor):
    """
    Video-specific processor.

    Example configurations:

        # Color correction
        VideoProcessor(
            name="Auto Color Balance",
            type=ProcessorType.COLOR_CORRECTION,
            config={
                "brightness": 0.0,  # -1.0 to 1.0
                "contrast": 1.0,  # 0.0 to 2.0
                "saturation": 1.0,  # 0.0 to 2.0
                "auto_white_balance": True,
            }
        )

        # Sharpening
        VideoProcessor(
            name="Sharpen Image",
            type=ProcessorType.SHARPENING,
            config={
                "strength": 0.5,  # 0.0 - 1.0
                "radius": 1.0,  # pixels
            }
        )

        # Face detection + auto-framing
        VideoProcessor(
            name="Auto-Frame on Faces",
            type=ProcessorType.AUTO_FRAMING,
            config={
                "enable_face_detection": True,
                "padding": 0.2,  # 20% padding around face
                "smooth_transitions": True,
                "min_face_size": 50,  # pixels
            }
        )
    """

    # Video-specific settings
    resolution: str = "1920x1080"
    fps: int = 30

    # GPU acceleration (if supported)
    use_gpu: bool = True
    gpu_device_id: int = 0

    def requires_gpu(self) -> bool:
        """Check if processor requires GPU"""
        return self.type in [
            ProcessorType.SUPER_RESOLUTION,
            ProcessorType.FACE_DETECTION,
            ProcessorType.AUTO_FRAMING,
            ProcessorType.STABILIZATION,
        ]
