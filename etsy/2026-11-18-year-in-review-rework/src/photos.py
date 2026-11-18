"""10 listing photos for the Couples Money Year in Review and 2027 Goals rework (2000x2000 JPG q90).
Slot order = Couples Finance winning recipe (benchmark MyProductiveLifeCo 'Ultimate Budget for Couples', listing 1547450542):
1 hero, 2 what's included, 3-8 one tab per photo with callouts, 9 Excel + Sheets / any currency / any device (+ 3 steps), 10 5 reasons.
Scenes: etsy/lib/scenes (reused, no new AI images). Every screen = real 300-dpi LibreOffice render of the EXAMPLE file / printable PDF.
Run: python3 photos.py [n ...]"""
import os, sys, glob, subprocess
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa

P = os.path.join(KIT, 'photos'); os.makedirs(P, exist_ok=True)
render_pages(EXAMPLE, 'ex')
DASH, START, SET, YIN, SPEND, NWT, REV, GOALS, CHK, MMC, DATE = range(1, 12)
EX = lambda n: page('ex', n)


def pdf_pages():
    d = os.path.join(WORK, 'pdf'); os.makedirs(d, exist_ok=True)
    if not glob.glob(d + '/p-*.png'):
        subprocess.run(['pdftoppm', '-r', '200', '-png', PDFA4, d + '/p'], check=True)
    return d


def pdfp(n): return Image.open(os.path.join(WORK, 'pdf', f'p-{n:02d}.png')).convert('RGB')


def badge(im, cx, cy, r, lines, f=None):
    """round white badge with a gold outline (cells of text typeset with Inter Bold)"""
    f = f or inter(40, 'Bold')
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).ellipse((cx - r, cy - r + 12, cx + r, cy + r + 12), fill=80)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 252, 246), outline=GOLD, width=9)
    d.ellipse((cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16), outline=(226, 205, 172), width=2)
    lh = f.size * 1.18; y = cy - lh * len(lines) / 2
    for ln in lines:
        center(d, y, ln, f, INK, cx); y += lh


def mapper(X0, Y0, i=0):
    tx0, ty0, sc, pl, pt = TRANS[i]
    return lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)


def checkin_cards():
    pg = EX(MMC)
    return [crop150(pg, b) for b in [(602, 228, 787, 313), (787, 228, 972, 313), (602, 322, 787, 409), (787, 322, 972, 409)]]


def phone_stack(cards, aspect=0.453):
    W = max(c.width for c in cards) + 24
    c = stack([Image.new('RGB', (W, 30), SHEETBG)] + [hcat([Image.new('RGB', (12, p.height), SHEETBG), p]) for p in cards], gap=26)
    return pad(c, aspect)


def cols(pg, xs, y0, y1):
    """real cells: side-by-side column strips (150-dpi x ranges) of one row band of a rendered tab"""
    return hcat([crop150(pg, (a, y0, b, y1)) for a, b in xs])


def fitpad(img, aspect, extra_right=0.0):
    """pad right/bottom only (content stays top-left, so callout maths stays exact)"""
    w, h = img.size; W = int(w / (1 - extra_right)) if extra_right else w
    H = max(h, int(round(W / aspect))); W = max(W, int(round(H * aspect)))
    c = Image.new('RGB', (W, H), SHEETBG); c.paste(img, (0, 0)); return c


def M_(i=0):
    """map composite source px (300 dpi) -> photo px for pasted screen i"""
    tx0, ty0, sc, pl, pt = TRANS[i]
    return lambda u, v: (tx0 + (u + pl) * sc, ty0 + (v + pt) * sc)


def checkin_stack():
    pg = EX(MMC)
    summ = crop150(pg, (42, 228, 545, 408)); kp = crop150(pg, (602, 228, 972, 409))
    tbl = cols(pg, [(48, 280), (495, 735)], 477, 753)
    W = max(p.width for p in (summ, kp, tbl)) + 28
    g = Image.new('RGB', (W, 30), SHEETBG)
    row = lambda p: hcat([Image.new('RGB', (14, p.height), SHEETBG), p])
    return stack([g, row(summ), g, row(kp), g, row(tbl)])


def chart_stack():
    pg = EX(DASH)
    return stack([Image.new('RGB', (10, 24), SHEETBG), crop150(pg, (49, 693, 432, 933)), Image.new('RGB', (10, 24), SHEETBG),
                  crop150(pg, (471, 693, 855, 933))])


def cut_tablet(content, sc):
    src = scene('tablet_phone_flowers')
    src, _ = comp(src, [(fitpad(content, 0.753), 'tab'), (Image.new('RGB', (10, 10), SHEETBG), 'phone')])
    t = cut_device(src, (250, 595, 1150, 1765)); return t.resize((int(t.width * sc), int(t.height * sc)), Image.LANCZOS)


def cut_phone(content, sc):
    src = scene('phone_large')
    src, _ = comp(src, [(content, 'phone')])
    t = cut_device(src, (720, 590, 1330, 1860)); return t.resize((int(t.width * sc), int(t.height * sc)), Image.LANCZOS)


def dash_cards(boxes):
    pg = EX(DASH); return [crop150(pg, b) for b in boxes]


K_TOP = [(480, 150, 640, 235), (480, 243, 640, 325)]                 # total income, saved or invested
K_ROW2 = [(46, 381, 213, 467), (261, 381, 427, 467), (470, 381, 643, 467), (679, 381, 858, 467)]


def side_label(im, cx, y, t, sub, target, side='left', f=None):
    """gold label at (cx, y); elbow leader from the label's inner edge to target (x, y) on a screen edge / card edge"""
    b = gold_label(im, cx, y, t, sub, f=f or inter(38, 'Bold'), h=70)
    tx, ty = target
    tx = tx - 16 if side == 'left' else tx + 16
    sx = b[2] + 10 if side == 'left' else b[0] - 10
    leader(im, [(sx, y + 35), ((sx + tx) / 2, y + 35), ((sx + tx) / 2, ty), (tx, ty)])


# ------------------------------------------------------------------ 1 hero (laptop + tablet + phone)
def p01():
    im = clean_keys(scene('laptop_large'))
    im, _ = comp(im, [(crop150(EX(DASH), (40, 40, 870, 575)), 'tab')])
    tab = cut_tablet(chart_stack(), 0.47)
    paste_shadow(im, tab, (14, 1705 - tab.height))
    ph = cut_phone(phone_stack(checkin_cards()), 0.40)
    paste_shadow(im, ph, (1745, 1705 - ph.height))
    y = title(im, 'Couples Money Year in Review', 'Look back on your whole year, then plan 2027 together', y=90, hs=118, ss=64)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y + 2, 'DASHBOARD  ·  2027 GOALS  ·  12 MONTHLY CHECK-INS  ·  PRINTABLES', inter(32, 'SemiBold'), GOLD_D, 5)
    for cx, ln in [(330, ['WHOLE', 'YEAR']), (1024, ['2027', 'GOALS']), (1718, ['SHEETS', '+ EXCEL'])]:
        badge(im, cx, 590, 118, ln, f=inter(38, 'Bold'))
    pill(im, (360, 1752, 1688, 1842), None, None, fill=(255, 251, 246))
    d = ImageDraw.Draw(im)
    center(d, 1773, 'Instant download  ·  Example + blank copy  ·  A4 + US Letter pages', inter(40, 'SemiBold'), INK)
    footer(im)
    return im


# ------------------------------------------------------------------ 2 what's included
def p02():
    im = background()
    y = title(im, 'Everything Included', '11 tabs + 12 printable pages, one job each', y=80, hs=118)
    rows = [('Dashboard', '9 headline numbers, 6 charts'), ('Start Here', '5 plain steps'), ('Year in Numbers', 'all 12 months'),
            ('Spending Review', 'was it worth it?'), ('Net Worth', 'start vs end of year'), ('Year in Review', '8 questions together'),
            ('2027 Goals', 'monthly amount + reality check'), ('2027 Check-ins', '12 months on one tab'),
            ('Monthly Money Check-in', 'your month in plain words'), ('Money Date', '30-minute agenda'),
            ('Printable pages', 'A4 + US Letter, fillable'), ('Example + blank copy', 'see it filled in first')]
    top = y + 40; h = 106; g = 16
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (90, y0, 1170, y0 + h), None, None, r=30)
        tick(im, 155, y0 + h / 2, 26)
        d = ImageDraw.Draw(im)
        d.text((205, y0 + h / 2), a, font=pf(44), fill=INK, anchor='lm')
        aw = tw(d, a, pf(44))
        d.text((205 + aw + 22, y0 + h / 2 + 4), b, font=pfi(36), fill=(120, 96, 64), anchor='lm')
    tab = cut_tablet(checkin_stack(), 0.82)
    tx = 2048 - tab.width - 20; ty0 = top + 20
    paste_shadow(im, tab, (tx, ty0))
    cx = tx + tab.width / 2
    d = ImageDraw.Draw(im)
    center(d, ty0 + tab.height + 26, 'Monthly Money Check-in tab', pfi(40), GOLD_D, cx)
    f = inter(36, 'SemiBold')
    for i, t in enumerate(['Excel 2016+', 'Google Sheets', 'Any currency']):
        yy = ty0 + tab.height + 105 + i * 96; w = tw(d, t, f) + 90
        pill(im, (cx - w / 2, yy, cx + w / 2, yy + 74), t, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), bw=1)
        d = ImageDraw.Draw(im)
    footer(im)
    return im


# ------------------------------------------------------------------ 3 dashboard charts
def p03():
    im = clean_keys(scene('laptop_large'))
    X0, Y0 = 40, 686
    TRANS.clear(); im, _ = comp(im, [(fitpad(crop150(EX(DASH), (X0, Y0, 866, 1214)), 1.57), 'tab')])
    m = M_()
    P_ = lambda x, y: m((x - X0) * 2, (y - Y0) * 2)
    title(im, 'Your Year at a Glance', 'The Dashboard draws 6 charts for you', y=80)
    gold_label(im, 330, 420, 'Income vs spending', 'every month')
    gold_label(im, 1024, 420, 'Where it went', 'by category')
    gold_label(im, 1720, 420, 'Net worth', 'start vs end of year')
    tx, ty = P_(62, 694); leader(im, [(330, 590), (330, 650), (tx, 650), (tx, ty)])
    tx, ty = P_(842, 694); leader(im, [(1024, 590), (1024, 640), (tx, 640), (tx, ty)])
    tx, ty = P_(855, 1150); leader(im, [(1720, 590), (1720, 660), (1990, 660), (1990, ty), (tx + 4, ty)])
    d = ImageDraw.Draw(im)
    center(d, 1765, 'Plus 9 headline numbers, goal progress and spent vs plan', pfi(52), GOLD_D)
    footer(im)
    return im


# ------------------------------------------------------------------ 4 year in numbers (tablet, 5 columns x 12 months)
def p04():
    im = scene('tablet_coffee')
    pg = EX(YIN)
    xs = [(64, 207), (637, 780), (1067, 1210), (1352, 1462)]
    tbl = cols(pg, xs, 275, 903)
    nw = cols(EX(NWT), [(64, 330), (610, 785)], 808, 902)
    tbl = stack([tbl, Image.new('RGB', (10, 40), SHEETBG), nw])
    TRANS.clear(); im, (bx,) = comp(im, [(fitpad(tbl, 0.721), 'tab')])
    m = M_()
    rowy = lambda r: (322 + (r - 0.5) * 43.33 - 275) * 2          # month r (1-12) centre, source px
    title(im, 'Your Whole Year, Month by Month', 'January to December, not one sample month', y=70, hs=104, ss=60)
    xl, xr = bx[0], bx[2]
    side_label(im, 300, 600, 'All 12 months', 'spending + left over', (xl, m(0, rowy(1))[1]))
    side_label(im, 300, 1420, 'Year total', 'and monthly average', (xl, m(0, (842 + 14 - 275) * 2)[1]))
    lb = gold_label(im, 1745, 860, 'Left over', 'worked out for you', f=inter(38, 'Bold'), h=70)
    bxy = m(0, (322 + 4 * 43.33 - 275) * 2)[1]          # row border between Apr and May
    lx, _ = m((143 + 143) * 2 + 40, 0)
    leader(im, [(lb[0] - 10, 895), (xr + 40, 895), (xr + 40, bxy), (lx, bxy)])
    side_label(im, 1745, 1340, 'How it felt', 'good, OK or tough', (xr, m(0, rowy(10))[1]), side='right')
    d = ImageDraw.Draw(im)
    pill(im, (60, 1738, 1180, 1812), None, None, fill=(255, 251, 246))
    d = ImageDraw.Draw(im); center(d, 1750, 'Below the months: net worth, end of year', pfi(40), GOLD_D, 620)
    footer(im)
    return im


# ------------------------------------------------------------------ 5 Year in Review (8 questions)
def p05():
    im = scene('laptop_phone')
    pg = EX(REV)
    tbl = cols(pg, [(64, 457), (1152, 1497)], 279, 762)
    TRANS.clear()
    phone = phone_stack(dash_cards([K_ROW2[0], K_ROW2[1]] + K_TOP))
    im, _ = comp(im, [(fitpad(tbl, 1.552, extra_right=0.15), 'tab'), (phone, 'phone')])
    m = M_()
    title(im, 'Look Back Together', '8 questions: answer apart first, then together', y=80, hs=118, ss=62)
    xl = m(0, 0)[0]
    gold_label(im, 330, 420, '8 look-back questions', 'wins, worth it, stress')
    gold_label(im, 1100, 420, 'Answer apart first', 'then fill in Together')
    tx, ty = xl - 18, m(0, 30 * 2 + 45 * 2)[1]
    leader(im, [(330, 590), (330, ty), (tx, ty)])
    tx2, ty2 = m(393 * 2 + 172 * 2, 0)
    leader(im, [(1100, 590), (1100, 650), (tx2, 650), (tx2, ty2 - 4)])
    d = ImageDraw.Draw(im)
    center(d, 1700, 'Phone: your year in numbers  ·  Laptop: questions 1-5 of 8', inter(34, 'SemiBold'), INK)
    center(d, 1770, 'Answers from the example couple, Sam and Alex', pfi(48), GOLD_D)
    footer(im)
    return im


# ------------------------------------------------------------------ 6 2027 goals (tablet + phone)
def p06():
    im = scene('tablet_phone_flowers')
    pg = EX(GOALS)
    a = cols(pg, [(112, 400), (513, 637), (884, 1018)], 252, 566)
    b = cols(pg, [(112, 400), (760, 884), (1017, 1140)], 636, 905)
    c = cols(pg, [(110, 665), (875, 1020)], 938, 1138)
    gap = Image.new('RGB', (10, 40), SHEETBG)
    tb = stack([a, gap, b, gap, c])
    cards = dash_cards([K_ROW2[2], K_ROW2[3]]) + [checkin_cards()[2]] + dash_cards([K_TOP[1]])
    ph = phone_stack(cards)
    TRANS.clear(); im, (bt, bp) = comp(im, [(fitpad(tb, 0.753), 'tab'), (ph, 'phone')])
    m = M_(0); mp = M_(1)
    title(im, '2027 Goals That Actually Fit', 'Pick 3 to 5 together. The sheet does the maths.', y=60, hs=108, ss=60)
    gold_label(im, 560, 360, 'Monthly amount', 'for each goal')
    gold_label(im, 1430, 360, 'Goal progress', 'on the Dashboard')
    ob = gold_label(im, 1775, 1640, 'On track or behind', 'from your check-ins')
    # dots on real values: the first goal's Needed-per-month cell, its Status cell, and the GOAL PROGRESS card
    tx, ty = m((288 + 124) * 2 + 34, (325 - 252) * 2)
    _, tyb = m(0, (349 - 252) * 2)                         # border under the first goal: no text on it
    leader(im, [(560, 530), (560, 565), (1172, 565), (1172, tyb), (tx, tyb), (tx, ty)])
    tx2, ty2 = m((412 + 108) * 2, a.height + 40 + (776 - 636) * 2)   # right of 'Behind' in the Status column
    leader(im, [(ob[0] - 10, 1675), (1205, 1675), (1205, ty2), (tx2, ty2)])
    y2 = 30 + cards[0].height + 26 + cards[1].height / 2
    tx3, ty3 = mp(12 + cards[1].width - 22, y2)
    leader(im, [(1430, 530), (1430, 565), (1650, 565), (1650, ty3), (tx3, ty3)])
    footer(im)
    return im


# ------------------------------------------------------------------ 7 12 monthly check-ins (grid)
def p07():
    im = clean_keys(scene('laptop_large'))
    pg = EX(CHK)
    R = {8: 210, 9: 240, 13: 361.5, 24: 695, 27: 786.5, 33: 969, 36: 1060}
    xs = [(56, 290), (290, 376), (376, 887), (1248, 1352)]
    band = lambda y0, y1: cols(pg, xs, y0, y1)
    g = Image.new('RGB', (10, 14), SHEETBG)
    parts = [band(R[8], R[13]), g, band(R[24], R[27]), g, band(R[27], R[36])]
    tbl = stack(parts)
    TRANS.clear(); im, (bx,) = comp(im, [(fitpad(tbl, 1.57), 'tab')])
    m0 = M_()
    # paint out the scene's left sparkle cluster (it sat behind a callout pill): per-row blend of the clean background either side
    A = np.array(im).astype(float); X0_, X1_, Y0_, Y1_ = 120, 410, 860, 1170
    for yy in range(Y0_, Y1_):
        l, r = A[yy, X0_], A[yy, X1_]
        t = np.linspace(0, 1, X1_ - X0_)[:, None]
        A[yy, X0_:X1_] = l * (1 - t) + r * t
    im = Image.fromarray(A.clip(0, 255).astype('uint8'))
    # zoom: laptop larger and higher (crop 1600 px square, scale to 2048)
    OX, OY, LZ = 175, 348, 1700; Z = S / LZ
    im = im.crop((OX, OY, OX + LZ, OY + LZ)).resize((S, S), Image.LANCZOS)
    m = lambda u, v: tuple(((c - o) * Z) for c, o in zip(m0(u, v), (OX, OY)))
    title(im, '12 Monthly Check-ins for 2027', 'One column per month, plan vs actual worked out', y=60, hs=108)
    xl = (bx[0] - OX) * Z
    h1 = parts[0].height; h2 = parts[2].height
    t1 = m(0, (240 + 60 - 210) * 2)[1]; t2 = m(0, h1 + 14 + h2 / 2)[1]; t3 = m(0, h1 + h2 + 28 + parts[4].height / 2)[1]
    side_label(im, 165, t1 - 120, 'Money in', 'both incomes', (xl, t1))
    side_label(im, 165, t2 - 35, 'Spent vs plan', 'totals worked out', (xl, t2))
    side_label(im, 165, t3 + 40, 'Goal top-ups', 'goals, left over', (xl, t3))
    d = ImageDraw.Draw(im)
    center(d, 1765, 'Type each month at your money date. Nothing else to set up.', pfi(52), GOLD_D)
    footer(im)
    return im


# ------------------------------------------------------------------ 8 Monthly Money Check-in (behaviour feature)
def p08():
    im = scene('tablet_coffee')
    st = checkin_stack()
    TRANS.clear(); im, (bx,) = comp(im, [(fitpad(st, 0.721), 'tab')])
    m = M_()
    title(im, 'Monthly Check-in', 'See your month in plain words', y=70, hs=120, ss=72)
    xl, xr = bx[0], bx[2]
    yS = m(0, (30 + 90) * 2)[1]; yK = m(0, (30 + 180 + 30 + 90) * 2)[1]; yT = m(0, (30 + 180 + 30 + 181 + 30 + 140) * 2)[1]
    side_label(im, 300, yS - 35, 'Your month', 'in plain words', (xl, yS))
    side_label(im, 300, yT - 35, 'Plan vs actual', 'by category', (xl, yT))
    side_label(im, 1745, 850, '4 numbers', 'earned, spent,\ngoals, left over', (xr, yK), side='right')
    pill(im, (70, 1748, 1250, 1824), None, None, fill=(255, 251, 246))
    d = ImageDraw.Draw(im); center(d, 1760, 'Plus 5 questions to talk through together', pfi(42), GOLD_D, 660)
    footer(im)
    return im


# ------------------------------------------------------------------ 9 Excel + Sheets, any currency, any device, print (+ 3 steps)
def p09():
    im = scene('laptop_phone')
    gbp = render_variant(EXAMPLE, 'gbp', [('Settings', 'C9', '£')], [10])
    pg = Image.open(gbp[10]).convert('RGB')
    cards = [crop150(pg, b) for b in [(602, 228, 787, 313), (787, 228, 972, 313), (602, 322, 787, 409), (787, 322, 972, 409)]]
    tbl = cols(EX(SPEND), [(66, 365), (365, 505), (782, 920), (920, 1060)], 280, 803)
    im, _ = comp(im, [(fitpad(tbl, 1.552, extra_right=0.16), 'tab'), (phone_stack(cards), 'phone')])
    y = title(im, 'Works in Excel + Google Sheets', None, y=60, hs=112)
    d = ImageDraw.Draw(im)
    steps = [('DOWNLOAD', 'Instant, from Etsy'), ('OPEN', 'Excel, or upload to Sheets'), ('FILL IN TOGETHER', 'or print the pages')]
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
    center(d, 478, 'Laptop in $, phone set to £: one currency setting', pfi(48), GOLD_D)
    f = inter(34, 'SemiBold'); labels = ['Any currency', 'Laptop, tablet, phone', 'Works offline', 'Print A4 + US Letter']
    ws = [tw(d, t, f) + 64 for t in labels]; gap = 22; x = S / 2 - (sum(ws) + gap * 3) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, 1730, x + w, 1804), t, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), bw=1); x += w + gap
    footer(im)
    return im


# ------------------------------------------------------------------ 10 5 reasons
def p10():
    im = background()
    y = title(im, '5 Reasons to Buy From Us', 'Why couples choose Way of Wealth Studio', y=80, hs=112)
    rows = [('Made by a qualified financial planner', 'MSc Behavioural Economics, not a template shop'),
            ('The whole year, not one month', 'January to December look-back + 12 check-ins for 2027'),
            ('Your own file, works offline', 'Excel or Google Sheets, no web app or sign-up'),
            ('Tested formulas, locked so they never break', '0 errors in the example and the blank copy'),
            ('Simple: one page per step', '5-step Start Here, example + blank, printable pages')]
    top = y + 50; h = 236; g = 44
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (190, y0, 1858, y0 + h), None, None, r=46)
        tick(im, 300, y0 + h / 2, 44)
        d = ImageDraw.Draw(im)
        d.text((390, y0 + 52), a, font=pf(56), fill=INK)
        d.text((390, y0 + 136), b, font=pfi(44), fill=(140, 104, 58))
    d = ImageDraw.Draw(im)
    center(d, 1885, 'Questions? Joel answers every email himself  ·  joel@wayofwealthcoaching.com', inter(28, 'Medium'), (120, 105, 90))
    footer(im, y=1950)
    return im


if __name__ == '__main__':
    which = [int(a) for a in sys.argv[1:]] or range(1, 11)
    for n in which:
        FRINGE.clear()
        save(globals()[f'p{n:02d}'](), os.path.join(P, f'{n:02d}.jpg'))
        print('   screen-edge green-dominant pixels after defringe:', FRINGE or 'no screens')
