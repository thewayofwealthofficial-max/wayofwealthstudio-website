"""Google Sheets proxy check (no Drive access here): scan the xlsx XML for things Sheets drops, list every function used,
then LibreOffice round-trip (xlsx -> ods -> xlsx), recalc and compare key values with the original."""
import sys, zipfile, re, subprocess, os, glob, shutil, openpyxl
P = sys.argv[1]; W = sys.argv[2]; os.makedirs(W, exist_ok=True)
z = zipfile.ZipFile(P); names = z.namelist()
xml = {n: z.read(n).decode('utf8', 'ignore') for n in names if n.endswith('.xml')}
draw = [n for n in names if 'drawings/drawing' in n and n.endswith('.xml')]
shapes = sum(len(re.findall(r'<xdr:sp>|<xdr:sp ', xml[n])) for n in draw)
pics = sum(xml[n].count('<xdr:pic') for n in draw)
charts = len([n for n in names if n.startswith('xl/charts/chart')])
bars = sum(x.count('<dataBar') for x in xml.values()); icons = sum(x.count('<iconSet') for x in xml.values())
macros = [n for n in names if 'vba' in n.lower()]
links = sum(x.count('<hyperlink ') for x in xml.values())
funcs = set()
for n, x in xml.items():
    if n.startswith('xl/worksheets/sheet'):
        for f in re.findall(r'<f>(.*?)</f>', x): funcs |= set(re.findall(r'([A-Z][A-Z0-9\.]+)\(', f))
print('shapes', shapes, '| pictures', pics, '| charts', charts, '| data bars', bars, '| icon sets', icons, '| macros', len(macros), '| hyperlinks', links)
print('functions used:', ', '.join(sorted(funcs)))
SHEETS_OK = {'AND', 'AVERAGEIF', 'COUNT', 'COUNTA', 'COUNTIF', 'COUNTIFS', 'DATE', 'EDATE', 'EOMONTH', 'IF', 'IFERROR', 'INDEX', 'LARGE', 'LEFT',
             'MATCH', 'MAX', 'MIN', 'MONTH', 'N', 'OR', 'REPT', 'ROUND', 'ROUNDUP', 'ROW', 'SMALL', 'SPARKLINE', 'SUBSTITUTE', 'SUM', 'SUMIFS',
             'SUMPRODUCT', 'TEXT', 'UPPER', 'YEAR'}
print('functions not on the Sheets-safe list:', sorted(funcs - SHEETS_OK) or 'none')
shutil.copy(P, f'{W}/orig.xlsx')
subprocess.run(['soffice', '--headless', '--convert-to', 'ods', '--outdir', W, f'{W}/orig.xlsx'], check=True, capture_output=True)
os.makedirs(f'{W}/rt', exist_ok=True)
subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx', '--outdir', f'{W}/rt', f'{W}/orig.ods'], check=True, capture_output=True)
R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
print('round-trip recalc:', subprocess.run(['python3', R, f'{W}/rt/orig.xlsx', '180'], capture_output=True, text=True).stdout.replace('\n', ' '))
a = openpyxl.load_workbook(P, data_only=True); b = openpyxl.load_workbook(f'{W}/rt/orig.xlsx', data_only=True)
keys = [('Monthly Summary', 'F21'), ('Monthly Summary', 'G21'), ('Monthly Summary', 'H21'), ('Dashboard', 'B8'), ('Dashboard', 'J8'),
        ('Dashboard', 'B16'), ('Dashboard', 'J22'), ('Pricing Check', 'I14'), ('Tax Set-Aside', 'G20'), ('Monthly Money Check-in', 'B11')]
same = 0
for s, c in keys:
    va, vb = a[s][c].value, b[s][c].value
    eq = va == vb or (isinstance(va, float) and isinstance(vb, (int, float)) and abs(va - vb) < 0.01); same += eq
    print(f'  {s}!{c}: {"same" if eq else "DIFF"}  {str(va)[:60]}')
print(f'{same}/{len(keys)} key cells identical after round-trip; charts after round-trip:',
      len([n for n in zipfile.ZipFile(f"{W}/rt/orig.xlsx").namelist() if n.startswith("xl/charts/chart")]))
