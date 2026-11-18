"""Google Sheets readiness check (gate 8 stand-in): no shapes / text boxes / data bars / icon sets / macros / internal links,
list every function used, and a LibreOffice xlsx round-trip recalculated with 0 errors."""
import zipfile, re, sys, glob, subprocess, os, tempfile, shutil
for f in sys.argv[1:]:
    z = zipfile.ZipFile(f); names = z.namelist()
    draw = [n for n in names if n.startswith('xl/drawings/drawing')]
    shapes = sum(len(re.findall(r'<xdr:sp>|<xdr:sp ', z.read(n).decode())) for n in draw)
    charts = len([n for n in names if n.startswith('xl/charts/chart')])
    xml = ''.join(z.read(n).decode('utf-8', 'ignore') for n in names if n.startswith('xl/worksheets/sheet'))
    fns = sorted(set(re.findall(r'([A-Z][A-Z0-9\.]+)\(', ' '.join(re.findall(r'<f>(.*?)</f>', xml)))))
    print(os.path.basename(f))
    print('  charts', charts, '| shapes/text boxes', shapes, '| dataBar', xml.count('dataBar'), '| iconSet', xml.count('iconSet'),
          '| macros', any(n.endswith('.bin') for n in names), '| internal hyperlinks', xml.count('location='))
    print('  functions:', ', '.join(fns))
    t = tempfile.mkdtemp(); shutil.copy(f, t + '/a.xlsx')
    subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', t + '/rt', t + '/a.xlsx'], capture_output=True)
    R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
    out = subprocess.run(['python3', R, t + '/rt/a.xlsx', '90'], capture_output=True, text=True).stdout
    print('  LibreOffice round-trip recalc:', re.search(r'"total_errors": \d+', out).group(0), re.search(r'"total_formulas": \d+', out).group(0))
