# Sony a7 IV End-to-End Test Guide

This concise guide explains how to run Miktos Hub end-to-end tests
with a Sony a7 IV camera. It covers connection options, OBS setup,
running the E2E script, and quick troubleshooting.

## Prerequisites

- HDMI capture card (recommended)
- USB tethering (Imaging Edge)
- Network streaming (RTSP)

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

```bash
python main.py
```

Verify API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Run the E2E test

```bash
python e2e_sony_a7iv_test.py
```

## Troubleshooting

- Camera detection: `system_profiler SPCameraDataType`
- OBS websocket: ensure plugin is installed and port is correct
- API health: `curl -f http://localhost:8000/api/health`

## Quick API commands

```bash
SESSION_ID="<your-session-id>"
curl http://localhost:8000/api/sessions/$SESSION_ID
curl http://localhost:8000/api/cameras/
```

## Links and assets

- [Sony a7 IV Manual](https://www.sony.com/electronics/support/e-mount-body-ilce-7-series/ilce-7m4/manuals)
- [OBS Studio docs](https://obsproject.com/wiki/)
