#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export GZ_PARTITION=qr_landing_project GZ_IP=127.0.0.1
instance="${QR_SITL_INSTANCE:-0}"
exec .venv/bin/python src/camera.py --topic "/world/qr_test/model/x500_mono_cam_down_${instance}/link/camera_link/sensor/imager/image" --seconds 3600 --show "$@"
