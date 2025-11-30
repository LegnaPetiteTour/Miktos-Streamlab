# Camera Pairing Guide

Complete guide for connecting and configuring Sony cameras with Miktos Hub.

## Supported Cameras

✅ **Fully Tested**:

- Sony a7 IV
- Sony a7S III (via Imaging Edge Webcam)

✅ **Compatible** (expected to work):

- Sony a7R IV/V
- Sony a6400/6600
- Sony ZV-E10/E1
- Any Sony camera with USB streaming support

## Part 1: Sony a7 IV Setup

### Hardware Requirements

- Sony a7 IV camera
- USB-C cable (USB 3.0 recommended)
- macOS 11+ or Windows 10+
- Imaging Edge Webcam software

### Step 1: Install Imaging Edge Webcam

1. **Download Software**
   - Visit: <https://imagingedge.sony.net/en-us/ie-desktop.html>
   - Download **Imaging Edge Webcam**
   - Compatible with macOS and Windows

2. **Install**
   - Run the installer
   - Follow installation prompts
   - Restart computer if prompted

3. **Verify Installation**
   - Launch Imaging Edge Webcam
   - You should see the app in your menu bar (macOS) or system tray (Windows)

### Step 2: Configure Camera

1. **Update Camera Firmware**
   - Check current firmware: Menu → Setup → Version
   - Download latest from Sony support site
   - Follow firmware update instructions
   - **Recommended**: Version 2.00 or higher

2. **Set Camera Mode**
   - Power on camera
   - Set dial to **Movie mode** or **Photo mode** (both work)
   - Navigate to: Menu → Network → PC Remote Function
   - Set to **On**

3. **Configure USB Connection**
   - Menu → Network → PC Remote
   - USB Connection Mode: **PC Remote**
   - USB LUN Setting: **Single** (recommended)
   - USB Power Supply: **On** (camera charges while connected)

4. **Optimize Camera Settings**
   - **Image Quality**: Set to highest quality for best stream
   - **Auto Power Off Temp.**: **High** (prevents shutdown during long streams)
   - **HDMI Settings**: Can leave as default (not used for USB streaming)

### Step 3: Connect to Computer

1. **Physical Connection**
   - Use USB-C cable (preferably USB 3.0/3.1)
   - Connect camera to computer USB port
   - **Important**: Use port directly on computer, not a hub if possible

2. **Power On Camera**
   - Turn on camera
   - You should see "PC Remote" indicator on camera screen

3. **Launch Imaging Edge Webcam**
   - Open Imaging Edge Webcam application
   - Camera should appear in device list
   - Select your camera (e.g., "ILCE-7M4" for a7 IV)

4. **Verify Connection**
   - You should see live preview in Imaging Edge window
   - Check video quality and frame rate
   - Adjust camera settings if needed

### Step 4: Add to OBS

1. **Create Video Source**
   - Open OBS Studio
   - In **Sources** panel, click **+**
   - Select **Video Capture Device**

2. **Configure Source**
   - Name: `Sony a7 IV` (or descriptive name)
   - Device: **Imaging Edge Webcam**
   - Resolution: **1920x1080** or **3840x2160** (4K)
   - FPS: **30** (or 60 if camera supports)
   - Use Custom Audio Device: **Off** (unless using camera mic)

3. **Adjust Source**
   - Right-click source → **Transform → Fit to screen**
   - Or manually resize/position

4. **Test**
   - Verify you see camera feed in OBS
   - Check that video is smooth
   - No lag or stuttering

## Part 2: Multi-Camera Setup

### Scenario: Two Sony Cameras

**Goal**: Use two Sony cameras simultaneously for different angles.

#### Hardware Setup

**Camera 1**: Sony a7 IV (Main)

- USB-C → Computer (USB 3.0 port)
- Imaging Edge Webcam

**Camera 2**: Sony a7S III (Secondary)

- USB-C → Computer (different USB 3.0 port)
- Imaging Edge Webcam (separate instance if needed)

#### Configuration

1. **Connect First Camera**
   - Follow Steps 1-4 from Part 1
   - Name OBS source: `Sony a7 IV - Main`

2. **Connect Second Camera**
   - Connect second camera to different USB port
   - Set to PC Remote mode
   - Open second instance of Imaging Edge or use same instance

3. **Add to OBS**
   - Add new **Video Capture Device**
   - Device: Select second camera from Imaging Edge
   - Name: `Sony a7S III - Secondary`

4. **Create Multi-Camera Scenes**

   **Scene: Main Camera**
   - Add source: `Sony a7 IV - Main` (full screen)

   **Scene: Secondary Camera**
   - Add source: `Sony a7S III - Secondary` (full screen)

   **Scene: Picture-in-Picture**
   - Background: `Sony a7 IV - Main` (full screen)
   - Overlay: `Sony a7S III - Secondary` (corner, 25% size)

   **Scene: Side-by-Side**
   - Add both sources
   - Position side by side (each 50% width)

### USB Bandwidth Considerations

**Important**: USB bandwidth is shared per controller.

**Best Practices**:

1. Connect cameras to USB ports on different controllers
2. Use USB 3.0/3.1 ports (blue ports)
3. Avoid USB hubs for cameras
4. If experiencing issues:
   - Reduce resolution (4K → 1080p)
   - Reduce frame rate (60fps → 30fps)
   - Use one camera at 4K, others at 1080p

**Check USB Controllers** (macOS):

- Apple Menu → About This Mac → System Report
- USB → See which ports are on same controller

## Part 3: Camera Settings for Streaming

### Recommended Camera Settings

#### Exposure Settings

**Auto Exposure**: Works well for most scenarios

- Mode: Aperture Priority (A) or Manual (M)
- ISO: Auto (or fixed ISO 400-1600 for indoor)
- Shutter Speed: 1/60s (for 30fps) or 1/120s (for 60fps)
- Aperture: f/2.8 - f/5.6 (balance depth and sharpness)

**Manual Exposure**: For consistent lighting

- ISO: 400-800 (indoor), 100-400 (outdoor)
- Shutter: Double frame rate (1/60 for 30fps, 1/120 for 60fps)
- Aperture: f/2.8 - f/4 (shallow DOF) or f/5.6-f/8 (deeper)

#### White Balance

**Auto WB**: Good for changing lighting
**Preset**: Better for consistent look

- Indoor: 3200K (tungsten) or 4000K (fluorescent)
- Outdoor: 5500K (daylight)
- Custom: Use gray card for perfect accuracy

#### Picture Profile

For streaming, consider:

- **Standard**: Works great out of box
- **PP1-PP10**: For advanced color grading
- **S-Log**: Only if you plan to color grade

**Recommended for Live Streaming**:

- Profile: **Standard**
- Contrast: **0** (neutral)
- Saturation: **+1** to **+2** (slightly enhanced)
- Sharpness: **0** to **+1** (subtle)

### Focus Settings

**Continuous AF**: Best for solo streaming

- AF Area: **Wide** or **Center**
- AF Speed: **5** (balanced)
- AF Sensitivity: **5** (standard)

**Face/Eye AF**: Excellent for talking head

- Enable Face Detection
- Enable Eye AF
- Priority: **Eye** → **Face** → **Body**

**Manual Focus**: Best for fixed position

- Set focus once
- Use focus magnifier to verify
- Lock focus ring if available

### Audio Settings

**Built-in Mic**: Basic quality

- Acceptable for emergency backup
- **Not recommended** for primary audio

**External Mic via Camera**:

- Connect mic to camera multi-interface shoe or mic input
- Set Audio Recording: **On**
- Rec Level: Manual (adjust to avoid clipping)
- Wind Noise Reduction: **On** (if outdoors)

**Recommended**: Use separate audio interface/mic

- Better quality
- More control
- Easier monitoring

## Part 4: Troubleshooting

### Camera Not Detected

**Problem**: Imaging Edge doesn't see camera

**Solutions**:

1. **Check USB Connection**
   - Try different USB cable
   - Use direct port (not hub)
   - Try different USB port

2. **Verify Camera Settings**
   - PC Remote Function: **On**
   - USB Connection Mode: **PC Remote**
   - Camera is powered on

3. **Restart Everything**
   - Quit Imaging Edge Webcam
   - Disconnect camera
   - Restart camera
   - Reconnect camera
   - Relaunch Imaging Edge

4. **Check Permissions** (macOS)
   - System Settings → Privacy & Security
   - Camera: Allow Imaging Edge Webcam

### Camera Disconnects Randomly

**Problem**: Connection drops during stream

**Solutions**:

1. **Disable Auto Power Off**
   - Menu → Setup → Auto Power Off Temp.: **High**
   - Menu → Setup → Auto Off w/ VF: **Off**

2. **Use AC Power**
   - Connect camera to AC adapter
   - Prevents battery drain issues
   - More stable power = more stable connection

3. **Check USB Power**
   - Menu → Network → USB Power Supply: **On**
   - Helps keep camera charged

4. **USB Cable Quality**
   - Use high-quality USB-C cable
   - Shorter cables are more reliable
   - Avoid damaged/worn cables

### Video Lag or Stuttering

**Problem**: Choppy video in OBS

**Solutions**:

1. **Reduce Resolution**
   - Change camera output: 4K → 1080p
   - Less data = smoother stream

2. **Reduce Frame Rate**
   - 60fps → 30fps
   - Significant bandwidth reduction

3. **Close Other Applications**
   - Free up CPU/RAM
   - Close browser tabs
   - Quit unnecessary programs

4. **Check USB Bandwidth**
   - Don't use multiple 4K cameras on same USB controller
   - Move one camera to different USB port/controller

### Image Quality Issues

**Problem**: Soft focus or poor image quality

**Solutions**:

1. **Check Focus**
   - Ensure camera is in focus
   - Use focus magnifier on camera
   - Enable Face/Eye AF

2. **Lens Settings**
   - Clean lens (fingerprints reduce sharpness)
   - Check aperture (too wide = soft, too narrow = diffraction)
   - Optimal aperture: f/2.8 - f/5.6 for most lenses

3. **Camera Settings**
   - Picture Profile sharpness
   - ISO not too high (noise)
   - Proper exposure

4. **Imaging Edge Settings**
   - Verify resolution settings
   - Check compression settings

### Audio Issues

**Problem**: No audio from camera

**Solutions**:

1. **Check OBS Audio Settings**
   - Sources → Camera source → Advanced Audio Properties
   - Verify not muted
   - Check audio monitoring

2. **Camera Audio Settings**
   - Menu → Audio Recording: **On**
   - Rec Level: Adjust manually
   - Check mic is connected (if external)

3. **Use Separate Audio**
   - Recommended for better quality
   - USB microphone or audio interface
   - Sync in OBS if needed

## Part 5: Advanced Configurations

### Remote Camera Control

You can control some camera settings remotely:

**Via Imaging Edge Desktop** (not Webcam):

- Download Imaging Edge Desktop suite
- Includes Remote app for camera control
- Adjust settings without touching camera

**Via Miktos Hub** (future feature):

- Planned API for camera control
- Adjust exposure, focus, etc.
- Automated workflows

### Multi-Camera Synchronization

For professional productions:

1. **Timecode Sync**
   - Use external timecode generator
   - Sync all cameras to same timecode
   - Essential for multi-camera editing

2. **Genlock** (for high-end setups)
   - Sync camera frame rates precisely
   - Requires genlock-capable cameras
   - Eliminates frame tearing in switches

3. **Manual Sync** (simple method)
   - Clap or flash at start
   - Align audio waveforms in post
   - Good enough for most live streams

### Network Cameras

For cameras in different locations:

**NDI** (Network Device Interface):

- Convert camera feed to NDI signal
- Stream over local network
- Use NDI plugin in OBS

**RTMP/RTSP**:

- Some cameras support network streaming
- Pull stream into OBS
- Adds latency (1-3 seconds)

## Best Practices

1. **Always Test First**
   - Test setup before going live
   - Verify all cameras work
   - Check focus, exposure, audio

2. **Label Everything**
   - Name cameras clearly in OBS
   - Label physical cables
   - Document your setup

3. **Have Backups**
   - Extra USB cables
   - Backup power supplies
   - Second computer if possible

4. **Monitor During Stream**
   - Watch OBS stats
   - Check camera battery (if not on AC)
   - Monitor temperature (cameras can overheat)

5. **Maintain Equipment**
   - Clean lenses regularly
   - Update firmware
   - Check cable connections

## Next Steps

- 🎬 [OBS Setup Guide](OBS_SETUP.md) - Configure OBS for streaming
- 🔧 [API Examples](API_EXAMPLES.md) - Control cameras via API
- 🐛 [Troubleshooting](TROUBLESHOOTING.md) - Common issues

---

**Need help?** Check the [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.
