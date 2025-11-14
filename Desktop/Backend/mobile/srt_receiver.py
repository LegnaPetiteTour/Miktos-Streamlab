"""
SRT Receiver for Mobile Camera Streams - Week 1 MVP

Receives H.264 video from mobile phones via SRT and outputs to OBS.

Features:
- Single camera support (Week 1 MVP)
- FFmpeg-based SRT reception
- SDL window preview or virtual camera output
- Latency monitoring
- Auto-reconnect

Usage:
    # Start receiver
    python -m src.mobile.srt_receiver --port 9001 --mode window
    
    # Or use programmatically
    receiver = SRTReceiver(port=9001)
    await receiver.start()
"""

import asyncio
import subprocess
import logging
import os
import signal
import sys
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import time
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StreamStats:
    """Statistics for received stream"""
    start_time: datetime = field(default_factory=datetime.now)
    bytes_received: int = 0
    frames_received: int = 0
    last_frame_time: Optional[datetime] = None
    connection_lost_count: int = 0
    avg_bitrate_mbps: float = 0.0
    current_latency_ms: int = 0


class SRTReceiver:
    """
    Receives SRT streams from mobile cameras.
    
    Week 1 MVP Implementation:
    - Single stream support
    - FFmpeg subprocess for SRT reception and decoding
    - SDL window output (viewable) or virtual camera (for OBS)
    - Basic error handling and reconnect
    
    Future enhancements (Week 2+):
    - Multi-camera support
    - Advanced quality adaptation
    - Tally feedback to phones
    - Network quality monitoring
    """
    
    def __init__(
        self,
        port: int = 9001,
        output_mode: str = 'window',  # 'window' or 'virtual_camera'
        latency_ms: int = 120,
        reconnect_delay: int = 5,
    ):
        """
        Initialize SRT receiver.
        
        Args:
            port: SRT listening port
            output_mode: 'window' (SDL preview) or 'virtual_camera' (OBS integration)
            latency_ms: SRT latency buffer in milliseconds
            reconnect_delay: Seconds to wait before reconnecting after failure
        """
        self.port = port
        self.output_mode = output_mode
        self.latency_ms = latency_ms
        self.reconnect_delay = reconnect_delay
        
        self.process: Optional[subprocess.Popen] = None
        self.stats = StreamStats()
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start receiving SRT stream"""
        if self.is_running:
            logger.warning("Receiver already running")
            return
            
        logger.info("=" * 60)
        logger.info("🎥 Starting Mobile Camera SRT Receiver")
        logger.info(f"   Port: {self.port}")
        logger.info(f"   Output: {self.output_mode}")
        logger.info(f"   Latency: {self.latency_ms}ms")
        logger.info("=" * 60)
        
        self.is_running = True
        self.stats = StreamStats()  # Reset stats
        
        try:
            # Check FFmpeg availability
            if not self._check_ffmpeg():
                raise RuntimeError("FFmpeg with SRT support not found")
            
            # Start main reception loop with auto-reconnect
            await self._reception_loop()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Received interrupt signal")
            await self.stop()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop receiving"""
        if not self.is_running:
            return
            
        logger.info("🛑 Stopping receiver...")
        self.is_running = False
        self._shutdown_event.set()
        
        if self.process:
            try:
                logger.info("Terminating FFmpeg process...")
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("✅ FFmpeg terminated cleanly")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  FFmpeg did not terminate, killing...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping process: {e}")
            finally:
                self.process = None
        
        logger.info("✅ Receiver stopped")
    
    async def _reception_loop(self):
        """Main reception loop with auto-reconnect"""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                logger.info(f"📡 Waiting for mobile camera on port {self.port}...")
                await self._start_ffmpeg_receiver()
                
            except Exception as e:
                self.stats.connection_lost_count += 1
                logger.error(f"❌ Stream failed: {e}")
                logger.info(f"🔄 Reconnecting in {self.reconnect_delay} seconds...")
                
                # Wait before reconnecting (unless shutdown requested)
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.reconnect_delay
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Reconnect
    
    async def _start_ffmpeg_receiver(self):
        """Start FFmpeg process to receive SRT and display"""
        cmd = self._build_ffmpeg_command()
        
        logger.info("🎬 Starting FFmpeg receiver:")
        logger.info(f"   {' '.join(cmd)}")
        
        # Set SDL window title via environment variable
        env = os.environ.copy()
        env['SDL_VIDEO_WINDOW_POS'] = 'center'
        env['SDL_VIDEO_CENTERED'] = '1'
        
        # Start FFmpeg process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env=env
        )
        
        logger.info("✅ FFmpeg process started")
        logger.info("📺 Waiting for stream...")
        
        # Monitor process output in background
        monitor_task = asyncio.create_task(
            self._monitor_ffmpeg_output()
        )
        
        # Wait for process to complete (or error)
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.process.wait
        )
        
        # Cancel monitor task
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # Check exit code
        if self.process.returncode != 0:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"FFmpeg exited with code {self.process.returncode}: {stderr}")
    
    async def _monitor_ffmpeg_output(self):
        """Monitor FFmpeg stderr for status updates"""
        if not self.process or not self.process.stderr:
            return
            
        try:
            while self.is_running:
                # Read line from stderr
                line = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.process.stderr.readline
                )
                
                if not line:
                    break
                    
                line = line.strip()
                
                # Parse FFmpeg output for useful info
                if 'frame=' in line:
                    # Example: frame=  120 fps= 30 q=-1.0 size=    1024kB time=00:00:04.00 bitrate=2097.2kbits/s
                    self._parse_ffmpeg_status(line)
                    
                elif 'error' in line.lower() or 'warning' in line.lower():
                    logger.warning(f"FFmpeg: {line}")
                    
        except Exception as e:
            logger.debug(f"Monitor stopped: {e}")
    
    def _parse_ffmpeg_status(self, line: str):
        """Parse FFmpeg status line to extract stats"""
        try:
            # Extract frame count
            if 'frame=' in line:
                frame_str = line.split('frame=')[1].split()[0].strip()
                self.stats.frames_received = int(frame_str)
                self.stats.last_frame_time = datetime.now()
            
            # Extract bitrate
            if 'bitrate=' in line:
                bitrate_str = line.split('bitrate=')[1].split()[0].strip()
                if 'kbits/s' in bitrate_str:
                    kbps = float(bitrate_str.replace('kbits/s', ''))
                    self.stats.avg_bitrate_mbps = kbps / 1000
            
            # Log progress every 100 frames
            if self.stats.frames_received % 100 == 0 and self.stats.frames_received > 0:
                logger.info(
                    f"📊 Receiving: {self.stats.frames_received} frames, "
                    f"{self.stats.avg_bitrate_mbps:.1f} Mbps"
                )
                
        except Exception as e:
            logger.debug(f"Failed to parse FFmpeg status: {e}")
    
    def _build_ffmpeg_command(self) -> List[str]:
        """Build FFmpeg command for receiving SRT stream"""
        # Input: SRT listener
        srt_input = f"srt://0.0.0.0:{self.port}?mode=listener&latency={self.latency_ms}"
        
        # Base command
        cmd = [
            'ffmpeg',
            '-hide_banner',  # Less verbose output
            '-loglevel', 'info',
            '-i', srt_input,  # Input: SRT stream
        ]
        
        # Output based on mode
        if self.output_mode == 'window':
            # SDL window output (simple preview)
            # Note: SDL window title must be set via environment variable
            cmd.extend([
                '-f', 'sdl',  # SDL video output
                '-'  # Output to stdout (SDL opens window)
            ])
            
        elif self.output_mode == 'virtual_camera':
            # Virtual camera output for OBS (platform-specific)
            if sys.platform == 'darwin':  # macOS
                # On macOS, use AVFoundation virtual camera
                # Note: Requires additional setup
                logger.warning("⚠️  Virtual camera not yet implemented for macOS")
                logger.warning("    Using window mode instead")
                cmd.extend([
                    '-f', 'sdl',
                    '-'
                ])
            elif sys.platform == 'linux':
                # On Linux, use v4l2loopback
                cmd.extend([
                    '-f', 'v4l2',
                    '/dev/video10'  # Virtual camera device
                ])
            else:  # Windows
                logger.warning("⚠️  Virtual camera not yet implemented for Windows")
                logger.warning("    Using window mode instead")
                cmd.extend([
                    '-f', 'sdl',
                    '-'
                ])
        else:
            raise ValueError(f"Invalid output mode: {self.output_mode}")
        
        return cmd
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg with SRT support is available"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.error("FFmpeg not found")
                return False
            
            # Check for SRT support
            if 'libsrt' not in result.stdout and '--enable-libsrt' not in result.stdout:
                logger.error("❌ FFmpeg does not have SRT support")
                logger.error("   Please install FFmpeg with SRT:")
                logger.error("   • macOS: brew install ffmpeg")
                logger.error("   • Linux: apt install ffmpeg libsrt-dev")
                logger.error("   • Or compile with --enable-libsrt")
                return False
            
            logger.info("✅ FFmpeg with SRT support found")
            return True
            
        except FileNotFoundError:
            logger.error("❌ FFmpeg not found in PATH")
            logger.error("   Please install FFmpeg with SRT support")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking FFmpeg: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get current stream statistics"""
        uptime = (datetime.now() - self.stats.start_time).total_seconds()
        
        return {
            'is_running': self.is_running,
            'port': self.port,
            'uptime_seconds': uptime,
            'frames_received': self.stats.frames_received,
            'avg_bitrate_mbps': self.stats.avg_bitrate_mbps,
            'connection_lost_count': self.stats.connection_lost_count,
            'last_frame_time': self.stats.last_frame_time.isoformat() if self.stats.last_frame_time else None,
        }


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Mobile Camera SRT Receiver - Week 1 MVP'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9001,
        help='SRT listening port (default: 9001)'
    )
    parser.add_argument(
        '--mode',
        choices=['window', 'virtual_camera'],
        default='window',
        help='Output mode: window (preview) or virtual_camera (OBS)'
    )
    parser.add_argument(
        '--latency',
        type=int,
        default=120,
        help='SRT latency in milliseconds (default: 120)'
    )
    
    args = parser.parse_args()
    
    # Create and start receiver
    receiver = SRTReceiver(
        port=args.port,
        output_mode=args.mode,
        latency_ms=args.latency
    )
    
    try:
        await receiver.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
    finally:
        await receiver.stop()


if __name__ == '__main__':
    asyncio.run(main())
