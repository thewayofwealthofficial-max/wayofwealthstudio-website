"""10 listing photos for the Couples Money Conversation Kit (premium), 2000x2000 JPG q90.
Scenes: etsy/lib/scenes (reused, no AI calls). Screens: real 300-dpi renders of the EXAMPLE planner (LibreOffice),
the filled-in demo of the 4-Week Plan PDF (build_pdf.py --demo) and the original Conversation Starter PDF.
Run: python3 photos.py [n ...]"""
import os, sys, subprocess
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa

P = os.path.join(KIT, 'photos'); os.makedirs(P, exist_ok=True)
render_pages(EXAMPLE, 'ex')
DASH, START, SETT, INC, BILLS, SPEND, GOALS, DATES, CHECK, CARDS = range(1, 11)
EX = lambda n: page('ex', n)
DEMO = os.path.join(WORK, 'demo'); ORIG = os.path.join(WORK, 'orig')
if not os.path.exists(os.path.join(DEMO, 'p-03.png')):
    subprocess.run(['python3', os.path.join(HERE, 'build_pdf.py'), DEMO, '--demo', os.path.join(HERE, 'demo_values.json')], check=True)
    subprocess.run(['pdftoppm', '-r', '300', '-png', os.path.join(DEMO, 'demo.pdf'), os.path.join(DEMO, 'p')], check=True)
if not os.path.exists(os.path.join(ORIG, 'p-01.png')):
    os.makedirs(ORIG, exist_ok=True)
    subprocess.run(['pdftoppm', '-r', '300', '-png', os.path.join(KIT, 'original_unzipped', 'Couples_Money_Conversation_Starter.pdf'),
                    os.path.join(ORIG, 'p')], check=True)
demo = lambda n: Image.open(os.path.join(DEMO, f'p-{n:02d}.png')).convert('RGB')
orig = lambda n: Image.open(os.path.join(ORIG, f'p-{n:02d}.png')).convert('RGB')
PAPER = (255, 252, 250)
from openpyxl import load_workbook
_v = load_workbook(EXAMPLE, data_only=True)
VAL = dict(left=_v['Monthly Check-in']['N23'].value, billsA=_v['Joint Bills']['K27'].value, billsB=_v['Joint Bills']['M27'].value,
           pa=_v['Settings']['C17'].value, transA=_v['Joint Bills']['J34'].value, trans=_v['Joint Bills']['H34'].value)
VAL['fifty'] = round(abs(VAL['trans'] / 2 - VAL['transA']))
CARDS_PDF = os.path.join(DEMO, 'cards.pdf')
if not os.path.exists(os.path.join(DEMO, 'c-1.png')):
    subprocess.run(['pdftoppm', '-r', '300', '-png', CARDS_PDF, os.path.join(DEMO, 'c')], check=True)
def cardtop(bottom=None):
    im = cardpg(1); w, h = im.size; m = int(w * 0.045)
    return im.crop((m, int(h * 0.012), w - m, h if bottom is None else int(h * bottom)))


cardpg = lambda n: Image.open(os.path.join(DEMO, f'c-{n}.png')).convert('RGB')


def pdfpage(im, top=0, bottom=None):
    """a PDF page (300 dpi) trimmed of its outer margin, optionally cut to a vertical range (fractions)"""
    w, h = im.size; m = int(w * 0.045)
    b = h if bottom is None else int(h * bottom)
    return im.crop((m, int(h * top) + (m if top == 0 else 0), w - m, b))


def dash_top():
    return crop150(EX(DASH), (20, 20, 880, 560))


def phone_dash():
    """real EXAMPLE dashboard re-flowed for a phone: hero, then KPI cards two per row, then the first chart"""
    pg = EX(DASH); c_ = lambda b: crop150(pg, b)
    gap = Image.new('RGB', (12, 10), SHEETBG)
    rows = [c_((44, 130, 399, 250))]
    for a, b in [((436, 130, 590, 210), (632, 130, 786, 210)), ((436, 208, 590, 290), (632, 208, 786, 290)),
                 ((44, 352, 198, 434), (240, 352, 394, 434)), ((436, 352, 590, 434), (632, 352, 786, 434))]:
        rows.append(hcat([c_(a), Image.new('RGB', (40, 10), SHEETBG), c_(b)]))
    rows.append(c_((44, 446, 399, 640)))
    W_ = max(r.width for r in rows)
    rows = [hcat([Image.new('RGB', ((W_ - r.width) // 2, 10), SHEETBG), r]) for r in rows]
    return pad(stack(rows, gap=16), 0.47)


def phone_week1():
    """real filled Week 1 page of the plan, re-flowed for a phone: timer, cards to pull, agenda, what I heard, agreement"""
    pgw = demo(3); W_ = 940
    def fitw(im):
        return im.resize((W_, round(im.height * W_ / im.width)), Image.LANCZOS)
    parts = [pgw.crop((150, 300, 1500, 560)), pgw.crop((150, 600, 2330, 780)), pgw.crop((1370, 815, 2310, 1500)),
             pgw.crop((150, 815, 1330, 1340)), pgw.crop((150, 1560, 1230, 1840)), pgw.crop((150, 2130, 2330, 2350))]
    return pad(stack([fitw(x) for x in parts], gap=18, bg=PAPER), 0.47, bg=PAPER)


def pills(im, y, labels, f=None, fill=(255, 251, 246), tc=INK, border=GOLD):
    d = ImageDraw.Draw(im); f = f or inter(38, 'SemiBold')
    ws = [tw(d, t, f) + 76 for t in labels]; gap = 30; x = S / 2 - (sum(ws) + gap * (len(ws) - 1)) / 2
    for t, w in zip(labels, ws):
        pill(im, (x, y, x + w, y + 74), t, f, fill=fill, border=border, tc=tc); x += w + gap


def screen_aspect(sc_img, i=0):
    g = screens_of(sc_img)[i]; return (g[2] - g[0]) / (g[3] - g[1])


def phone_on(im, src, xy, scale=0.52):
    """a phone cut from the phone_large scene (real screenshot composited), pasted onto another scene with a shadow"""
    ph = scene('phone_large')
    ph, _ = comp(ph, [(src, 'phone')])
    phone = cut_device(ph, (720, 590, 1330, 1860))
    phone = phone.resize((int(phone.width * scale), int(phone.height * scale)), Image.LANCZOS)
    paste_shadow(im, phone, xy)
    return phone.size


def p01():
    im = scene('laptop_large')
    dt_ = crop150(EX(DASH), (20, 20, 880, 560))
    a = screen_aspect(im)
    shot = Image.new('RGB', (round(dt_.width / 0.93), dt_.height), SHEETBG); shot.paste(dt_, (0, 0))   # phone covers the right 7%: blank page there
    im, _ = comp(im, [(shot, 'tab')])
    cs = cardpg(1); w = cs.width
    col = cs.crop((int(w * 0.045), 255, int(w * 0.5) + 6, 255 + int((w * 0.455 + 6) / 0.462)))   # real crop: left column of the card sheet
    phone_on(im, col, (1530, 960))
    gold_label(im, S / 2, 70, 'THE COMPLETE PREMIUM KIT', f=inter(36, 'Bold'), h=66)
    y = title(im, 'Couples Money Conversation Kit', 'Talk about money without the fight, then plan it together', y=170, hs=112, ss=60)
    pills(im, y + 14, ['20 conversation cards', '4 guided money dates', 'Excel + Google Sheets planner'])
    pill(im, (400, 1760, 1648, 1850), None, inter(40), fill=(255, 251, 246))
    d = ImageDraw.Draw(im)
    center(d, 1779, 'Instant download  ·  Example + blank  ·  Printable PDFs', inter(40, 'SemiBold'), INK)
    footer(im)
    return im


def p02():
    im = background()
    title(im, 'Everything in the Premium Kit', 'Our bestselling cards, plus everything to use them', y=80, hs=110)
    items = [(cardtop(0.62), 'Conversation Cards', 'The original guide + cut-out cards', 'OUR BESTSELLER'),
             (pdfpage(demo(3), 0, 0.62), '4-Week Money Date Plan', 'Fillable PDF, A4 + US Letter', 'NEW'),
             (crop150(EX(DASH), (20, 20, 880, 700)), 'Money Date Planner', 'Excel + Google Sheets, 10 tabs', 'NEW'),
             (pdfpage(demo(8), 0, 0.62), 'Monthly Money Check-in', 'Printable page + planner tab', 'NEW')]
    cw, ch = 860, 690; xs = [124, 1064]; ys = [330, 1070]
    for i, (shot, name, sub, tag) in enumerate(items):
        x0, y0 = xs[i % 2], ys[i // 2]
        card(im, (x0, y0, x0 + cw, y0 + ch), r=36)
        sh_h = 400; sh_w = int(sh_h * shot.width / shot.height)
        if sh_w > cw - 80:
            sh_w = cw - 80; sh_h = int(sh_w * shot.height / shot.width)
        sx = x0 + (cw - sh_w) // 2
        shot_card(im, shot, (sx, y0 + 96, sx + sh_w, y0 + 96 + sh_h), r=14)
        d = ImageDraw.Draw(im)
        number_disc(im, x0 + 70, y0 + 568, i + 1, r=36)
        d.text((x0 + 128, y0 + 528), name, font=pf(50), fill=INK)
        d.text((x0 + 128, y0 + 598), sub, font=pfi(40), fill=GOLD_D)
        tf = inter(28, 'Bold'); w = tw(d, tag, tf) + 40
        pill(im, (x0 + (cw - w) / 2, y0 + 26, x0 + (cw + w) / 2, y0 + 76), tag, tf, fill=GOLD if tag == 'NEW' else INK,
             border=GOLD if tag == 'NEW' else INK, tc=(255, 255, 255), bw=1)
    d = ImageDraw.Draw(im)
    center(d, 1820, '+ README  ·  A4 + US Letter cut-out cards  ·  instant download', inter(38, 'SemiBold'), INK)
    footer(im)
    return im


def p03():
    im = scene('two_tablets_rings')
    im, _ = comp(im, [(pdfpage(orig(7)), 'tab'), (cardtop(), 'tab')])
    y = title(im, '20 Conversation Cards', 'The full guide, plus printable cut-out cards', y=230, hs=118, ss=58)
    pills(im, y + 30, ['Quiz + couple types', '20 cut-out cards', 'Numbered to match the planner'])
    d = ImageDraw.Draw(im)
    center(d, 1800, 'Each money date tells you which cards to pull', pfi(54), GOLD_D)
    footer(im)
    return im


def p04():
    im = scene('tablet_phone_flowers')
    a = screen_aspect(im, 1)
    p3, p4 = pdfpage(demo(3), 0.03), pdfpage(demo(4), 0.03)       # PDF-viewer view: Week 1 page, then the top of Week 2
    gapv = Image.new('RGB', (p3.width, 60), (226, 220, 214))
    ph = stack([p3, gapv, p4]); ph = ph.crop((0, 0, ph.width, round(ph.width / 0.468)))
    im, _ = comp(im, [(pdfpage(demo(5)), 'tab'), (ph, 'phone')])
    y = title(im, '4 Guided Money Dates', 'Twenty minutes each: agenda, cards, timer, agreement', y=60, hs=118, ss=56)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y + 6, 'MONEY STORIES  ·  WHERE IT ALL GOES  ·  SHARED GOALS  ·  OUR MONEY SYSTEM', inter(31, 'SemiBold'), GOLD_D, 4)
    center(d, 1878, 'Fillable PDF: type in the boxes or print it', pfi(46), GOLD_D)
    footer(im)
    return im


def p05():
    im = scene('laptop_large')
    X0, Y0 = 20, 20
    shot = crop150(EX(DASH), (X0, Y0, 880, 560))
    TRANS.clear(); im, _ = comp(im, [(shot, 'tab')])
    tx0, ty0, sc, pl, pt = TRANS[0]
    P_ = lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    title(im, 'Your Money Date Dashboard', 'Nine numbers and five charts, worked out for you', y=70, hs=112, ss=56)
    labs = [(330, 'Left over this month', 'after bills, spending, goals'), (1024, 'Comfort score, 1-10', 'watch it climb date by date'),
            (1718, 'Biggest overspend', 'named for you')]
    boxes = [(44, 131, 399, 292), (241, 353, 394, 435), (631, 353, 786, 435)]
    d = ImageDraw.Draw(im)
    for i, ((cx, a, b), bx) in enumerate(zip(labs, boxes)):
        number_disc(im, cx - 260 if i != 1 else cx - 250, 437, i + 1, r=30)
        gold_label(im, cx, 400, a, b)
        x0, y0 = P_(bx[0], bx[1]); x1, y1 = P_(bx[2], bx[3])
        ImageDraw.Draw(im).rounded_rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), 8, outline=GOLD_D, width=5)
        number_disc(im, x1 - 6, y1 - 6, i + 1, r=20)
    d = ImageDraw.Draw(im)
    center(d, 1760, f'Alex and Jordan\u2019s example: £{VAL["left"]:,.0f} left over in November', pfi(54), GOLD_D)
    footer(im)
    return im


def p06():
    im = background()
    title(im, 'Joint Bills, Split Fairly', 'By income, 50/50 or your own %', y=70, hs=118)
    d = ImageDraw.Draw(im)
    for x, who, pct, amt in [(130, 'ALEX PAYS', f'{VAL["pa"]:.0%}', f'£{VAL["billsA"]:,.0f} a month'), (1064, 'JORDAN PAYS', f'{1 - VAL["pa"]:.0%}', f'£{VAL["billsB"]:,.0f} a month')]:
        card(im, (x, 310, x + 854, 660), r=36)
        d = ImageDraw.Draw(im)
        gold_label(im, x + 427, 340, who, f=inter(42, 'Bold'))
        center(d, 425, pct, pf(130), INK, x + 427)
        center(d, 590, amt, inter(44, 'SemiBold'), (92, 78, 62), x + 427)
    jb = EX(BILLS)
    tbl = stack([crop150(jb, (14, 266, 1320, 590)), crop150(jb, (14, 866, 1320, 904))])
    w = 1788; h = int(w * tbl.height / tbl.width); X = 130
    shot_card(im, tbl, (X, 710, X + w, 710 + h))
    tr = crop150(jb, (14, 936, 1232, 1152))
    y2 = 710 + h + 44; h2 = int(w * tr.height / tr.width)
    shot_card(im, tr, (X, y2, X + w, y2 + h2))
    d = ImageDraw.Draw(im)
    yc = y2 + h2 + 50
    center(d, yc, f'At 50/50, Jordan would pay £{VAL["fifty"]:,} more each month', pfi(56), GOLD_D)
    pills(im, yc + 100, ['By income (fair)', '50/50', 'Our own %', 'Monthly transfer worked out'])
    footer(im)
    return im


def p07():
    im = scene('laptop_large')
    X0, Y0 = 20, 20
    shot = crop150(EX(CHECK), (X0, Y0, 1080, 680))
    TRANS.clear(); im, _ = comp(im, [(shot, 'tab')])
    tx0, ty0, sc, pl, pt = TRANS[0]
    P_ = lambda x, y: (tx0 + ((x - X0) * 2 + pl) * sc, ty0 + ((y - Y0) * 2 + pt) * sc)
    title(im, ['Monthly check-in:', 'see your month in plain words'], None, y=50, hs=104)
    gold_label(im, 1024, 430, 'Written from your own numbers', 'income, bills, spending vs plan, goals', f=inter(40, 'Bold'))
    number_disc(im, 1024 - 400, 467, 1, r=30)
    a0, b0 = P_(50, 230); a1, b1 = P_(504, 489)
    t0 = P_(50, 201)[1]
    ImageDraw.Draw(im).rounded_rectangle((a0 - 16, t0, a1 + 16, b1 + 16), 14, outline=GOLD_D, width=6)
    number_disc(im, a1 + 12, b1 + 12, 1, r=22)
    d = ImageDraw.Draw(im)
    center(d, 1740, 'Plus five questions to answer together, and a printable page', pfi(50), GOLD_D)
    footer(im)
    return im


def p08():
    im = scene('laptop_large')
    a = screen_aspect(im)
    md = crop150(EX(DATES), (20, 20, 1180, 20 + round(1160 / a)))   # real crop at the screen's own shape: fills the screen
    im, _ = comp(im, [(md, 'tab')])
    y = title(im, 'Log Every Money Date', 'Cards pulled, a 1-10 score and one agreement', y=80, hs=118, ss=58)
    d = ImageDraw.Draw(im)
    spaced(d, S / 2, y + 10, 'THE DASHBOARD AND THE CARD TRACKER UPDATE AS YOU TYPE', inter(32, 'SemiBold'), GOLD_D, 4)
    center(d, 1780, 'Every card you log is ticked off on the Conversation Cards tab', pfi(50), GOLD_D)
    footer(im)
    return im


def p09():
    im = scene('two_tablets_rings')
    # the scene's two top-right sparkles sit where step 3's words go: cover them with plain backdrop from just below
    # (same backdrop, no sparkles there), feathered so no edge shows
    patch = im.crop((1725, 480, 1915, 660))
    m = Image.new('L', (190, 180), 0); ImageDraw.Draw(m).rounded_rectangle((10, 10, 180, 170), 40, fill=255)
    from PIL import ImageFilter as _IF
    im.paste(patch, (1725, 300), m.filter(_IF.GaussianBlur(8)))
    im, _ = comp(im, [(pdfpage(orig(4)), 'tab'), (pdfpage(demo(8)), 'tab')])
    title(im, 'How It Works in 3 Steps', None, y=40, hs=108)
    d = ImageDraw.Draw(im)
    steps = [('TAKE THE QUIZ', 'Find your couple type'), ('4 MONEY DATES', 'One 20-minute date a week'), ('CHECK IN MONTHLY', 'Your month in plain words')]
    cxs = [370, 1024, 1678]
    for i, (h, t) in enumerate(steps):
        number_disc(im, cxs[i], 238, i + 1, r=46)
        d = ImageDraw.Draw(im)
        center(d, 304, h, inter(42, 'Bold'), INK, cxs[i])
        center(d, 362, t, inter(36, 'Medium'), (92, 78, 62), cxs[i])
        if i < 2:
            ax0, ax1 = cxs[i] + 80, cxs[i + 1] - 80
            d.line([(ax0, 238), (ax1, 238)], fill=GOLD_D, width=4)
            d.polygon([(ax1, 238), (ax1 - 20, 227), (ax1 - 20, 249)], fill=GOLD_D)
    center(d, 432, 'Every date ends with one thing you both agreed', pfi(46), GOLD_D)
    footer(im)
    return im


def p10():
    im = background()
    y = title(im, '5 Reasons to Buy From Us', 'Why couples choose Way of Wealth Studio', y=80, hs=112)
    rows = [('Made by a qualified financial planner', 'MSc Behavioural Economics, not a template shop'),
            ('Built on our bestselling conversation cards', 'The full Conversation Starter is inside'),
            ('Talk first, numbers second', 'Every date starts with cards, ends with an agreement'),
            ('Works in Excel and Google Sheets', 'Example + blank planner, any currency'),
            ('Real help by email', 'Questions answered by Joel himself')]
    top = y + 50; h = 236; g = 44
    for i, (a, b) in enumerate(rows):
        y0 = top + i * (h + g)
        pill(im, (190, y0, 1858, y0 + h), None, None, r=46)
        tick(im, 300, y0 + h / 2, 44)
        d = ImageDraw.Draw(im)
        d.text((390, y0 + 52), a, font=pf(56), fill=INK)
        d.text((390, y0 + 136), b, font=pfi(44), fill=(140, 104, 58))
    d = ImageDraw.Draw(im)
    center(d, 1885, 'Instant download  ·  Printable PDFs  ·  Excel 2016+ and Google Sheets', inter(30, 'Medium'), (120, 105, 90))
    footer(im, y=1950)
    return im


if __name__ == '__main__':
    which = [int(a) for a in sys.argv[1:]] or range(1, 11)
    for n in which:
        FRINGE.clear()
        save(globals()[f'p{n:02d}'](), os.path.join(P, f'{n:02d}.jpg'))
        print('   screen-edge green-dominant pixels after defringe:', FRINGE or 'no screens')
