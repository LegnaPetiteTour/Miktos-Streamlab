# Sony a7 IV End-to-End Test Guide

This concise guide explains how to run Miktos Hub end-to-end tests
with a Sony a7 IV camera. It covers connection options, OBS setup,
running the E2E script, and quick troubleshooting.

## Prerequisites

### Connection options

- HDMI capture card (recommended)
- USB tethering (Imaging Edge)
- Network streaming (RTSP)

### Quick checks

1. Confirm camera is powered on and has video output enabled.
1. Confirm OBS is installed and can see the video source.

## OBS + obs-websocket

1. Install OBS Studio:

```bash
brew install --cask obs
```bash
SESSION_ID="<your-session-id>"
curl http://localhost:8000/api/sessions/$SESSION_ID

curl http://localhost:8000/api/cameras/
# Sony a7 IV End-to-End Test Guide

This concise guide explains how to run Miktos Hub end-to-end tests
with a Sony a7 IV camera. It covers connection options, OBS setup,
running the E2E script, and quick troubleshooting.

## Prerequisites

### Connection options

- HDMI capture card (recommended)
- USB tethering (Imaging Edge)
- Network streaming (RTSP)

### Quick checks

1. Confirm camera is powered on and has video output enabled.
1. Confirm OBS is installed and can see the video source.

## OBS + obs-websocket

1. Install OBS Studio:

```bash
brew install --cask obs
```

1. Install obs-websocket (v5+):

- Download: [obs-websocket releases](https://github.com/obsproject/obs-websocket/releases)
- Install and restart OBS

1. Configure obs-websocket:

- OBS → Tools → obs-websocket Settings
- Recommended: port `4455`; enable authentication for shared hosts

1. Verify connection:

```bash
curl -sS http://localhost:4455 || true
```

## Start Miktos Hub

1. Start server:

```bash
python main.py
```

1. Verify API docs:

- Visit [Miktos Hub API docs](http://localhost:8000/docs)

## Run the E2E test

```bash
python e2e_sony_a7iv_test.py
```

The test validates:

1. Server health
1. Camera discovery
1. Session creation and persistence
1. OBS integration (scenes)
1. Optional RTMP destination setup

## Troubleshooting

### Camera detection

```bash
system_profiler SPCameraDataType
```

### OBS websocket

- Confirm obs-websocket plugin is installed and running.
- Check port and password in the plugin settings.

### API health

```bash
curl -f http://localhost:8000/api/health || echo "server down"
```

Restart the server:

```bash
python main.py
```

## Quick API commands

```bash
SESSION_ID="<your-session-id>"
curl http://localhost:8000/api/sessions/$SESSION_ID

curl http://localhost:8000/api/cameras/
```

## Links and assets

- [Sony a7 IV Manual](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7m4/manuals)
- [OBS Studio docs](https://obsproject.com/wiki/)
- Add screenshots to `docs/images/` and reference them here.

---

If you want, I can (1) add example OBS scene JSON, (2) add image
placeholders, or (3) run the markdownlint report and fix any remaining
issues automatically. Which would you like next?

