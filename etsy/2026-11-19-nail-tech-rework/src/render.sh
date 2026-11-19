#!/bin/bash
# Build EXAMPLE + BLANK, recalc both (0 errors expected), render every EXAMPLE tab to PNG in $W
set -e
cd "$(dirname "$0")"; mkdir -p ../out
EX="../out/Nail Tech Income Expense Tracker - EXAMPLE (filled in).xlsx"
BL="../out/Nail Tech Income Expense Tracker - BLANK (start here).xlsx"
python3 build_xlsx.py "$EX"; python3 build_xlsx.py "$BL" blank
R=$(ls /root/.claude/skills/synced/*/xlsx/scripts/recalc.py | head -1)
python3 $R "$EX" 180 | grep -E '"status"|total_errors|total_formulas'
python3 $R "$BL" 180 | grep -E '"status"|total_errors|total_formulas'
W=${W:-/tmp/claude-0/nailw}; mkdir -p $W; rm -f $W/ex*.png $W/bl*.png
cp "$EX" $W/ex.xlsx; cp "$BL" $W/bl.xlsx
(cd $W && soffice --headless --convert-to pdf ex.xlsx >/dev/null 2>&1 && soffice --headless --convert-to pdf bl.xlsx >/dev/null 2>&1)
pdftoppm -r 70 -png $W/ex.pdf $W/ex 2>/dev/null; pdftoppm -r 70 -png $W/bl.pdf $W/bl 2>/dev/null
echo rendered $(ls $W/ex-*.png | wc -l) example pages
