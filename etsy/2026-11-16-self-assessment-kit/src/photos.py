"""10 listing photos for the UK Self Assessment 2025/26 Deadline Kit (2000x2000 JPG q90).
Scenes: etsy/lib/scenes (reused, no AI calls). Screens: real 300-dpi LibreOffice renders of the EXAMPLE / BLANK files.
Run: SA_WORK=/some/tmp python3 photos.py [n ...]"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa

P = os.path.join(KIT, 'photos'); os.makedirs(P, exist_ok=True)
render_pages(EXAMPLE, 'ex'); render_pages(BLANKF, 'bl')
render_noapr(EXAMPLE, 'noapr')   # dashboard shots: example without the out-of-year April 2026 row (no ✕ warning line)
EX = lambda n: page('ex', n)
DASH, START, INC, SA103, TAXEST, TAXPOT, DEAD = 1, 2, 4, 13, 14, 15, 16

# ---- real crops (boxes in 150-dpi page coords)
dash_top = crop150(page('noapr', 1), (40, 40, 760, 500))
hero = crop150(page('noapr', 1), (47, 136, 376, 289))
kpi = lambda b: crop150(page('noapr', 1), b)
k_days, k_profit = kpi((423, 136, 563, 209)), kpi((610, 136, 751, 209))
k_it, k_c4 = kpi((423, 217, 563, 289)), kpi((610, 217, 751, 289))
k_jul = kpi((423, 408, 563, 481))
steps3 = crop150(page('noapr', 1), (47, 302, 752, 386))


def phone_dash(aspect=0.50, pg=None):
    """Dashboard for a phone, one narrow column of real cells: total (label + figure), then 4 KPI cards."""
    pg = pg or page('noapr', 1)
    c_ = lambda b: crop150(pg, b)
    parts = [c_((47, 136, 215, 205)), c_((423, 217, 563, 289)), c_((610, 217, 751, 289)), c_((423, 136, 563, 209)), c_((423, 408, 563, 481))]
    W = max(p.width for p in parts) + 24
    c = stack([Image.new('RGB', (W, 16), SHEETBG)] + [hcat([Image.new('RGB', (12, p.height), SHEETBG), p]) for p in parts], gap=24)
    return pad(c, aspect)


def p01():
    im = scene('laptop_large')
    clean = crop150(page('noapr', 1), (40, 40, 760, 500))
    im, _ = comp(im, [(clean, 'tab')])
    # tablet cut from the tablet_phone_flowers scene, shows the Tax Estimate 'what you pay, and when' + Deadlines dates
    src = scene('tablet_phone_flowers')
    dl = EX(DEAD)
    est = stack([crop150(dl, (58, 55, 700, 140)), hcat([crop150(dl, (58, 236, 180, 920)), crop150(dl, (190, 236, 700, 920))])])
    src, _ = comp(src, [(pad(est, 819 / 1088, align='top'), 'tab'), (Image.new('RGB', (10, 10), SHEETBG), 'phone')])
    tab = cut_device(src, (250, 595, 1150, 1765))
    tab = tab.resize((int(tab.width * .52), int(tab.height * .52)), Image.LANCZOS)
    paste_shadow(im, tab, (1534, 1690 - tab.height))
    y = title(im, 'UK Self Assessment 2025/26', 'Deadline Kit for UK sole traders', y=120, hs=124, ss=74)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y + 8, 'CHECKLIST · TAX BILL · PAYMENTS ON ACCOUNT', inter(34, 'SemiBold'), GOLD_D, 5)
    f = inter(38, 'SemiBold'); y2 = y + 105
    labels = ['2025/26 rates', 'SA103S + SA103F boxes', 'Excel + Google Sheets']
    ws = [tw(d, t, f) + 80 for t in labels]; gap = 34; x = S / 2 - (sum(ws) + gap * 2) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, y2, x + w, y2 + 76), t, f); x += w + gap
    # instant download strip
    d = ImageDraw.Draw(im)
    pill(im, (430, 1745, 1618, 1835), None, f, fill=(255, 251, 246))
    center(d, 1764, 'Instant download  ·  Example + blank file  ·  README', inter(40, 'SemiBold'), INK)
    center(d, 1868, 'Not tax advice. Does not file your return.', inter(30, 'Medium'), (120, 105, 90))
    footer(im)
    return im


def p02():
    im = background()
    y = title(im, 'What\u2019s in the Kit', '11 tabs, one job each', y=90)
    rows = [('Dashboard', 'Your bill, due dates and next 3 steps'),
            ('Start Here', 'Plain steps for first-time filers'),
            ('Settings', 'Cash basis, Scottish rates, job pay'),
            ('Income Log', 'One row per payment, checked for you'),
            ('Expenses Log', 'Costs sorted into HMRC\u2019s categories'),
            ('Mileage', 'Business miles at the flat rate'),
            ('Use of Home', 'Flat rate for hours worked at home'),
            ('SA103 Boxes', 'Every figure next to its box number'),
            ('Tax Estimate', 'Income Tax, Class 4, what to pay'),
            ('Tax Pot 26-27', 'Set money aside for next year'),
            ('Deadlines', 'Every date ticked off, days left')]
    d = ImageDraw.Draw(im); top = y + 40; h = 120; g = 22
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (190, y0, 1858, y0 + h), None, None, r=34)
        d = ImageDraw.Draw(im)
        number_disc(im, 268, y0 + h / 2, i + 1, r=36)
        d.text((340, y0 + h / 2), a, font=pf(52), fill=INK, anchor='lm')
        d.text((830, y0 + h / 2), b, font=pfi(44), fill=(92, 78, 62), anchor='lm')
    footer(im)
    return im


def p03():
    im = scene('laptop_large')
    X0, Y0 = 40, 130
    shot = crop150(page('noapr', 1), (X0, Y0, 760, 590))  # starts at the card row: leader lines never cross sheet text
    TRANS.clear(); im, (bx,) = comp(im, [(shot, 'tab')])
    tx0, ty0, sc, pl, pt = TRANS[0]
    P_ = lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    title(im, 'Your Tax Bill at a Glance', 'The Dashboard does the sums for you', y=80)
    gold_label(im, 300, 420, 'Total to pay', 'by 31 Jan 2027')
    gold_label(im, 1024, 420, 'Income Tax + Class 4', 'worked out on 2025/26 rates')
    gold_label(im, 1750, 420, 'Days left', 'to file and pay')
    tx, ty = P_(211, 136)
    leader(im, [(300, 600), (300, 650), (tx, 650), (tx, ty)])
    a0, b0 = P_(418, 213); a1, b1 = P_(756, 293)
    ImageDraw.Draw(im).rounded_rectangle((a0, b0, a1, b1), 10, outline=GOLD_D, width=5)
    gx, _ = P_(399.5, 0); ty = (b0 + b1) / 2
    leader(im, [(gx, 600), (gx, ty), (a0 - 2, ty)])
    tx, ty = P_(493, 136)
    leader(im, [(1750, 600), (1750, 650), (tx, 650), (tx, ty)])
    d = ImageDraw.Draw(im)
    center(d, 1770, 'Sam\u2019s example year: £8,549 by 31 Jan, then £2,850 by 31 Jul', pfi(54), GOLD_D)
    footer(im)
    return im


def p04():
    im = scene('tablet_phone_flowers')
    il = EX(INC)
    left = hcat([crop150(il, (54, 195, 347, 866)), crop150(il, (658, 195, 765, 866)), crop150(il, (968, 195, 1168, 866))])
    head = stack([crop150(il, (54, 50, 654, 95)), crop150(il, (54, 125, 654, 165))])
    tabshot = stack([head, left])
    im, _ = comp(im, [(pad(tabshot, 819 / 1088), 'tab'), (pad(crop150(page('noapr', 1), (40, 128, 392, 730)), 0.49), 'phone')])
    y = title(im, 'How It Works in 3 Steps', None, y=60, hs=112)
    d = ImageDraw.Draw(im)
    steps = [('LOG IT', 'Type income and costs'), ('CHECK IT', 'Look over the SA103 Boxes tab'), ('FILE AND PAY', 'Online by 31 Jan 2027')]
    cxs = [370, 1024, 1678]
    for i, (h, t) in enumerate(steps):
        number_disc(im, cxs[i], 270, i + 1, r=46)
        d = ImageDraw.Draw(im)
        center(d, 336, h, inter(40, 'Bold'), INK, cxs[i])
        center(d, 392, t, inter(34, 'Medium'), (92, 78, 62), cxs[i])
        if i < 2:
            ax0, ax1 = cxs[i] + 80, cxs[i + 1] - 80
            d.line([(ax0, 270), (ax1, 270)], fill=GOLD_D, width=4)
            d.polygon([(ax1, 270), (ax1 - 20, 259), (ax1 - 20, 281)], fill=GOLD_D)
    center(d, 470, 'Plain steps on the Start Here tab. No formulas to touch.', pfi(50), GOLD_D)
    footer(im)
    return im


def p05():
    im = background(sparkles=False)
    for (x, y, r) in [(92, 300, 42), (140, 395, 18), (1958, 290, 40), (1905, 380, 18), (92, 1760, 34), (150, 1840, 16)]:
        sparkle(im, x, y, r)
    title(im, 'SA103 Boxes, Mapped', 'Each figure sits next to its box number', y=60, hs=112, ss=60)
    page('ex6', SA103)
    t = page('ex6', SA103)                      # 600 dpi render: 4 px per 150-dpi unit
    Y0, Y1, X0, X1 = 640, 919, 44, 476
    shot = t.crop((4 * X0, 4 * Y0, 4 * X1, 4 * Y1))
    L, T, W = 60, 330, 1880
    sc = W / (X1 - X0); H = round((Y1 - Y0) * sc)
    shot_card(im, shot, (L, T, L + W, T + H))
    yy = lambda y: T + (y - Y0) * sc
    d = ImageDraw.Draw(im)
    b0, b1 = yy(836.5), yy(869.5)                # grid lines above box 23 and below box 24
    d.rounded_rectangle((L + 6, b0, L + W - 6, b1), 10, outline=(176, 128, 60), width=7)
    lab = gold_label(im, 1430, T + H + 70, 'SA103F boxes 23 + 24, checked', f=inter(42, 'Bold'), h=80)
    cy = (b0 + b1) / 2
    leader(im, [(lab[2] + 4, lab[1] + 40), (1990, lab[1] + 40), (1990, cy), (L + W + 2, cy)])
    tick(im, 150, T + H + 110, 34)
    d = ImageDraw.Draw(im)
    d.text((205, T + H + 110), 'Same figures on the short form', font=inter(36, 'Medium'), fill=INK, anchor='lm')
    center(d, T + H + 230, 'Every box number checked against HMRC\u2019s 2025/26 SA103S and SA103F forms', pfi(46), GOLD_D)
    footer(im)
    return im


def p06():
    im = background()
    y = title(im, 'Payments on Account, Explained', 'Two dates. The kit works out both amounts.', y=80, hs=108)
    d = ImageDraw.Draw(im)
    cards = [(170, '31 JAN 2027', '£8,549', ['2025/26 balance  £5,700', '+ 1st payment on account  £2,850']),
             (1064, '31 JUL 2027', '£2,850', ['2nd payment on account', 'for 2026/27'])]
    for x, date, amt, lines in cards:
        card(im, (x, 330, x + 814, 830), r=36)
        d = ImageDraw.Draw(im)
        gold_label(im, x + 407, 370, date, f=inter(42, 'Bold'))
        center(d, 470, amt, pf(150), INK, x + 407)
        yy = 680
        for ln in lines:
            center(d, yy, ln, inter(38, 'Medium'), (92, 78, 62), x + 407); yy += 54
    tbl = crop150(EX(TAXEST), (40, 674, 540, 832))
    w = 1040; h = int(w * tbl.height / tbl.width)
    chart = crop150(page('noapr', 1), (424, 741, 764, 954))
    cw = 600; ch = int(cw * chart.height / chart.width)
    top = 900; rowh = max(h, ch)
    shot_card(im, tbl, (170, top + (rowh - h) // 2, 170 + w, top + (rowh - h) // 2 + h))
    shot_card(im, chart, (1270, top, 1270 + cw, top + ch))
    y2 = top + rowh + 70
    card(im, (170, y2, 1878, y2 + 300), r=36)
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(['Each payment on account is half of your Income Tax + Class 4',
                            'Not needed if the bill is under £1,000, or over 80% was taxed at source']):
        tick(im, 260, y2 + 95 + i * 110, 32)
        d.text((320, y2 + 95 + i * 110), ln, font=inter(40, 'Medium'), fill=INK, anchor='lm')
    center(d, y2 + 350, 'Figures from Sam\u2019s example. Yours fill in as you type.', pfi(50), GOLD_D)
    footer(im)
    return im


def p07():
    im = scene('laptop_large')
    shot = crop150(EX(DEAD), (58, 232, 1104, 912))   # header to the 31 Jul 2027 row, ends right after DAYS LEFT
    im, _ = comp(im, [(shot, 'tab')])
    y = title(im, 'Never Miss a Deadline', None, y=60, hs=118)
    cards = [('5 OCT 2026', 'Register for', 'Self Assessment', 'late? register now'),
             ('31 JAN 2027', 'File online, pay the', 'balance + 1st payment', 'your 2025/26 return'),
             ('31 JUL 2027', 'Pay the 2nd', 'payment on account', 'towards 2026/27')]
    cxs = [370, 1024, 1678]
    for cx, (dt, a, b, c) in zip(cxs, cards):
        card(im, (cx - 300, 240, cx + 300, 600), r=30)
        d = ImageDraw.Draw(im)
        gold_label(im, cx, 280, dt, f=inter(40, 'Bold'))
        center(d, 410, a, inter(36, 'SemiBold'), INK, cx)
        center(d, 460, b, inter(36, 'SemiBold'), INK, cx)
        center(d, 530, c, pfi(34), GOLD_D, cx)
    d = ImageDraw.Draw(im)
    center(d, 1770, 'The Deadlines tab counts the days left and ticks off each step', pfi(50), GOLD_D)
    footer(im)
    return im


def p08():
    im = scene('laptop_large')
    tpc = crop150(EX(TAXPOT), (50, 45, 830, 590))
    cw = round(tpc.width / 0.87); tp = Image.new('RGB', (cw, round(cw / 1.57)), SHEETBG); tp.paste(tpc, (0, 0))
    im, _ = comp(im, [(tp, 'tab')])                 # tax pot fills the left 90% of the screen: the phone covers no text
    ph = scene('phone_large')
    bd = crop150(page('bl', DASH), (40, 128, 760, 1206))   # the whole real BLANK Dashboard
    ph, _ = comp(ph, [(pad(bd, 0.498), 'phone')])
    phone = cut_device(ph, (720, 590, 1330, 1860))
    phone = phone.resize((int(phone.width * .56), int(phone.height * .56)), Image.LANCZOS)
    paste_shadow(im, phone, (1462, 1672 - phone.height))
    y = title(im, 'Works in Excel and Google Sheets', 'Plus a 2026/27 tax pot, month by month', y=160, hs=104)
    spaced(ImageDraw.Draw(im), S / 2, y + 30, 'LAPTOP: EXAMPLE FILE  ·  PHONE: BLANK FILE', inter(34, 'SemiBold'), GOLD_D, 5)
    card(im, (300, 1708, 1748, 1800), r=46)
    tick(im, 370, 1754, 30)
    d = ImageDraw.Draw(im)
    d.text((420, 1754), 'Tested in Google Sheets: upload the file, every total matches', font=inter(38, 'SemiBold'), fill=INK, anchor='lm')
    f = inter(36, 'SemiBold'); labels = ['Excel 2016+', 'Google Sheets', 'Example + blank file']
    ws = [tw(d, t, f) + 70 for t in labels]; gap = 30; x = S / 2 - (sum(ws) + gap * 2) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, 1832, x + w, 1900), t, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), bw=1); x += w + gap
    footer(im, y=1950)
    return im


def p09():
    im = background()
    title(im, 'What\u2019s in Your Download', 'Three files, clearly named', y=80)
    rd = Image.open(os.path.join(WORK, 'readme-1.png')).convert('RGB')
    base = 'UK Self Assessment 2025-26 Deadline Kit -'
    files = [(crop150(page('noapr', 1), (40, 40, 760, 500)), [base, 'EXAMPLE (filled in).xlsx'], 'Sam\u2019s year, every tab working'),
             (crop150(page('bl', 1), (40, 40, 760, 500)), [base, 'BLANK (start here).xlsx'], 'Your own numbers go here'),
             (rd, ['README.pdf'], 'Read first: set up in 5 steps')]
    top, rh, g = 350, 430, 36
    for i, (img, name, sub) in enumerate(files):
        y0 = top + i * (rh + g)
        card(im, (100, y0, 1948, y0 + rh), r=36)
        if img is rd:
            h = rh - 50; w = int(h * img.width / img.height); x = 140 + (620 - w) // 2
            shot_card(im, img.crop((0, 0, img.width, int(img.width * h / w))), (x, y0 + 25, x + w, y0 + 25 + h))
        else:
            w = 600; h = int(w * img.height / img.width)
            shot_card(im, img, (140, y0 + (rh - h) // 2, 140 + w, y0 + (rh - h) // 2 + h))
        d = ImageDraw.Draw(im)
        number_disc(im, 860, y0 + rh / 2, i + 1, r=40)
        yy = y0 + rh / 2 - (95 if len(name) == 2 else 70)
        if len(name) == 2:
            d.text((940, yy), name[0], font=inter(34, 'Medium'), fill=(92, 78, 62)); yy += 52
        d.text((940, yy), name[-1], font=inter(54, 'Bold'), fill=INK); yy += 82
        d.text((940, yy), sub, font=pfi(46), fill=GOLD_D)
    d = ImageDraw.Draw(im)
    center(d, 1762, 'Instant download. Open in Excel 2016+ or upload to Google Sheets.', inter(38, 'SemiBold'), INK)
    center(d, 1826, 'Nothing is posted.', pfi(44), GOLD_D)
    footer(im)
    return im


def p10():
    im = background()
    y = title(im, '5 Reasons to Buy From Us', 'Why sole traders choose Way of Wealth Studio', y=80, hs=112)
    rows = [('Made by a qualified financial planner', 'MSc Behavioural Economics, not a template shop'),
            ("Box numbers checked against HMRC’s 2025/26 forms", 'SA103S short and SA103F full'),
            ('Beginner-friendly Start Here steps', 'Plain words, no formulas to touch'),
            ("Covers next year’s tax pot too", 'Set aside for 31 Jan and 31 Jul 2027'),
            ('One example + one blank, clearly named', "See Sam’s year, then type yours")]
    top = y + 50; h = 236; g = 44
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (190, y0, 1858, y0 + h), None, None, r=46)
        tick(im, 300, y0 + h / 2, 44)
        d = ImageDraw.Draw(im)
        d.text((390, y0 + 52), a, font=pf(56), fill=INK)
        d.text((390, y0 + 136), b, font=pfi(44), fill=(140, 104, 58))
    d = ImageDraw.Draw(im)
    center(d, 1885, 'Not tax advice. Does not file your return.  ·  Works in Excel 2016+ and Google Sheets', inter(28, 'Medium'), (120, 105, 90))
    footer(im, y=1950)
    return im


if __name__ == '__main__':
    import subprocess
    rp = os.path.join(WORK, 'readme-1.png')
    if not os.path.exists(rp):
        subprocess.run(['pdftoppm', '-r', '150', '-png', '-singlefile', '-f', '1', '-l', '1', README, rp[:-4]], check=True)
    which = [int(a) for a in sys.argv[1:]] or range(1, 11)
    for n in which:
        FRINGE.clear()
        save(globals()[f'p{n:02d}'](), os.path.join(P, f'{n:02d}.jpg'))
        print('   screen-edge green-dominant pixels after defringe (G > max(R,B)+8):', FRINGE or 'no screens')
