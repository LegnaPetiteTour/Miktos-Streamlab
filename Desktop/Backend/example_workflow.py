#!/usr/bin/env python3
"""
Example: Automated Stream Workflow
===================================

This example demonstrates a complete automated streaming workflow:
1. Connect to OBS
2. Show intro scene
3. Switch to main content
4. Show outro scene
5. Stop streaming

Customize this for your needs!
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from obs_controller import OBSController


def countdown(seconds, message="Starting in"):
    """Display a countdown"""
    for i in range(seconds, 0, -1):
        print(f"\r{message} {i} seconds...", end='', flush=True)
        time.sleep(1)
    print(f"\r{message} NOW!         ")


def main():
    print("=" * 60)
    print("  AUTOMATED STREAM WORKFLOW EXAMPLE")
    print("=" * 60)
    print()
    
    # Configuration
    INTRO_DURATION = 10  # seconds
    MAIN_DURATION = 30   # seconds
    OUTRO_DURATION = 10  # seconds
    
    # Connect to OBS
    print("📡 Connecting to OBS...")
    obs = OBSController()
    
    if not obs.connect():
        print("❌ Failed to connect to OBS")
        return 1
    
    print()
    
    try:
        # Get scenes
        scenes = obs.get_scenes()
        print(f"📋 Available scenes: {', '.join(scenes)}")
        print()
        
        # Check if required scenes exist
        required_scenes = ['Intro', 'Main', 'Outro']
        for scene in required_scenes:
            if scene not in scenes:
                print(f"⚠️  Warning: Scene '{scene}' not found")
                print(f"   Available scenes: {scenes}")
                print(f"   Create '{scene}' scene in OBS or edit this script")
                print()
        
        # Start workflow
        print("🎬 Starting automated workflow...")
        print()
        
        # Phase 1: Intro
        print("Phase 1: INTRO")
        print("-" * 40)
        
        if 'Intro' in scenes:
            obs.switch_scene('Intro')
            print("  ✓ Switched to Intro scene")
        else:
            print("  ⚠️  Intro scene not found, using current scene")
        
        print("  ▶️  Starting stream...")
        obs.start_streaming()
        
        print("  🔴 Starting recording...")
        obs.start_recording()
        
        print(f"  ⏱️  Intro duration: {INTRO_DURATION} seconds")
        countdown(INTRO_DURATION, "Intro ending in")
        print()
        
        # Phase 2: Main Content
        print("Phase 2: MAIN CONTENT")
        print("-" * 40)
        
        if 'Main' in scenes:
            obs.switch_scene('Main')
            print("  ✓ Switched to Main scene")
        
        print(f"  ⏱️  Main content duration: {MAIN_DURATION} seconds")
        print("  💬 This is where your main content would be...")
        countdown(MAIN_DURATION, "Main content ending in")
        print()
        
        # Phase 3: Outro
        print("Phase 3: OUTRO")
        print("-" * 40)
        
        if 'Outro' in scenes:
            obs.switch_scene('Outro')
            print("  ✓ Switched to Outro scene")
        
        print(f"  ⏱️  Outro duration: {OUTRO_DURATION} seconds")
        countdown(OUTRO_DURATION, "Outro ending in")
        print()
        
        # Stop everything
        print("🛑 Stopping stream and recording...")
        obs.stop_recording()
        obs.stop_streaming()
        print("  ✓ Stopped")
        print()
        
        print("=" * 60)
        print("  ✅ WORKFLOW COMPLETE!")
        print("=" * 60)
        print()
        print("Your recording has been saved to OBS's recording folder.")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("Stopping stream and recording...")
        
        try:
            if obs.is_streaming():
                obs.stop_streaming()
            if obs.is_recording():
                obs.stop_recording()
        except:
            pass
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Try to stop streaming/recording on error
        try:
            if obs.is_streaming():
                obs.stop_streaming()
            if obs.is_recording():
                obs.stop_recording()
        except:
            pass
        
        return 1
    
    finally:
        # Always disconnect
        obs.disconnect()
    
    return 0


if __name__ == "__main__":
    print()
    print("⚠️  NOTE: This will start streaming and recording!")
    print("   Make sure you're ready or modify the script to test without streaming.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        sys.exit(main())
    else:
        print("Cancelled.")
        sys.exit(0)
