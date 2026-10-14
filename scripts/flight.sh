#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export GZ_PARTITION=qr_landing_project GZ_IP=127.0.0.1
exec .venv/bin/python src/flight.py
