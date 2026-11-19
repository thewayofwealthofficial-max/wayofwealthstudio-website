"""Every SPARKLINE cell must be exactly =IFERROR(SPARKLINE(...),fallback): nothing joined before or after, no & inside the
SPARKLINE call (Google Sheets returns #VALUE! when a SPARKLINE is concatenated with text)."""
import openpyxl, sys
def close(s, i):
    d = 0; q = False
    for j in range(i, len(s)):
        ch = s[j]
        if ch == '"': q = not q
        elif not q and ch == '(': d += 1
        elif not q and ch == ')':
            d -= 1
            if d == 0: return j
for f in sys.argv[1:]:
    wb = openpyxl.load_workbook(f); n = bad = 0
    for ws in wb:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if not (isinstance(v, str) and 'SPARKLINE' in v): continue
                n += 1; ok = v.startswith('=IFERROR(SPARKLINE(') and v.count('SPARKLINE') == 1
                if ok:
                    ok &= close(v, len('=IFERROR')) == len(v) - 1          # IFERROR wraps the whole cell
                    sp = v[len('=IFERROR('):close(v, len('=IFERROR(SPARKLINE')) + 1]
                    ok &= '&' not in sp                                      # nothing joined inside the sparkline
                if not ok: bad += 1; print('BAD', ws.title, c.coordinate, v[:90])
    print(f.split('/')[-1], 'sparkline cells', n, 'not whole-cell', bad)
