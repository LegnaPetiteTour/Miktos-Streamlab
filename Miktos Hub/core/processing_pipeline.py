"""
Processing Pipeline - Chain audio/video processors

This allows stacking enhancement effects in a clean, testable way.
Each processor is independent and can be added/removed/reordered.
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProcessorType(Enum):
    """Types of media processors"""
    AUDIO = "audio"
    VIDEO = "video"
    METADATA = "metadata"


@dataclass
class ProcessorConfig:
    """Configuration for a processor"""
    name: str
    type: ProcessorType
    enabled: bool = True
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class IMediaProcessor(Protocol):
    """
    Interface for media processors

    All processors (audio, video) implement this interface.
    They receive data, process it, and return modified data.
    """

    @property
    def name(self) -> str:
        """Unique name for this processor"""
        ...

    @property
    def type(self) -> ProcessorType:
        """Type of processor (audio/video/metadata)"""
        ...

    async def process(self, data: Any, metadata: Dict[str, Any]) -> Any:
        """
        Process media data

        Args:
            data: Input data (audio samples, video frames, etc.)
            metadata: Context information (sample rate, frame rate, etc.)

        Returns:
            Processed data
        """
        ...

    async def initialize(self, config: ProcessorConfig) -> bool:
        """Initialize processor with configuration"""
        ...

    async def cleanup(self) -> None:
        """Clean up resources"""
        ...


class ProcessingPipeline:
    """
    Chain of media processors

    Example audio chain:
        Input → Noise Reduction → Compression → Normalization → Output

    Example video chain:
        Input → Color Correction → Sharpening → Stabilization → Output
    """

    def __init__(self, name: str):
        self.name = name
        self._processors: List[IMediaProcessor] = []
        self._enabled = True

        logger.info(f"Created processing pipeline: {name}")

    def add_processor(
        self,
        processor: IMediaProcessor,
        position: Optional[int] = None
    ) -> None:
        """
        Add a processor to the pipeline

        Args:
            processor: Processor to add
            position: Optional position in pipeline (default: end)
        """
        if position is None:
            self._processors.append(processor)
            logger.info(f"Added processor '{processor.name}' at end of pipeline '{self.name}'")
        else:
            self._processors.insert(position, processor)
            logger.info(f"Added processor '{processor.name}' at position {position} in pipeline '{self.name}'")

    def remove_processor(self, processor_name: str) -> bool:
        """
        Remove a processor by name

        Args:
            processor_name: Name of processor to remove

        Returns:
            True if removed
        """
        original_count = len(self._processors)
        self._processors = [p for p in self._processors if p.name != processor_name]

        if len(self._processors) < original_count:
            logger.info(f"Removed processor '{processor_name}' from pipeline '{self.name}'")
            return True

        logger.warning(f"Processor '{processor_name}' not found in pipeline '{self.name}'")
        return False

    def get_processor(self, processor_name: str) -> Optional[IMediaProcessor]:
        """Get a processor by name"""
        for processor in self._processors:
            if processor.name == processor_name:
                return processor
        return None

    def list_processors(self) -> List[str]:
        """List all processor names in order"""
        return [p.name for p in self._processors]

    async def process(self, data: Any, metadata: Dict[str, Any]) -> Any:
        """
        Process data through all processors in sequence

        Args:
            data: Input data
            metadata: Context metadata

        Returns:
            Processed data
        """
        if not self._enabled:
            logger.debug(f"Pipeline '{self.name}' is disabled, passing data through")
            return data

        current_data = data

        for processor in self._processors:
            try:
                current_data = await processor.process(current_data, metadata)
            except Exception as e:
                logger.error(
                    f"Error in processor '{processor.name}' of pipeline '{self.name}': {e}",
                    exc_info=True
                )
                # Continue with unprocessed data if processor fails
                # This prevents one bad processor from breaking the whole pipeline

        return current_data

    def enable(self) -> None:
        """Enable the pipeline"""
        self._enabled = True
        logger.info(f"Enabled pipeline: {self.name}")

    def disable(self) -> None:
        """Disable the pipeline (data passes through unchanged)"""
        self._enabled = False
        logger.info(f"Disabled pipeline: {self.name}")

    def is_enabled(self) -> bool:
        """Check if pipeline is enabled"""
        return self._enabled

    def clear(self) -> None:
        """Remove all processors"""
        count = len(self._processors)
        self._processors.clear()
        logger.info(f"Cleared {count} processors from pipeline '{self.name}'")

    async def initialize_all(self, configs: List[ProcessorConfig]) -> bool:
        """
        Initialize all processors in the pipeline

        Args:
            configs: List of processor configurations

        Returns:
            True if all initialized successfully
        """
        success = True

        for processor, config in zip(self._processors, configs):
            try:
                if not await processor.initialize(config):
                    logger.error(f"Failed to initialize processor: {processor.name}")
                    success = False
            except Exception as e:
                logger.error(f"Error initializing processor '{processor.name}': {e}")
                success = False

        return success

    async def cleanup_all(self) -> None:
        """Clean up all processors"""
        for processor in self._processors:
            try:
                await processor.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up processor '{processor.name}': {e}")


class ProcessingPipelineManager:
    """
    Manages multiple processing pipelines

    Example usage:
        audio_pipeline = manager.create_pipeline("audio_main", ProcessorType.AUDIO)
        audio_pipeline.add_processor(NoiseReductionProcessor())
        audio_pipeline.add_processor(NormalizationProcessor())

        video_pipeline = manager.create_pipeline("video_main", ProcessorType.VIDEO)
        video_pipeline.add_processor(ColorCorrectionProcessor())
    """

    def __init__(self):
        self._pipelines: Dict[str, ProcessingPipeline] = {}
        logger.info("ProcessingPipelineManager initialized")

    def create_pipeline(self, name: str) -> ProcessingPipeline:
        """
        Create a new pipeline

        Args:
            name: Pipeline name

        Returns:
            Created pipeline
        """
        if name in self._pipelines:
            logger.warning(f"Pipeline '{name}' already exists, returning existing")
            return self._pipelines[name]

        pipeline = ProcessingPipeline(name)
        self._pipelines[name] = pipeline

        logger.info(f"Created pipeline: {name}")
        return pipeline

    def get_pipeline(self, name: str) -> Optional[ProcessingPipeline]:
        """Get a pipeline by name"""
        return self._pipelines.get(name)

    def delete_pipeline(self, name: str) -> bool:
        """
        Delete a pipeline

        Args:
            name: Pipeline to delete

        Returns:
            True if deleted
        """
        if name in self._pipelines:
            del self._pipelines[name]
            logger.info(f"Deleted pipeline: {name}")
            return True

        logger.warning(f"Pipeline not found: {name}")
        return False

    def list_pipelines(self) -> List[str]:
        """List all pipeline names"""
        return list(self._pipelines.keys())

    async def cleanup_all(self) -> None:
        """Clean up all pipelines"""
        for pipeline in self._pipelines.values():
            await pipeline.cleanup_all()

        logger.info("Cleaned up all pipelines")


# Example processor implementations (these will be replaced with actual implementations)

class ExampleNoiseReductionProcessor:
    """Example audio noise reduction processor"""

    @property
    def name(self) -> str:
        return "noise_reduction"

    @property
    def type(self) -> ProcessorType:
        return ProcessorType.AUDIO

    async def process(self, data: Any, metadata: Dict[str, Any]) -> Any:
        # Placeholder: In real implementation, use RNNoise or NVIDIA Broadcast
        logger.debug("Processing audio with noise reduction")
        return data

    async def initialize(self, config: ProcessorConfig) -> bool:
        logger.info("Initialized noise reduction processor")
        return True

    async def cleanup(self) -> None:
        logger.info("Cleaned up noise reduction processor")


class ExampleColorCorrectionProcessor:
    """Example video color correction processor"""

    @property
    def name(self) -> str:
        return "color_correction"

    @property
    def type(self) -> ProcessorType:
        return ProcessorType.VIDEO

    async def process(self, data: Any, metadata: Dict[str, Any]) -> Any:
        # Placeholder: In real implementation, use OpenCV or GPU shader
        logger.debug("Processing video with color correction")
        return data

    async def initialize(self, config: ProcessorConfig) -> bool:
        logger.info("Initialized color correction processor")
        return True

    async def cleanup(self) -> None:
        logger.info("Cleaned up color correction processor")
