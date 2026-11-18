#!/bin/bash
# render every EXAMPLE (or BLANK with arg 'blank') tab to PNG (150 dpi) in ../renders[-blank]
set -e
cd "$(dirname "$0")"
if [ "$1" = blank ]; then F="../out/Couples Money Year in Review 2027 - BLANK (start here).xlsx"; O=../renders-blank; else F="../out/Couples Money Year in Review 2027 - EXAMPLE (filled in).xlsx"; O=../renders; fi
mkdir -p $O; rm -f $O/*.png
T=$(mktemp -d); cp "$F" $T/x.xlsx
(cd $T && soffice --headless --convert-to pdf x.xlsx >/dev/null 2>&1)
python3 - "$T/x.pdf" $O <<'P'
import sys, subprocess, re
pdf, O = sys.argv[1], sys.argv[2]
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
seen = {}; prev = 'x'
for p in range(1, n + 1):
    t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-layout', pdf, '-'], capture_output=True, text=True).stdout
    m = re.search(r'TAB (\d+) OF \d+\s+·\s+([A-Z0-9 \-/]+?)\s+·', t)
    if m: key = f'{int(m.group(1)):02d}-{m.group(2).strip().lower().replace(" ", "-")}'; seen[key] = 1; prev = key
    else: seen[prev] = seen.get(prev, 1) + 1; key = f'{prev}-p{seen[prev]}'
    subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', '-f', str(p), '-l', str(p), pdf, f'{O}/{key}'])
    print(p, key)
P
cp $T/x.pdf $O/all.pdf
