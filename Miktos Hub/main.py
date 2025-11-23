"""
Miktos Hub - Main Entry Point

Run the Miktos Hub API server.

Usage:
    python main.py                  # Run with default settings
    python main.py --host 0.0.0.0   # Run on all interfaces
    python main.py --port 8080      # Run on custom port
    python main.py --reload         # Enable auto-reload for development
"""
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('miktos_hub.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    import uvicorn
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Miktos Hub API Server'
    )
    parser.add_argument(
        '--host', default='0.0.0.0', help='Host to bind to'
    )
    parser.add_argument(
        '--port', type=int, default=8000, help='Port to bind to'
    )
    parser.add_argument(
        '--reload', action='store_true', help='Enable auto-reload'
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("MIKTOS HUB")
    logger.info("Professional Live Streaming Orchestration Platform")
    logger.info("=" * 60)
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info("=" * 60)

    # Run server
    try:
        uvicorn.run(
            "hub_api.server:create_app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            factory=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
