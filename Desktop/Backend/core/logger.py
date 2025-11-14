"""
Structured Logging Module
Provides comprehensive logging with JSON output and rotation.
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console output for better readability"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build message
        message = f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name:20s} | {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)

        return message


def setup_logging(
    log_dir: Path = Path.home() / ".miktos" / "logs",
    level: str = "INFO",
    enable_json: bool = False,
    enable_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup application logging

    Args:
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON formatted file logging
        enable_console: Enable console logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured root logger
    """
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)

    # File handler - standard logs
    standard_log = log_dir / "miktos.log"
    file_handler = RotatingFileHandler(
        standard_log,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)

    if enable_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    root_logger.addHandler(file_handler)

    # Error log file (only errors and critical)
    error_log = log_dir / "errors.log"
    error_handler = RotatingFileHandler(
        error_log,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n'
        )
    )
    root_logger.addHandler(error_handler)

    logging.info("Logging initialized")
    logging.info(f"Log directory: {log_dir}")
    logging.info(f"Log level: {level}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class StreamLogger:
    """Special logger for stream events"""

    def __init__(self, log_dir: Path = Path.home() / ".miktos" / "logs"):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('stream')

    def log_stream_start(self, channels: list[str], metadata: Dict[str, Any]):
        """Log stream start event"""
        self.logger.info(f"Stream started on channels: {', '.join(channels)}")

        # Write to stream log
        stream_log = self.log_dir / f"stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stream_log, 'w') as f:
            json.dump({
                'event': 'start',
                'timestamp': datetime.utcnow().isoformat(),
                'channels': channels,
                'metadata': metadata
            }, f, indent=2)

    def log_stream_end(self, duration: float, metadata: Dict[str, Any]):
        """Log stream end event"""
        self.logger.info(f"Stream ended. Duration: {duration:.1f}s")

    def log_stream_error(self, error: str, metadata: Dict[str, Any]):
        """Log stream error"""
        self.logger.error(f"Stream error: {error}")
