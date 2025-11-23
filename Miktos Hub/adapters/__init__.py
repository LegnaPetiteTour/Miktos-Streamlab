"""
Adapters Package

Provides adapters to bridge between Hub models and Backend models.
"""

from .model_adapters import ModelAdapter
from .obs_engine import OBSEngineAdapter

__all__ = ['ModelAdapter', 'OBSEngineAdapter']
