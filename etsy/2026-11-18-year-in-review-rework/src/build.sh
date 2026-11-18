#!/bin/bash
set -e
cd "$(dirname "$0")"
EX="../out/Couples Money Year in Review 2027 - EXAMPLE (filled in).xlsx"; BL="../out/Couples Money Year in Review 2027 - BLANK (start here).xlsx"
python3 build_xlsx.py "$EX" && python3 build_xlsx.py "$BL" blank
R=$(ls /root/.claude/skills/synced/*/xlsx/scripts/recalc.py | head -1)
python3 $R "$EX" 120; python3 $R "$BL" 120
