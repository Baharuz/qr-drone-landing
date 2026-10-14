#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd "$(dirname "$0")/.." && pwd)"
target_dir="${QR_PROJECT_DIR:-$HOME/qr-drone-landing}"
mkdir -p "$target_dir"
# Mevcut dosyaları üzerine yazmadan korur; venv yeni konumda yeniden oluşturulur.
python3 - "$source_dir" "$target_dir" <<'PY'
from pathlib import Path
import shutil,sys
src,dst=map(Path,sys.argv[1:])
for f in src.rglob('*'):
 rel=f.relative_to(src)
 if any(part in {'.git','.venv','runtime','logs','__pycache__'} for part in rel.parts): continue
 target=dst/rel
 if f.is_dir(): target.mkdir(parents=True,exist_ok=True)
 elif not target.exists(): shutil.copy2(f,target)
PY
bash "$target_dir/scripts/setup.sh"
printf 'Proje hazır: %s\n' "$target_dir"
