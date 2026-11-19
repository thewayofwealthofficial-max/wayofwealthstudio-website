"""10 listing photos for the US Self-Employed Tax Deduction and Quarterly Tax Tracker (2000x2000 JPG q90).
Slot order = the HeyMorning 'Tax Deduction Tracker' winning recipe (hero, included, deductions, mileage, quarterly, dashboard,
Schedule C, accountant, Excel+Sheets/check-in, 3 steps + 5 reasons). Scenes: etsy/lib/scenes (reused, 0 new AI images).
Screens: real 300-dpi LibreOffice renders of the EXAMPLE file. Every figure typeset in a photo is read from the recalculated file.
Run: python3 photos.py [n ...]"""
import os, sys
from PIL import Image, ImageDraw
from openpyxl import load_workbook
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa

P = os.path.join(KIT, 'photos'); os.makedirs(P, exist_ok=True)
render_pages(EXAMPLE, 'ex'); render_pages(BLANKF, 'bl')
EX = lambda n: page('ex', n)
import re, subprocess


def tabpages(name):
    """first PDF page of each tab, read from the 'TAB n OF 12' strip (so the photo crops never drift when a tab gains a page)"""
    pdf = os.path.join(WORK, name, name + '.pdf'); out = {}
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
    for p_ in range(1, n + 1):
        t = subprocess.run(['pdftotext', '-f', str(p_), '-l', str(p_), '-layout', pdf, '-'], capture_output=True, text=True).stdout
        m = re.search(r'TAB (\d+) OF 12', t)
        if m and int(m.group(1)) not in out: out[int(m.group(1))] = p_
    return out


TP = tabpages('ex')
DASH, START, SETT, INC, DED, MIL, SCH, TAXE, QTR, ACC, CHK, RATES = [TP[i] for i in range(1, 13)]
V = load_workbook(EXAMPLE, data_only=True)
q = V['Quarterly Tax']
QV = [(q[f'E{r}'].value, q[f'K{r}'].value or q[f'G{r}'].value, q[f'O{r}'].value, q[f'G{r}'].value, bool(q[f'K{r}'].value)) for r in range(38, 42)]
money = lambda v: f'${v:,.0f}'
INKS = (92, 78, 62)


def dash(box): return crop150(EX(DASH), box)


def phone_dash(aspect=0.465):
    """one narrow column of real Dashboard cards for a phone screen: hero card, then 4 KPI cards at the same width"""
    top = dash((47, 136, 376, 289)); W = top.width
    small = [dash(b_) for b_ in [(422, 135, 564, 210), (610, 135, 752, 210), (422, 217, 564, 289), (610, 217, 752, 289)]]
    small = [x.resize((W, round(x.height * W / x.width)), Image.LANCZOS) for x in small]
    c = stack([Image.new('RGB', (W, 14), SHEETBG), top] + small, gap=22)
    c = hcat([Image.new('RGB', (10, c.height), SHEETBG), c, Image.new('RGB', (10, c.height), SHEETBG)])
    return pad(c, aspect)


def clean_edge(im, x0=1940):
    """the zoomed laptop_large scene leaves slivers of the saucer and a sparkle at the right edge: continue the backdrop
    (each row's colour at x0) to the frame edge, so no half-cut prop shows"""
    import numpy as np
    a = np.array(im); a[:, x0:] = a[:, x0:x0 + 1]; return Image.fromarray(a)


def clear_box(im, x0, y0, y1, horizon, mode='row'):
    """remove a prop cut by the right frame edge: rows y0..y1, columns x0..edge get plain backdrop.
    mode 'row': each row takes its colour at x0-2 (a clean gap). mode 'col': wall rows take the colour above the box,
    floor rows the colour below it (keeps the wall/floor line at `horizon`)."""
    import numpy as np
    a = np.array(im).astype(float)
    if mode == 'row':
        a[y0:y1, x0:] = a[y0:y1, x0 - 2:x0 - 1]
    else:
        a[y0:horizon, x0:] = a[y0 - 6:y0 - 5, x0:]
        a[horizon:y1, x0:] = a[y1 + 6:y1 + 7, x0:]
    out = Image.fromarray(a.clip(0, 255).astype('uint8'))
    soft = out.crop((x0 - 4, y0 - 4, im.width, y1 + 4)).filter(ImageFilter.GaussianBlur(2))
    out.paste(soft, (x0 - 4, y0 - 4)); return out


def rowlines(pg, x=300):
    """y of the input-cell grid lines (300-dpi page) in the Deductions log, measured in column B"""
    import numpy as np
    a = np.array(pg).astype(int)[:, x]
    ys = [y for y in range(len(a)) if abs(a[y][0] - 230) < 12 and abs(a[y][1] - 217) < 12 and abs(a[y][2] - 181) < 14]
    g = []
    for y in ys:
        if not g or y - g[-1][-1] > 2: g.append([y])
        else: g[-1].append(y)
    return [round(sum(v) / len(v)) for v in g]


def badges(im, items, cy, r=150, gap=40):
    d = ImageDraw.Draw(im)
    n = len(items); total = n * 2 * r + (n - 1) * gap; x = S / 2 - total / 2 + r
    for lines in items:
        sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).ellipse((x - r, cy - r + 12, x + r, cy + r + 12), fill=80)
        im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
        d = ImageDraw.Draw(im)
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=(255, 251, 246), outline=GOLD, width=7)
        d.ellipse((x - r + 16, cy - r + 16, x + r - 16, cy + r - 16), outline=(226, 205, 170), width=2)
        f0, f1 = pf(58), inter(30, 'SemiBold')
        y = cy - 52
        center(d, y, lines[0], f0, INK, x); y += 74
        for ln in lines[1:]:
            center(d, y, ln, f1, GOLD_D, x); y += 36
        x += 2 * r + gap


def p01():
    im = clean_edge(scene('laptop_large').crop((110, 400, 1750, 2040)).resize((S, S), Image.LANCZOS))   # zoom 1.25, cup cropped out: the dashboard fills the frame
    shot = dash((40, 40, 762, 488))
    TRANS.clear(); im, _ = comp(im, [(shot, 'tab')])
    ph = scene('phone_large')
    ph, _ = comp(ph, [(phone_dash(0.465), 'phone')])
    phone = cut_device(ph, (720, 590, 1330, 1860))
    phone = phone.resize((int(phone.width * .42), int(phone.height * .42)), Image.LANCZOS)
    paste_shadow(im, phone, (S - phone.width - 34, 1560 - phone.height))       # beside the screen
    y = title(im, 'Self-Employed Tax Tracker', 'Deductions \u00b7 Quarterly tax \u00b7 Mileage', y=30, hs=124, ss=70, gap=10)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y - 6, 'FOR US FREELANCERS \u00b7 1099 \u00b7 SOLE PROPRIETORS', inter(32, 'SemiBold'), GOLD_D, 5)
    badges(im, [('2026', '+ 2027 IRS', 'due dates'), ('Sch. C', 'every line', 'mapped'), ('Auto', 'calculates', 'your tax'),
                ('Excel', '+ Google', 'Sheets')], 1790, r=132, gap=46)
    footer(im)
    return im


def p02():
    im = background()
    y = title(im, 'What’s Included', '12 tabs, one job each', y=50, hs=112, ss=58)
    rows = [('Dashboard', '8 cards, 5 charts, next 3 steps'), ('Start Here', '5 written steps for beginners'),
            ('Settings', 'One tax-year dropdown'), ('Income Log', 'Paste your invoices: it sorts itself'),
            ('Deductions', 'Schedule C line filled in'), ('Mileage', 'IRS rate picked by date'),
            ('Schedule C', 'Every line, totaled'), ('Tax Estimate', 'SE tax + federal income tax'),
            ('Quarterly Tax', '1040-ES dates + safe harbor'), ('Accountant', 'Ready-for-tax-time checklist'),
            ('Check-in', 'Your month in plain words'), ('Tax Rates', '2026 + 2027, with sources')]
    top = y + 10; h = 112; g = 16; cw = 880; xs_ = [(S - 2 * cw - 40) // 2, (S - 2 * cw - 40) // 2 + cw + 40]
    for i, (a_, b_) in enumerate(rows):
        x0 = xs_[i // 6]; y0 = top + (i % 6) * (h + g)
        pill(im, (x0, y0, x0 + cw, y0 + h), None, None, r=30)
        number_disc(im, x0 + 62, y0 + h / 2, i + 1, r=34)
        d = ImageDraw.Draw(im)
        d.text((x0 + 118, y0 + 14), a_, font=pf(42), fill=INK)
        d.text((x0 + 118, y0 + 64), b_, font=pfi(32), fill=INKS)
    z = crop150(EX(START), (60, 330, 1146, 742))     # zoom: the real Start Here steps 1-4
    w = 1800; hh = round(z.height * w / z.width); x0 = (S - w) // 2; y0 = top + 6 * (h + g) + 70
    shot_card(im, z, (x0, y0, x0 + w, y0 + hh))
    gold_label(im, S / 2, y0 - 46, 'Start Here tab: written steps, plus a filled example file', f=inter(34, 'Bold'), h=62)
    footer(im)
    return im


def p03():
    im = clean_edge(scene('laptop_large').crop((110, 400, 1750, 2040)).resize((S, S), Image.LANCZOS))   # cup cropped out
    pg = EX(DED)
    cols = [(54, 163), (572, 667), (667, 1028), (1028, 1106), (1214, 1300), (1300, 1378), (1378, 1490)]
    Y0 = 195; RY_ = rowlines(pg); Y1 = max(v for v in RY_ if v <= 1580) / 2     # end exactly on a row line: no half rows
    shot = hcat([crop150(pg, (a, Y0, b, Y1)) for a, b in cols])
    TRANS.clear(); im, (bx,) = comp(im, [(shot, 'tab')])
    tx0, ty0, sc, pl, pt = TRANS[0]
    xs = []; acc = 0
    for a, b in cols: xs.append(acc); acc += b - a
    P_ = lambda ci, xo, y: (tx0 + ((xs[ci] + xo) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    title(im, 'Log Your Deductions', 'Pick a category. The Schedule C line fills in.', y=40, hs=112, ss=60)
    gold_label(im, 330, 300, 'Schedule C category')
    gold_label(im, 1024, 300, 'Business % for shared costs')
    gold_label(im, 1730, 300, 'Line number + \u2713 check')
    x, _ = P_(2, 150, 0); ty = ty0 - 14
    leader(im, [(330, 374), (330, 405), (x, 405), (x, ty)])
    x2, _ = P_(3, 39, 0); ty2 = ty0 - 14
    leader(im, [(1024, 374), (1024, 420), (x2, 420), (x2, ty2)])
    x3, _ = P_(5, 39, 0); ty3 = ty0 - 14
    leader(im, [(1730, 374), (1730, 410), (x3, 410), (x3, ty3)])
    # zoom cards: real cells from the same page, enlarged
    RY = rowlines(pg)
    rows = (RY[4], RY[7])
    zooms = [((667, 1028), 'Schedule C category'), ((1214, 1378), 'Deductible + line'), ((1378, 1490), 'Counted')]
    parts = []
    for (a, b), lab in zooms:
        z = stack([pg.crop((2 * a, RY[0] - 62, 2 * b, RY[0])), pg.crop((2 * a, rows[0], 2 * b, rows[1]))])
        k = 230 / z.height; parts.append((z.resize((round(z.width * k), 230), Image.LANCZOS), lab))
    tot = sum(z.width for z, _ in parts) + 50 * 2; x = (S - tot) // 2; y0 = 1575
    for z, lab in parts:
        shot_card(im, z, (x, y0, x + z.width, y0 + z.height))
        gold_label(im, x + z.width / 2, y0 - 50, lab, f=inter(34, 'Bold'), h=62)
        x += z.width + 50
    footer(im)
    return im


def p04():
    im = scene('tablet_phone_flowers')
    pg = EX(MIL)
    cols = [(53, 158), (429, 639), (639, 722), (722, 805), (805, 905)]
    tbl = hcat([crop150(pg, (a, 193, b, 720)) for a, b in cols])
    rate = crop150(pg, (1090, 193, 1540, 252)); rate = rate.resize((tbl.width, round(rate.height * tbl.width / rate.width)), Image.LANCZOS)
    p4 = crop150(pg, (1090, 315, 1540, 495)); p4 = p4.resize((tbl.width, round(p4.height * tbl.width / p4.width)), Image.LANCZOS)
    tabshot = stack([crop150(pg, (53, 166, 53 + tbl.width // 2, 190)), tbl, Image.new('RGB', (tbl.width, 20), SHEETBG), rate,
                     Image.new('RGB', (tbl.width, 20), SHEETBG), p4])
    nar = [(53, 158), (722, 805), (805, 905)]
    ptbl = hcat([crop150(pg, (a, 193, b, 720)) for a, b in nar])
    prate = hcat([crop150(pg, (1090, 193, 1312, 252)), crop150(pg, (1462, 193, 1540, 252))])   # rate box: label + per-mile columns
    prate = hcat([prate, Image.new('RGB', (max(0, ptbl.width - prate.width), prate.height), SHEETBG)]) if prate.width < ptbl.width else prate.resize((ptbl.width, round(prate.height * ptbl.width / prate.width)), Image.LANCZOS)
    ph = stack([Image.new('RGB', (ptbl.width, 12), SHEETBG), prate, Image.new('RGB', (ptbl.width, 16), SHEETBG), ptbl])
    im, _ = comp(im, [(pad(tabshot, 819 / 1088), 'tab'), (pad(ph, 0.465), 'phone')])
    y = title(im, 'Track Your Mileage', 'At the IRS standard mileage rate', y=60, hs=116, ss=62)
    d = ImageDraw.Draw(im)
    labels = ['72.5\u00a2 Jan\u2013Jun 2026', '76\u00a2 from Jul 1, 2026', 'Schedule C Part IV answers']
    f = inter(36, 'SemiBold'); ws = [tw(d, t, f) + 70 for t in labels]; x = S / 2 - (sum(ws) + 2 * 24) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, y + 20, x + w, y + 92), t, f); x += w + 24
    d = ImageDraw.Draw(im)
    card(im, (170, 1808, 1878, 1898), r=45, shadow=40)
    d = ImageDraw.Draw(im)
    center(d, 1822, 'Rate picked by trip date. Update it in one cell when the IRS changes it.', pfi(44), GOLD_D)
    footer(im)
    return im


def p05():
    im = background()
    y = title(im, 'Quarterly Estimated Tax', 'Four 1040-ES due dates, worked out for you', y=70, hs=112)
    cols = [(GOLD_D, 'Q1'), (GOLD_D, 'Q2'), (GOLD_D, 'Q3'), (GOLD_D, 'Q4')]
    cw, g, x0, top = 420, 36, 0, y + 40
    x0 = (S - (4 * cw + 3 * g)) / 2
    for i, ((due, amt, st, plan, paid), (col, qn)) in enumerate(zip(QV, cols)):
        x = x0 + i * (cw + g)
        card(im, (x, top, x + cw, top + 430), r=34)
        d = ImageDraw.Draw(im)
        gold_label(im, x + cw / 2, top + 36, f'{qn} · {due.strftime("%b")} {due.day}', f=inter(40, 'Bold'))
        center(d, top + 140, str(due.year), inter(34, 'Medium'), INKS, x + cw / 2)
        center(d, top + 195, money(amt), pf(96), INK, x + cw / 2)
        stt = 'Paid' if paid else st
        if paid: tick(im, x + cw / 2 - tw(d, stt, inter(36, 'SemiBold')) / 2 - 36, top + 340, 24)
        d = ImageDraw.Draw(im)
        center(d, 318 + top, stt, inter(36, 'SemiBold'), (110, 140, 100) if paid else (196, 96, 80), x + cw / 2 + (14 if paid else 0))
        center(d, 370 + top, f'planned {money(plan)}' if paid else 'to pay', inter(30, 'Medium'), INKS, x + cw / 2)
    qp = EX(QTR)
    pay = crop150(qp, (50, 652, 1036, 826))
    pw = 1840; ph_ = round(pay.height * pw / pay.width); t1 = top + 470
    shot_card(im, pay, ((S - pw) // 2, t1, (S - pw) // 2 + pw, t1 + ph_))
    tbl = crop150(qp, (50, 290, 790, 598))
    w = 1180; h = int(w * tbl.height / tbl.width)
    t2 = t1 + ph_ + 40
    shot_card(im, tbl, (100, t2, 100 + w, t2 + h))
    card(im, (1320, t2, 1948, t2 + h), r=34)
    d = ImageDraw.Draw(im)
    d.text((1370, t2 + 50), 'Safe harbor', font=pf(64), fill=INK)
    yy = t2 + 135
    for ln in ['Pay the smaller of 90% of', 'this year’s tax or 100% of', 'last year’s (110% if AGI', 'was over $150,000).', '',
               'Pay a quarter late or short?', 'The next one catches you up.']:
        d.text((1370, yy), ln, font=inter(34, 'Medium'), fill=INK); yy += 46
    center(d, t2 + h + 40, 'Jordan’s example: safe-harbor target $12,000. Estimate, not tax advice.', pfi(46), GOLD_D)
    footer(im)
    return im


def p06():
    im = clean_edge(scene('laptop_large').crop((110, 400, 1750, 2040)).resize((S, S), Image.LANCZOS))   # zoom 1.25, cup cropped out
    X0, Y0 = 40, 490
    shot = crop150(EX(DASH), (X0, Y0, 772, 960))
    cw = round(shot.width / 0.86); sh = Image.new('RGB', (cw, round(cw / 1.55)), SHEETBG); sh.paste(shot, (0, 0))
    TRANS.clear(); im, _ = comp(im, [(sh, 'tab')])          # charts fill the left 86%: the phone covers no chart
    tx0, ty0, sc, pl, pt = TRANS[0]
    P_ = lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    ph = scene('phone_large')
    ph, _ = comp(ph, [(phone_dash(0.465), 'phone')])
    phone = cut_device(ph, (720, 590, 1330, 1860))
    phone = phone.resize((int(phone.width * .55), int(phone.height * .55)), Image.LANCZOS)
    PX, PY = S - phone.width - 30, 1600 - phone.height
    paste_shadow(im, phone, (PX, PY))
    title(im, 'Annual Dashboard', 'Your whole tax year at a glance', y=50, hs=112, ss=60)
    gold_label(im, 520, 318, 'Charts that update as you type')
    gold_label(im, 1560, 318, 'Next payment + 8 live cards')
    a, b = P_(215, 495); leader(im, [(520, 392), (520, 420), (a, 420), (a, b)])
    cxp = PX + phone.width / 2
    leader(im, [(1560, 392), (1560, 420), (cxp, 420), (cxp, PY + 40)])
    d = ImageDraw.Draw(im)
    center(d, 1770, 'Income, deductions, profit, SE tax, income tax, paid so far', pfi(52), GOLD_D)
    footer(im)
    return im


def p07():
    im = background(sparkles=False)
    for (x, y, r) in [(92, 300, 42), (140, 395, 18), (92, 1760, 34), (150, 1840, 16), (1958, 1700, 36), (1900, 1790, 16)]:
        sparkle(im, x, y, r)
    title(im, 'Schedule C Summary', 'Every total on its official line number', y=60, hs=112, ss=60)
    render_pages(EXAMPLE, 'ex6', dpi=600)
    t = page('ex6', SCH)
    Y0, Y1, X0, X1 = 393, 1125, 50, 662
    shot = t.crop((4 * X0, 4 * Y0, 4 * X1, 4 * Y1))
    T_, Hh = 300, 1390
    sc = Hh / (Y1 - Y0); W_ = round((X1 - X0) * sc); L_ = 250
    shot_card(im, shot, (L_, T_, L_ + W_, T_ + Hh))
    yy = lambda y: T_ + (y - Y0) * sc
    d = ImageDraw.Draw(im)
    marks = [(440, 465, 'Line 9', 'mileage + parking'), (1068, 1095, 'Line 30', 'home office'), (1100, 1124, 'Line 31', 'net profit \u2192 SE tax')]
    for a_, b_, lab, sub in marks:
        b0, b1 = yy(a_), yy(b_)
        ImageDraw.Draw(im).rounded_rectangle((L_ + 4, b0, L_ + W_ - 4, b1), 10, outline=(176, 128, 60), width=6)
        cy = (b0 + b1) / 2
        box = gold_label(im, 1745, cy - 40 if lab != 'Line 30' else cy - 110, lab, f=inter(42, 'Bold'), h=78)
        leader(im, [(box[0] - 4, (box[1] + box[3]) / 2), (L_ + W_ + 40, (box[1] + box[3]) / 2), (L_ + W_ + 40, cy), (L_ + W_ + 2, cy)])
        d = ImageDraw.Draw(im)
        center(d, box[3] + 10, sub, inter(32, 'Medium'), INK, 1745)
    center(d, T_ + Hh + 60, 'Lines 1\u201331 from the current Schedule C (Form 1040). Hand it to your tax pro.', pfi(46), GOLD_D)
    footer(im)
    return im


def p08():
    im = scene('tablet_phone_flowers')
    shot = stack([crop150(EX(ACC), (55, 60, 762, 100)), crop150(EX(ACC), (55, 215, 762, 945))])
    cards = [crop150(EX(QTR), (x, 152, x + 188, 263)) for x in (49, 295, 542, 788)]
    ph = stack([Image.new('RGB', (cards[0].width, 20), SHEETBG)] + cards + [Image.new('RGB', (cards[0].width, 190), SHEETBG)], gap=16)
    im, _ = comp(im, [(pad(shot, 819 / 1088), 'tab'), (pad(ph, 0.465), 'phone')])
    title(im, 'Ready for Your Accountant', 'Tax time without the shoebox', y=60, hs=112)
    d = ImageDraw.Draw(im)
    labels = ['16-point checklist', 'Progress bar', 'Questions for your pro', 'Payments on your phone']
    f = inter(36, 'SemiBold'); ws = [tw(d, t, f) + 70 for t in labels]
    x = S / 2 - (sum(ws) + 3 * 20) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, 340, x + w, 410), t, f); x += w + 20
    pg = EX(ACC)
    bar = hcat([pg.crop((110, 1822, 560, 1872)), pg.crop((1250, 1822, 1660, 1872))])
    bar = hcat([bar, Image.new('RGB', (1414 - bar.width, bar.height), (238, 242, 234))])
    z = stack([pg.crop((110, 966, 1524, 1288)), Image.new('RGB', (1414, 26), SHEETBG), bar])
    w = 1500; h = round(z.height * w / z.width); x0 = (S - w) // 2; y0 = 1525
    shot_card(im, z, (x0, y0, x0 + w, y0 + h))
    gold_label(im, 560, y0 - 52, 'Zoom: real rows from the checklist', f=inter(34, 'Bold'), h=62)
    footer(im)
    return im


def p09():
    im = scene_nokeys().crop((145, 400, 1785, 2040)).resize((S, S), Image.LANCZOS)   # zoom 1.25, plant cropped out
    im = clear_box(im, 1925, 420, 640, 500)        # sparkle cut by the right edge
    pg = EX(CHK)
    lap = stack([crop150(pg, (48, 200, 990, 420)), crop150(pg, (48, 440, 990, 765))])
    im, _ = comp(im, [(lap, 'tab'), (phone_dash(), 'phone')])
    y = title(im, 'Monthly Check-in', 'See your month in plain words', y=24, hs=116, ss=60, gap=6)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y + 4, 'PLUS 5 QUESTIONS FOR FREELANCERS', inter(32, 'SemiBold'), GOLD_D, 5)
    card(im, (120, 1640, 1928, 1780), r=60)
    d = ImageDraw.Draw(im)
    center(d, 1660, 'Works in Excel and Google Sheets', pf(84), INK)
    f = inter(34, 'SemiBold'); labels = ['Excel 2016-compatible formulas', 'Google Sheets', 'No macros']
    ws = [tw(d, t, f) + 64 for t in labels]; gap = 24; x = S / 2 - (sum(ws) + gap * (len(ws) - 1)) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, 1820, x + w, 1884), t, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), bw=1); x += w + gap
    footer(im, y=1950)
    return im


def p10():
    im = background()
    y = title(im, 'How It Works', None, y=50, hs=104)
    d = ImageDraw.Draw(im)
    steps = [('PICK THE YEAR', 'One dropdown: 2026 or 2027'), ('LOG OR PASTE', 'Income, costs, miles'), ('PAY ON TIME', 'Four 1040-ES dates')]
    cxs = [370, 1024, 1678]
    for i, (h, t) in enumerate(steps):
        number_disc(im, cxs[i], 230, i + 1, r=44)
        d = ImageDraw.Draw(im)
        center(d, 292, h, inter(38, 'Bold'), INK, cxs[i]); center(d, 342, t, inter(32, 'Medium'), INKS, cxs[i])
        if i < 2:
            a0, a1 = cxs[i] + 80, cxs[i + 1] - 80
            d.line([(a0, 230), (a1, 230)], fill=GOLD_D, width=4); d.polygon([(a1, 230), (a1 - 20, 219), (a1 - 20, 241)], fill=GOLD_D)
    center(d, 430, '5 Reasons to Buy From Us', pf(92), INK)
    rows = [('Written Start Here tab + a filled example', 'Never lost setting up: 5 plain steps, then copy Jordan’s year'),
            ('Works in Excel and Google Sheets', 'Excel 2016-compatible formulas, no macros, no 365-only functions'),
            ('Paste a CSV of your invoices', 'Any order, any date style: the list sorts itself'),
            ('One tax-year dropdown', 'Dates, rates and brackets all switch together'),
            ('Made by a qualified financial planner', 'Says plainly what it is: an estimate, not tax advice')]
    top = 560; h = 220; g = 32
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (150, y0, 1898, y0 + h), None, None, r=46)
        tick(im, 255, y0 + h / 2, 42)
        d = ImageDraw.Draw(im)
        d.text((340, y0 + 46), a, font=pf(56), fill=INK)
        d.text((340, y0 + 128), b, font=pfi(44), fill=(140, 104, 58))
    footer(im, y=1950)
    return im


if __name__ == '__main__':
    which = [int(a) for a in sys.argv[1:]] or range(1, 11)
    for n in which:
        FRINGE.clear()
        save(globals()[f'p{n:02d}'](), os.path.join(P, f'{n:02d}.jpg'))
        print('   screen-edge green-dominant pixels after defringe:', FRINGE or 'no screens')
