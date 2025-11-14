"""
Setup script for Miktos StreamLab
Provides backward compatibility with older pip versions
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="miktos-streamlab",
    version="0.1.0",
    author="Miktos StreamLab Team",
    description="Professional municipal broadcasting platform with AI-powered bilingual transcription",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/miktos-streamlab",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "obs-websocket-py>=1.0",
        "openai-whisper>=20231117",
        "speedtest-cli>=2.1.3",
        "psutil>=5.9.0",
        "cryptography>=41.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "numpy>=1.24.0",
        "torch>=2.0.0",
        "ffmpeg-python>=0.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.3",
        ],
        "ui": [
            "PyQt6>=6.5.0",
            "pyqtgraph>=0.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "miktos=src.main:main",
        ],
    },
)
