#!/bin/bash
# Build EXAMPLE + BLANK, recalc both, hand-check, render every EXAMPLE tab to PNG (150 dpi) in ../renders
set -e
cd "$(dirname "$0")"; mkdir -p ../out ../renders
EX="../out/US Self-Employed Tax Tracker 2026-2027 - EXAMPLE (filled in).xlsx"
BL="../out/US Self-Employed Tax Tracker 2026-2027 - BLANK (start here).xlsx"
python3 build_xlsx.py "$EX" && python3 build_xlsx.py "$BL" blank
R=$(ls /root/.claude/skills/synced/*/xlsx/scripts/recalc.py | head -1)
python3 $R "$EX" 120 > ../review/recalc_example.json; python3 $R "$BL" 120 > ../review/recalc_blank.json
grep -E '"status"|total_errors|total_formulas' ../review/recalc_example.json ../review/recalc_blank.json
T=$(mktemp -d); cp "$EX" $T/example.xlsx
(cd $T && soffice --headless --convert-to pdf example.xlsx >/dev/null 2>&1)
rm -f ../renders/*.png
python3 - "$T/example.pdf" <<'P'
import sys, subprocess, re
pdf = sys.argv[1]
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
seen = {}; prev = None
for p in range(1, n + 1):
    t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-layout', pdf, '-'], capture_output=True, text=True).stdout
    m = re.search(r'TAB (\d+) OF \d+\s+·\s+([A-Z0-9 \-/]+?)\s+·', t)
    key = f'{int(m.group(1)):02d}-{m.group(2).strip().lower().replace(" ", "-")}' if m else None
    if key is None:
        key = prev; seen[key] += 1; key = f'{key}-p{seen[key]}'
    else:
        seen[key] = 1; prev = key
    subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', '-f', str(p), '-l', str(p), pdf, f'../renders/{key}'])
    print(p, key)
P
