"""10 listing photos for the Nail Tech Income & Expense Tracker rework (2000x2000 JPG q90).
Slot order copied (structure only) from the benchmark AnarosaStudioCo 'Nail Tech Spreadsheet All in One' (Etsy 4518077032):
cover, everything included, dashboard at a glance, feature slides, 3 steps, reasons. House style = Moving In Together.
Scenes: etsy/lib/scenes (reused, no AI calls). Screens: real 300-dpi LibreOffice renders of the EXAMPLE file.
Run: python3 photos.py [n ...]"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa

P = os.path.join(KIT, 'photos'); os.makedirs(P, exist_ok=True)
render_pages(EXAMPLE, 'ex')
EX = lambda n: page('ex', n)
DASH, START, SET, CL, EXP, STK, RB, MS, PC, TX, CI = range(1, 12)
c = lambda n, b: crop150(EX(n), b)
SUB = (92, 78, 62)


def phone_dash(aspect=0.461, charts=((40, 435, 352, 628), (40, 650, 352, 873), (40, 892, 352, 1115))):
    """Phone screen = a narrow column of the real Dashboard: the title line, then three charts, whole and uncut."""
    parts = [c(DASH, (40, 38, 352, 68))] + [c(DASH, b) for b in charts]
    return pad(stack(parts), aspect)


def phone_on(im, shot, x, bottom, scale=0.56):
    """real screenshot on the phone_large phone, cut out and placed on another scene with a soft shadow"""
    ph, _ = comp(scene('phone_large'), [(shot, 'phone')])
    phone = cut_device(ph, (720, 590, 1330, 1860))
    phone = phone.resize((int(phone.width * scale), int(phone.height * scale)), Image.LANCZOS)
    paste_shadow(im, phone, (x, bottom - phone.height))


def pills(im, y, labels, f=None, gold=False, h=76, gap=30):
    d = ImageDraw.Draw(im); f = f or inter(38, 'SemiBold')
    ws = [tw(d, t, f) + 80 for t in labels]; x = S / 2 - (sum(ws) + gap * (len(labels) - 1)) / 2
    for t, w in zip(labels, ws):
        if gold: pill(im, (x, y, x + w, y + h), t, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), bw=1)
        else: pill(im, (x, y, x + w, y + h), t, f)
        x += w + gap


# ---------------------------------------------------------------- 1 cover
def p01():
    im = scene('laptop_large')
    im, _ = comp(im, [(c(DASH, (40, 30, 668, 430)), 'tab')])          # title to the second card row: whole rows, full screen
    phone_on(im, phone_dash(), 1600, 1700)
    y = title(im, 'Nail Tech Income Tracker', 'See your real profit after every client', y=110, hs=124, ss=76)
    spaced(ImageDraw.Draw(im), S / 2, y + 6, 'CLIENTS · TIPS · SUPPLIES · PRICING · TAX POT', inter(34, 'SemiBold'), GOLD_D, 5)
    pills(im, y + 100, ['11 tabs', 'Excel + Google Sheets', 'Any currency'])
    pill(im, (400, 1755, 1648, 1845), None, None, fill=(255, 251, 246))
    d = ImageDraw.Draw(im)
    center(d, 1774, 'Instant download  ·  Example + blank file  ·  README', inter(40, 'SemiBold'), INK)
    footer(im)
    return im


# ---------------------------------------------------------------- 2 everything included (infographic 1)
def p02():
    im = background()
    y = title(im, 'Everything Your Nail Business Needs', '11 tabs, one job each', y=90, hs=104)
    rows = [('Dashboard', 'Profit, tips, 5 charts, your next steps'),
            ('Start Here', 'Five plain steps, no formulas to touch'),
            ('Settings', 'Currency, year start, goal, target pay'),
            ('Client Log', 'Every appointment, tip and how they paid'),
            ('Expenses', '16 nail categories, from gel to chair rent'),
            ('Supplies & Stock', 'Reorder levels so you never run out'),
            ('Rent & Bills', 'Chair or booth rent as one monthly figure'),
            ('Monthly Summary', '12 months side by side'),
            ('Pricing Check', 'True cost and profit per hour'),
            ('Tax Set-Aside', 'Your % of profit, moved every month'),
            ('Money Check-in', 'Your month in plain words + 5 questions')]
    top = y + 40; h = 116; g = 22
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (170, y0, 1878, y0 + h), None, None, r=34)
        d = ImageDraw.Draw(im)
        number_disc(im, 248, y0 + h / 2, i + 1, r=36)
        d = ImageDraw.Draw(im)
        d.text((320, y0 + h / 2), a, font=pf(50), fill=INK, anchor='lm')
        d.text((860, y0 + h / 2), b, font=pfi(42), fill=SUB, anchor='lm')
    footer(im)
    return im


# ---------------------------------------------------------------- 3 dashboard at a glance
def p03():
    im = scene('laptop_large')
    X0, Y0 = 40, 30
    shot = c(DASH, (X0, Y0, 668, 430))
    TRANS.clear(); im, _ = comp(im, [(shot, 'tab')])
    tx0, ty0, sc, pl, pt = TRANS[0]
    P_ = lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    title(im, 'Your Business at a Glance', 'The Dashboard does every sum for you', y=80)
    gold_label(im, 330, 420, 'Profit so far', 'after every cost')
    gold_label(im, 1024, 420, 'Tips: card + cash', 'counted separately')
    gold_label(im, 1720, 420, 'Next steps', 'reorder, prices, tax pot')
    hx, hy = P_(45, 200)                                              # to the left edge of the profit card, outside its text
    leader(im, [(330, 600), (330, hy), (hx - 12, hy)])
    gx, _ = P_(519, 0); cx, cy = P_(498, 226)                       # down the gap between the card columns, to the Tips card
    leader(im, [(1024, 600), (1024, 660), (gx, 660), (gx, cy), (cx + 10, cy)])
    a0, b0 = P_(45, 265); a1, b1 = P_(663, 345)
    ImageDraw.Draw(im).rounded_rectangle((a0 - 4, b0, a1 + 4, b1), 10, outline=GOLD_D, width=5)
    my = (b0 + b1) / 2
    leader(im, [(1720, 600), (1720, my), (a1 + 6, my)])
    d = ImageDraw.Draw(im)
    center(d, 1770, 'Mia\u2019s example year: £16,308 profit from 723 appointments', pfi(54), GOLD_D)
    footer(im)
    return im


# ---------------------------------------------------------------- 4 clients and tips
def p04():
    im = background()
    title(im, 'Every Client, Every Tip', 'Cash or card, logged in seconds', y=80)
    cols = c(CL, (55, 215, 900, 521))         # every column from Date to Total, so price + tip + retail = total on screen
    L, T, W = 110, 360, 1828
    H = round(W * cols.height / cols.width)
    shot_card(im, cols, (L, T, L + W, T + H))
    sc = W / (cols.width / 2)     # px per 150-dpi unit
    yy = lambda y: T + (y - 215) * sc
    d = ImageDraw.Draw(im)
    # highlight the tipped row (7 Nov 2025, Niamh O., gel manicure 30 + tip 3 + retail)
    r0, r1 = yy(500), yy(521)
    d.rounded_rectangle((L + 6, r0, L + W - 6, r1), 8, outline=(176, 128, 60), width=6)
    yb = T + H + 70
    gold_label(im, 360, yb, 'Pick the service', 'from your own menu')
    gold_label(im, 1024, yb, 'Tip + how they paid', 'card, cash or transfer')
    gold_label(im, 1690, yb, 'Total adds itself', 'price + tip + retail')
    xx = lambda x: L + (x - 55) * sc
    for lx, col in [(360, 385), (1024, 628), (1690, 860)]:          # service, tip / paid by, total columns
        tx = xx(col); my = (r1 + yb) / 2
        leader(im, [(lx, yb - 6), (lx, my), (tx, my), (tx, r1 + 4)])
    d = ImageDraw.Draw(im)
    center(d, yb + 230, 'Room for 800 appointments a year. Tips are split card and cash on the Dashboard.', pfi(48), GOLD_D)
    kp = c(DASH, (372, 192, 501, 260)); kw = 560; kh = round(kw * kp.height / kp.width)
    shot_card(im, kp, (1024 - kw // 2, yb + 330, 1024 + kw // 2, yb + 330 + kh))
    d = ImageDraw.Draw(im)
    d.text((1024 - kw // 2 - 40, yb + 330 + kh / 2), 'On the Dashboard', font=pfi(46), fill=GOLD_D, anchor='rm')
    footer(im)
    return im


# ---------------------------------------------------------------- 5 where the money goes
def p05():
    im = background()
    title(im, 'Know Where Your Money Goes', 'Every month, every category, worked out', y=80, hs=108)
    summ = c(MS, (62, 262, 1520, 700))
    L, T, W = 70, 330, 1908
    H = round(W * summ.height / summ.width)
    shot_card(im, summ, (L, T, L + W, T + H))
    y2 = T + H + 70
    ch = c(DASH, (40, 650, 352, 873))
    tx = hcat([c(TX, (62, 300, 250, 720)), c(TX, (360, 300, 665, 720)), c(TX, (1000, 300, 1290, 720))])
    w1 = 820; h1 = round(w1 * ch.height / ch.width)
    shot_card(im, ch, (70, y2, 70 + w1, y2 + h1))
    x2 = 70 + w1 + 50; w2 = 1978 - x2; h2 = round(w2 * tx.height / tx.width)
    shot_card(im, tx, (x2, y2, 1978, y2 + h2))
    gold_label(im, x2 + w2 / 2, y2 + h2 + 36, 'Tax set-aside: your %, any country', f=inter(36, 'Bold'), h=68)
    d = ImageDraw.Draw(im)
    center(d, 1785, 'Monthly Summary, costs by category and your tax pot, all from the logs', pfi(46), GOLD_D)
    footer(im)
    return im


# ---------------------------------------------------------------- 6 pricing check
def p06():
    im = background()
    title(im, 'Price Every Service Properly', 'True cost, profit per hour, the price that pays you', y=80, hs=112, ss=58)
    pg = EX(PC)
    rows = (300, 668)
    parts = [crop150(pg, (62, rows[0], 300, rows[1])), crop150(pg, (300, rows[0], 410, rows[1])),
             crop150(pg, (745, rows[0], 847, rows[1])), crop150(pg, (955, rows[0], 1076, rows[1])),
             crop150(pg, (1250, rows[0], 1525, rows[1]))]
    tbl = hcat(parts)
    L, T, W = 90, 330, 1868
    H = round(W * tbl.height / tbl.width)
    shot_card(im, tbl, (L, T, L + W, T + H))
    sc = W / (tbl.width / 2)
    yy = lambda y: T + (y - rows[0]) * sc
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((L + 6, yy(474), L + W - 6, yy(500)), 8, outline=(176, 128, 60), width=6)
    wc = crop150(pg, (62, 848, 1522, 892))
    y2 = T + H + 50
    h2 = round(1868 * wc.height / wc.width)
    shot_card(im, wc, (90, y2, 1958, y2 + h2))
    d = ImageDraw.Draw(im)
    tick(im, 200, y2 + h2 + 110, 34)
    d.text((255, y2 + h2 + 110), 'Acrylic infill earns £19.70 an hour: the sheet says raise it to £39', font=inter(40, 'SemiBold'), fill=INK, anchor='lm')
    center(d, y2 + h2 + 200, 'Your chair rent and bills are shared across every service', pfi(48), GOLD_D)
    pills(im, y2 + h2 + 320, ['Profit per hour', 'Price for your target', '10% worth check'], gold=True)
    footer(im)
    return im


# ---------------------------------------------------------------- 7 supplies and stock
def p07():
    im = scene('laptop_large')
    banner = c(STK, (62, 232, 870, 280))
    tbl = hcat([c(STK, (62, 280, 365, 748)), c(STK, (870, 280, 1375, 748))])
    im, _ = comp(im, [(stack([banner, tbl]), 'tab')])
    title(im, 'Never Run Out Mid-Set', 'Reorder levels for gel, acrylic and disposables', y=80)
    cards = [('6 TO REORDER', 'Shown in coral', 'and on the Dashboard'), ('REORDER AT', 'You set the level', 'for each product'),
             ('STOCK VALUE', 'Cost x what you hold', 'worked out for you')]
    cxs = [370, 1024, 1678]
    for cx, (a, b, c_) in zip(cxs, cards):
        card(im, (cx - 300, 330, cx + 300, 610), r=30)
        gold_label(im, cx, 360, a, f=inter(38, 'Bold'))
        d = ImageDraw.Draw(im)
        center(d, 470, b, inter(38, 'SemiBold'), INK, cx)
        center(d, 528, c_, pfi(36), GOLD_D, cx)
    d = ImageDraw.Draw(im)
    center(d, 1770, 'Supplies & Stock tab: what you have, what to buy, what it is worth', pfi(50), GOLD_D)
    footer(im)
    return im


# ---------------------------------------------------------------- 8 monthly check-in (feature photo)
def p08():
    im = background()
    title(im, 'Monthly Check-in', 'See your month in plain words', y=80, hs=124, ss=70)
    pg = EX(CI)
    summ = stack([crop150(pg, (48, 253, 865, 400)), crop150(pg, (48, 400, 865, 430))], gap=0)
    L, T, W = 194, 480, 1660
    H = round(W * summ.height / summ.width)
    shot_card(im, summ, (L, T, L + W, T + H))
    gold_label(im, 1024, T - 100, 'Written by the sheet from your logs', f=inter(38, 'Bold'), h=72)
    qs = crop150(pg, (48, 476, 865, 750))
    y2 = T + H + 140
    H2 = round(W * qs.height / qs.width)
    shot_card(im, qs, (L, y2, L + W, y2 + H2))
    gold_label(im, 1024, y2 - 100, '5 honest questions, answered by you', f=inter(38, 'Bold'), h=72)
    d = ImageDraw.Draw(im)
    pills(im, y2 + H2 + 70, ['Copy-ready summary', 'Spending vs your plan', 'Works on its own'])
    d = ImageDraw.Draw(im)
    center(d, y2 + H2 + 200, 'Ten minutes at the end of the month, in your own currency.', pfi(48), GOLD_D)
    footer(im)
    return im


# ---------------------------------------------------------------- 9 three steps + download
def p09():
    im = scene('tablet_phone_flowers')
    tab = c(CL, (35, 50, 903, 1222))                                  # whole Client Log page: every column Date to Total
    ph = phone_dash(0.465, charts=((372, 435, 676, 628), (372, 650, 676, 873), (40, 892, 352, 1115)))
    im, _ = comp(im, [(pad(tab, 819 / 1088), 'tab'), (ph, 'phone')])
    title(im, 'How It Works in 3 Steps', None, y=60, hs=112)
    d = ImageDraw.Draw(im)
    steps = [('SET UP', 'Currency, menu, rent'), ('LOG', 'Clients, tips and costs'), ('CHECK IN', 'Monthly, in 10 minutes')]
    cxs = [370, 1024, 1678]
    for i, (h, t) in enumerate(steps):
        number_disc(im, cxs[i], 270, i + 1, r=46)
        d = ImageDraw.Draw(im)
        center(d, 336, h, inter(40, 'Bold'), INK, cxs[i])
        center(d, 392, t, inter(34, 'Medium'), SUB, cxs[i])
        if i < 2:
            ax0, ax1 = cxs[i] + 80, cxs[i + 1] - 80
            d.line([(ax0, 270), (ax1, 270)], fill=GOLD_D, width=4)
            d.polygon([(ax1, 270), (ax1 - 20, 259), (ax1 - 20, 281)], fill=GOLD_D)
    center(d, 470, 'Example file + blank file + README. Instant download.', pfi(50), GOLD_D)
    pill(im, (330, 1790, 1718, 1880), None, None, fill=(255, 251, 246))
    d = ImageDraw.Draw(im)
    center(d, 1810, 'Opens in Excel 2016+ and Google Sheets. Nothing is posted.', inter(38, 'SemiBold'), INK)
    footer(im, y=1950)
    return im


# ---------------------------------------------------------------- 10 five reasons (infographic 2)
def p10():
    im = background()
    y = title(im, '5 Reasons to Buy From Us', 'Why nail techs choose Way of Wealth Studio', y=80, hs=112)
    rows = [('Made by a qualified financial planner', 'MSc Behavioural Economics, not a template shop'),
            ('A real .xlsx for Excel and Google Sheets', 'Nothing opens in Canva, no password-locked tabs'),
            ('Built for nail techs', 'Tips by cash and card, gel and acrylic stock, chair rent'),
            ('Profit per hour for every service', 'And the price that would pay you properly'),
            ('Monthly money check-in', 'Your month in plain words, plus 5 honest questions')]
    top = y + 50; h = 236; g = 44
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (170, y0, 1878, y0 + h), None, None, r=46)
        tick(im, 280, y0 + h / 2, 44)
        d = ImageDraw.Draw(im)
        d.text((370, y0 + 52), a, font=pf(56), fill=INK)
        d.text((370, y0 + 136), b, font=pfi(44), fill=(140, 104, 58))
    d = ImageDraw.Draw(im)
    center(d, 1885, 'Questions answered by Joel himself  ·  any currency, any country', inter(30, 'Medium'), (120, 105, 90))
    footer(im, y=1950)
    return im


if __name__ == '__main__':
    which = [int(a) for a in sys.argv[1:]] or range(1, 11)
    for n in which:
        FRINGE.clear()
        save(globals()[f'p{n:02d}'](), os.path.join(P, f'{n:02d}.jpg'))
        print('   screen-edge green-dominant pixels after defringe:', FRINGE or 'no screens')
