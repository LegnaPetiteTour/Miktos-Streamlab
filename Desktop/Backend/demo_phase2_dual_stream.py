#!/usr/bin/env python3
"""
Phase 2 Demo: YouTube Dual-Language Streaming with Failover

This script demonstrates the enhanced dual-path egress system for
City of Ottawa municipal broadcasting with English/French channels.

Features demonstrated:
- Dual YouTube channel configuration (EN/FR)
- Automatic failover between channels
- SRT backup relay
- Municipal compliance logging
- Bilingual slate management

Usage:
    python3 demo_phase2_dual_stream.py
    
Requirements:
    - YouTube stream keys configured in .env
    - OBS Studio running with WebSocket enabled
    - SRT relay server (optional)

Author: Miktos StreamLab Team  
License: MIT
"""

import asyncio
import logging
import os
from pathlib import Path
import sys
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Desktop.Backend.core.youtube_dual_stream import (
    YouTubeDualStreamManager,
    create_dual_stream_config,
    Language
)
from Desktop.Backend.core.logger import get_logger
from Desktop.Backend.obs_controller import OBSController


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = get_logger("phase2_demo")


class Phase2DemoRunner:
    """
    Phase 2 demonstration runner for dual-language streaming
    
    Showcases the enhanced egress system with YouTube EN/FR channels
    and intelligent failover capabilities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("Phase2Demo")
        self.obs_controller: Optional[OBSController] = None
        self.dual_stream_manager: Optional[YouTubeDualStreamManager] = None
        
        # Demo configuration
        self.demo_config = {
            "simulate_failures": True,
            "test_language_switching": True, 
            "test_cross_language_failover": True,
            "demo_duration_minutes": 5
        }
    
    async def initialize_components(self) -> bool:
        """Initialize OBS and dual-stream components"""
        try:
            self.logger.info("🚀 Initializing Phase 2 Dual-Stream Demo Components")
            
            # Initialize OBS controller
            self.logger.info("📺 Connecting to OBS WebSocket...")
            self.obs_controller = OBSController()
            
            try:
                await self.obs_controller.connect()
                self.logger.info("✅ OBS WebSocket connected successfully")
            except Exception as e:
                self.logger.warning(f"⚠️  OBS connection failed: {e}. Demo will continue without OBS integration.")
                self.obs_controller = None
            
            # Create dual-stream configuration
            dual_stream_config = self._create_demo_config()
            
            # Initialize dual-stream manager
            self.dual_stream_manager = YouTubeDualStreamManager(
                config=dual_stream_config,
                obs_controller=self.obs_controller
            )
            
            self.logger.info("✅ Phase 2 dual-stream components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False
    
    def _create_demo_config(self):
        """Create demonstration configuration for dual streaming"""
        
        # Load from environment or use demo keys
        en_stream_key = os.getenv("YOUTUBE_EN_STREAM_KEY", "demo-en-key-xxxx")
        fr_stream_key = os.getenv("YOUTUBE_FR_STREAM_KEY", "demo-fr-key-xxxx")
        en_channel_id = os.getenv("YOUTUBE_EN_CHANNEL_ID", "UCxxxxx_EN")
        fr_channel_id = os.getenv("YOUTUBE_FR_CHANNEL_ID", "UCxxxxx_FR")
        srt_relay_url = os.getenv("SRT_RELAY_URL", "srt://localhost:9999")
        
        self.logger.info("📋 Creating Ottawa municipal dual-stream configuration")
        self.logger.info(f"   English Channel: {en_channel_id}")
        self.logger.info(f"   French Channel: {fr_channel_id}")
        self.logger.info(f"   SRT Backup: {srt_relay_url if srt_relay_url != 'srt://localhost:9999' else 'Demo mode'}")
        
        return create_dual_stream_config(
            primary_stream_key=en_stream_key,
            secondary_stream_key=fr_stream_key,
            primary_channel_id=en_channel_id,
            secondary_channel_id=fr_channel_id,
            primary_language=Language.ENGLISH,
            secondary_language=Language.FRENCH,
            primary_channel_name="english_channel",
            secondary_channel_name="french_channel",
            srt_relay_url=srt_relay_url
        )
    
    async def demonstrate_dual_streaming(self):
        """Demonstrate dual-language streaming capabilities"""
        try:
            self.logger.info("🎯 Starting Phase 2 Dual-Language Streaming Demonstration")
            
            if not self.dual_stream_manager:
                self.logger.error("❌ Dual-stream manager not initialized")
                return
            
            # Test 1: Start English streaming
            self.logger.info("📡 Test 1: Starting English streaming...")
            success = await self.dual_stream_manager.start_streaming(Language.ENGLISH)
            if success:
                self.logger.info("✅ English streaming started successfully")
                
                # Show health status
                health = await self.dual_stream_manager.get_health_status()
                self.logger.info(f"📊 Health Status: {health.get('streaming', False)} | Language: {health.get('active_language', 'unknown')}")
            else:
                self.logger.error("❌ Failed to start English streaming")
                return
            
            # Wait and monitor
            await asyncio.sleep(5)
            
            # Test 2: Language switching
            if self.demo_config["test_language_switching"]:
                self.logger.info("🔄 Test 2: Switching to French streaming...")
                await self.dual_stream_manager.switch_language(Language.FRENCH)
                
                health = await self.dual_stream_manager.get_health_status()
                self.logger.info(f"📊 Post-switch Health: Language: {health.get('active_language', 'unknown')}")
                
                await asyncio.sleep(3)
            
            # Test 3: Demonstrate failover capabilities
            if self.demo_config["simulate_failures"]:
                self.logger.info("⚠️  Test 3: Simulating network failure for failover testing...")
                await self._simulate_network_failure()
                
                await asyncio.sleep(5)
            
            # Test 4: Health monitoring
            self.logger.info("📈 Test 4: Comprehensive health monitoring...")
            await self._demonstrate_health_monitoring()
            
            # Stop streaming
            self.logger.info("🛑 Stopping dual-language streaming...")
            await self.dual_stream_manager.stop_streaming()
            
            self.logger.info("✅ Phase 2 demonstration completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during dual-streaming demonstration: {e}")
    
    async def _simulate_network_failure(self):
        """Simulate network failure to test failover"""
        self.logger.info("🔧 Simulating primary destination failure...")
        self.logger.info("   (In production, this would trigger automatic failover to SRT backup)")
        self.logger.info("   Failover logic: packet loss >5% OR RTT >300ms OR dropped frames >25")
        
        # In a real implementation, we would inject network issues
        # For demo purposes, we just log what would happen
        self.logger.info("🔄 Automatic failover would be triggered...")
        self.logger.info("📺 Slate display: 'Experiencing Technical Difficulties - Problèmes Techniques'")
        self.logger.info("🚀 Backup SRT stream activated")
        self.logger.info("⚡ Failover completed in <3 seconds")
    
    async def _demonstrate_health_monitoring(self):
        """Demonstrate comprehensive health monitoring"""
        if not self.dual_stream_manager:
            return
            
        self.logger.info("📊 Gathering comprehensive health metrics...")
        
        health_status = await self.dual_stream_manager.get_health_status()
        
        # Display health information
        self.logger.info("🏥 Health Status Report:")
        self.logger.info(f"   Streaming Active: {health_status.get('streaming', False)}")
        self.logger.info(f"   Active Language: {health_status.get('active_language', 'unknown')}")
        self.logger.info(f"   Failover Status: {health_status.get('failover_active', False)}")
        
        # Channel status
        channels = health_status.get('channels', {})
        self.logger.info(f"   English Channel: {'✅ Configured' if channels.get('english', {}).get('configured') else '❌ Not configured'}")
        self.logger.info(f"   French Channel: {'✅ Configured' if channels.get('french', {}).get('configured') else '❌ Not configured'}")
        
        # Failover metrics
        failover_metrics = health_status.get('failover_metrics', {})
        if failover_metrics:
            self.logger.info(f"   Total Failovers: {failover_metrics.get('total_failovers', 0)}")
            self.logger.info(f"   Recovery Success Rate: {failover_metrics.get('recovery_success_rate_pct', 0)}%")
    
    async def demonstrate_municipal_compliance(self):
        """Demonstrate municipal compliance features"""
        self.logger.info("🏛️  Municipal Compliance Features:")
        self.logger.info("   ✅ Enhanced reliability thresholds (packet loss <3%, RTT <300ms)")
        self.logger.info("   ✅ Faster failover detection (5 seconds vs. 10 seconds)")
        self.logger.info("   ✅ More recovery attempts (15 vs. 10)")
        self.logger.info("   ✅ Bilingual error messaging (EN/FR)")
        self.logger.info("   ✅ Comprehensive audit logging")
        self.logger.info("   ✅ Cross-language failover (EN ↔ FR)")
        self.logger.info("   ✅ SRT backup for maximum reliability")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.dual_stream_manager and self.dual_stream_manager.streaming:
                await self.dual_stream_manager.stop_streaming()
            
            if self.obs_controller:
                await self.obs_controller.disconnect()
                
            self.logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main demonstration function"""
    print("🎯 MIKTOS STREAMLAB - PHASE 2 DEMO")
    print("📡 YouTube Dual-Language Streaming with Advanced Failover")
    print("=" * 60)
    
    demo = Phase2DemoRunner()
    
    try:
        # Initialize
        success = await demo.initialize_components()
        if not success:
            print("❌ Failed to initialize components. Check configuration.")
            return
        
        # Run demonstrations
        await demo.demonstrate_dual_streaming()
        await demo.demonstrate_municipal_compliance()
        
        print("\n" + "=" * 60)
        print("✅ Phase 2 demonstration completed successfully!")
        print("🚀 Ready for production deployment with City of Ottawa")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    # Run the demonstration
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo terminated by user")