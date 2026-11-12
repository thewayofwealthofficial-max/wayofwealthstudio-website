#!/bin/bash
# build both, recalc, render sample to PNG per tab
set -e
cd "$(dirname "$0")"; mkdir -p out
python3 build_xlsx.py out/sample.xlsx && python3 build_xlsx.py out/blank.xlsx blank
R=$(ls /root/.claude/skills/synced/*/xlsx/scripts/recalc.py)
python3 $R out/sample.xlsx 90 | grep -E '"status"|total_formulas'; python3 $R out/blank.xlsx 90 | grep -E '"status"'
cd out && rm -f sample.pdf tab-*.png && soffice --headless --convert-to pdf sample.xlsx >/dev/null 2>&1 && pdfinfo sample.pdf | grep Pages && pdftoppm -r 110 -png sample.pdf tab
