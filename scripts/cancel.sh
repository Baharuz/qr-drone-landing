#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Uçuş döngüsü isteği okuyup LAND uygular. Simülasyon süreci kapatılmaz.
touch logs/cancel_requested
printf 'İptal isteği yazıldı; uçuş terminalinde iniş doğrulamasını bekleyin.\n'
