#!/usr/bin/env python3
"""
Test script to simulate mobile phone SRT streaming.

This script helps test the desktop receiver without needing the mobile app.
It sends a test video file via SRT to the receiver.

Usage:
    # Start receiver first:
    python -m src.mobile.srt_receiver --port 9001
    
    # Then in another terminal, run this test:
    python src/mobile/test_srt_streaming.py --video test_video.mp4
"""

import subprocess
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_srt_stream(video_file: str, host: str = "localhost", port: int = 9001):
    """
    Stream a video file via SRT to test the receiver.
    
    Args:
        video_file: Path to test video file (MP4, MOV, etc.)
        host: Destination host (localhost for testing)
        port: Destination SRT port
    """
    
    logger.info("=" * 60)
    logger.info("StreamLab SRT Streaming Test")
    logger.info("=" * 60)
    logger.info(f"Video file: {video_file}")
    logger.info(f"Streaming to: {host}:{port}")
    logger.info("")
    logger.info("This simulates a mobile phone streaming to the desktop receiver.")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # FFmpeg command to stream video via SRT
    cmd = [
        'ffmpeg',
        '-re',  # Read input at native frame rate (simulate live)
        '-stream_loop', '-1',  # Loop indefinitely
        '-i', video_file,
        '-c:v', 'libx264',  # Re-encode to H.264 (like mobile phone would)
        '-preset', 'ultrafast',  # Fast encoding
        '-tune', 'zerolatency',  # Low latency
        '-b:v', '5M',  # 5 Mbps bitrate (typical mobile)
        '-maxrate', '5M',
        '-bufsize', '10M',
        '-g', '60',  # Keyframe every 60 frames (2 seconds at 30fps)
        '-c:a', 'aac',  # AAC audio
        '-b:a', '128k',
        '-f', 'mpegts',  # MPEG-TS container
        f'srt://{host}:{port}?mode=caller&latency=120000'  # SRT output
    ]
    
    logger.info(f"\nFFmpeg command: {' '.join(cmd)}\n")
    
    try:
        # Run FFmpeg
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("Streaming started! Check the receiver window.")
        logger.info("Press Ctrl+C to stop\n")
        
        # Wait for process
        process.wait()
        
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg:")
        logger.error("  macOS: brew install ffmpeg")
        logger.error("  Linux: apt-get install ffmpeg")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nStopping stream...")
        process.terminate()
        process.wait()
        logger.info("Stream stopped")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def generate_test_video():
    """Generate a simple test pattern video if no video file exists"""
    logger.info("Generating test video with testsrc pattern...")
    
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'testsrc=duration=30:size=1920x1080:rate=30',  # 30 second test pattern
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-y',  # Overwrite
        'test_pattern.mp4'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("Test video generated: test_pattern.mp4")
        return "test_pattern.mp4"
    except Exception as e:
        logger.error(f"Failed to generate test video: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Test SRT streaming (simulates mobile phone)'
    )
    parser.add_argument(
        '--video',
        help='Video file to stream (will generate test pattern if not provided)'
    )
    parser.add_argument('--host', default='localhost', help='Destination host')
    parser.add_argument('--port', type=int, default=9001, help='Destination port')
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate a test pattern video'
    )
    
    args = parser.parse_args()
    
    video_file = args.video
    
    if args.generate or not video_file:
        video_file = generate_test_video()
        if not video_file:
            logger.error("No video file available")
            sys.exit(1)
    
    # Start streaming
    test_srt_stream(video_file, args.host, args.port)


if __name__ == '__main__':
    main()
