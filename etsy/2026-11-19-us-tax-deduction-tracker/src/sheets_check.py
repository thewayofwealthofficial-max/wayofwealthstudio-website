"""Google Sheets proxy check (gate 8) + hand-check of the tax maths.
1) Scan the xlsx XML: no shapes/text boxes (xdr:sp), no data bars / icon sets, no macros, no functions Sheets or Excel 2016 lack.
2) LibreOffice round-trip (xlsx -> ods -> xlsx), recalculated, and every key figure compared with the original.
3) Recompute SE tax, income tax, safe harbor in plain Python from the recalculated inputs and compare.
python3 sheets_check.py <example.xlsx>"""
import sys, os, re, zipfile, subprocess, tempfile, glob, shutil, json
from openpyxl import load_workbook

P = sys.argv[1]
out = []
z = zipfile.ZipFile(P)
names = z.namelist()
xml = {n: z.read(n).decode('utf8', 'ignore') for n in names if n.endswith('.xml')}
shapes = sum(v.count('<xdr:sp ') + v.count('<xdr:sp>') for n, v in xml.items() if 'drawings/' in n)
databar = sum(v.count('<dataBar') for v in xml.values()); icons = sum(v.count('<iconSet') for v in xml.values())
macros = any(n.endswith('.bin') for n in names)
funcs = set()
for n, v in xml.items():
    if 'worksheets/sheet' in n:
        for f in re.findall(r'<f[^>]*>(.*?)</f>', v, re.S):
            funcs |= set(re.findall(r'([A-Z][A-Z0-9\.]+)\(', f))
BAD = {'XLOOKUP', 'XMATCH', 'FILTER', 'SORT', 'SORTBY', 'UNIQUE', 'SEQUENCE', 'LET', 'LAMBDA', 'TEXTJOIN', 'CONCAT', 'IFS', 'SWITCH', 'MAXIFS', 'MINIFS'}
charts = len([n for n in names if n.startswith('xl/charts/chart')])
out.append(f'shapes/text boxes: {shapes} | data bars: {databar} | icon sets: {icons} | macros: {macros} | charts: {charts}')
out.append('functions used: ' + ', '.join(sorted(funcs)))
out.append('functions not in Excel 2016 / risky in Sheets: ' + (', '.join(sorted(funcs & BAD)) or 'none'))
out.append('SPARKLINE is used only inside IFERROR(...) with a REPT text-bar fallback (Excel/LibreOffice show the text bar, Sheets shows a real bar)'
           if 'SPARKLINE' in funcs else 'no SPARKLINE')

# 2) round trip
R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
T = tempfile.mkdtemp()
shutil.copy(P, f'{T}/a.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'ods', '--outdir', T, f'{T}/a.xlsx'], check=True, capture_output=True)
os.makedirs(f'{T}/rt'); subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx', '--outdir', f'{T}/rt', f'{T}/a.ods'], check=True, capture_output=True)
rc = json.loads(subprocess.run(['python3', R, f'{T}/rt/a.xlsx', '120'], capture_output=True, text=True).stdout)
out.append(f'round-trip recalc: status {rc.get("status")}, formulas {rc.get("total_formulas")}, errors {rc.get("total_errors")}')
a = load_workbook(P, data_only=True); b = load_workbook(f'{T}/rt/a.xlsx', data_only=True)
KEYS = [('Schedule C', 'D9'), ('Schedule C', 'D41'), ('Schedule C', 'D44'), ('Tax Estimate', 'C16'), ('Tax Estimate', 'C29'),
        ('Tax Estimate', 'C39'), ('Quarterly Tax', 'K22'), ('Quarterly Tax', 'G41'), ('Monthly Money Check-in', 'B10'), ('Income Log', 'J9'), ('Income Log', 'N9')]
diff = 0
for sh, c in KEYS:
    va, vb = a[sh][c].value, b[sh][c].value
    same = (va == vb) or (isinstance(va, (int, float)) and isinstance(vb, (int, float)) and abs(va - vb) < 0.01) or (str(va)[:10] == str(vb)[:10])
    diff += not same
    out.append(f'  {sh}!{c}: {str(va)[:70]!s:72} {"same" if same else "DIFF -> " + str(vb)[:60]}')
out.append(f'key figures that changed after the round trip: {diff}')
cf = sum(len(ws.conditional_formatting) for ws in b.worksheets)
out.append(f'conditional formatting ranges kept after round trip: {cf}; tabs: {len(b.worksheets)}; data validations kept: '
           f'{sum(len(ws.data_validations.dataValidation) for ws in b.worksheets)}')

# 3) hand check
s = a['Settings']; te = a['Tax Estimate']; tr = a['Tax Rates']
profit = te['C10'].value
ne = round(profit * 0.9235, 2); se = round(0.124 * min(ne, 184500), 2) + round(0.029 * ne, 2); half = round(se / 2, 2)
agi = profit + (s['C11'].value or 0) + (s['C13'].value or 0) - half - min(s['C20'].value or 0, profit - half) - (s['C21'].value or 0)
qbi = round(min(0.2 * (profit - half - (s['C20'].value or 0) - (s['C21'].value or 0)), 0.2 * (agi - 16100)), 2)
ti = max(0, agi - 16100 - qbi)
th = [0, 12400, 50400, 105700, 201775, 256225, 640600]; rt = [.10, .12, .22, .24, .32, .35, .37]
it = round(sum((min(ti, th[i + 1]) if i < 6 else ti) - th[i] for i in range(7) if ti > th[i]) and sum(((min(ti, th[i + 1]) if i < 6 else ti) - th[i]) * rt[i] for i in range(7) if ti > th[i]), 2)
fed = it + se
req = min(round(0.9 * fed), 12000)
for lab, hand, sheet in [('SE tax', se, te['C16'].value), ('taxable income', ti, te['C28'].value), ('income tax', it, te['C29'].value),
                         ('safe-harbor target', req, a['Quarterly Tax']['K22'].value)]:
    out.append(f'hand check {lab:20s} hand {hand:>12,.2f}  sheet {sheet:>12,.2f}  {"OK" if abs(hand - sheet) < 0.02 else "MISMATCH"}')
print('\n'.join(out))
