"""Shared typesetting + compositing helpers (copied from the 16 Nov SA kit) for the Couples Year in Review rework photos and video.
All text is typeset here with PIL (Playfair Display + Inter). Scenes come from etsy/lib/scenes (no AI calls)."""
import os, sys, subprocess, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
LIB = os.path.join(KIT, '..', 'lib')
sys.path.insert(0, LIB)
import nb  # noqa: E402

SCENES = os.path.join(LIB, 'scenes')
WORK = os.environ.get('YR_WORK', '/tmp/claude-0/-home-claude-wayofwealthstudio-website/f46713d3-e66a-5160-9439-2a092bf5b893/scratchpad/work')
OUTX = os.path.join(KIT, 'out')
EXAMPLE = os.path.join(OUTX, 'Couples Money Year in Review 2027 - EXAMPLE (filled in).xlsx')
BLANKF = os.path.join(OUTX, 'Couples Money Year in Review 2027 - BLANK (start here).xlsx')
PDFA4 = os.path.join(OUTX, 'Couples Money Year in Review and 2027 Goals - printable A4.pdf')
README = os.path.join(OUTX, 'README.pdf')

F = '/home/claude/fonts/'
IN = '/usr/share/fonts/opentype/inter/'
INK = (42, 38, 32)        # #2A2620
GOLD = (184, 149, 110)    # #B8956E
GOLD_D = (160, 122, 74)   # darker gold for small text on cream
CREAM = (253, 247, 240)
SHEETBG = (246, 241, 234)
S = 2048                  # working canvas (scenes are 2048), saved at 2000


def pf(s): return ImageFont.truetype(F + 'PF-700-normal.ttf', s)
def pfi(s): return ImageFont.truetype(F + 'PF-400-italic.ttf', s)
def pfr(s): return ImageFont.truetype(F + 'PF-400-normal.ttf', s)
def inter(s, w='Medium'): return ImageFont.truetype(IN + f'Inter-{w}.otf', s)


# ---------------------------------------------------------------- product renders
def render_pages(xlsx, name, dpi=300):
    """xlsx -> pdf -> one PNG per page in WORK/name/p-XX.png (LibreOffice recalculates formulas)."""
    d = os.path.join(WORK, name); os.makedirs(d, exist_ok=True)
    if not glob.glob(d + '/p-*.png'):
        src = os.path.join(d, name + '.xlsx'); subprocess.run(['cp', xlsx, src], check=True)
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', d, src], check=True, capture_output=True)
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', src[:-5] + '.pdf', d + '/p'], check=True, capture_output=True)
    return d


_pc = {}
def page(name, n):
    k = (name, n)
    if k not in _pc:
        _pc[k] = Image.open(os.path.join(WORK, name, f'p-{n:02d}.png')).convert('RGB')
    return _pc[k]


def crop150(im, box):
    """crop with box given in 150-dpi coordinates on a 300-dpi page"""
    return im.crop(tuple(2 * v for v in box))


def pad(im, aspect, bg=SHEETBG, align='top'):
    w, h = im.size
    if w / h > aspect:
        H = int(round(w / aspect)); c = Image.new('RGB', (w, H), bg); c.paste(im, (0, 0 if align == 'top' else (H - h) // 2)); return c
    W = int(round(h * aspect)); c = Image.new('RGB', (W, h), bg); c.paste(im, ((W - w) // 2, 0)); return c


def stack(parts, gap=0, bg=SHEETBG):
    W = max(p.width for p in parts); H = sum(p.height for p in parts) + gap * (len(parts) - 1)
    c = Image.new('RGB', (W, H), bg); y = 0
    for p in parts: c.paste(p, (0, y)); y += p.height + gap
    return c


def hcat(parts, bg=SHEETBG):
    W = sum(p.width for p in parts); H = max(p.height for p in parts); c = Image.new('RGB', (W, H), bg); x = 0
    for p in parts: c.paste(p, (x, 0)); x += p.width
    return c


# ---------------------------------------------------------------- scenes + compositing
def scene(name): return Image.open(os.path.join(SCENES, name + '.jpg')).convert('RGB')


def screens_of(img):
    return sorted(nb.screens(img), key=lambda g: g[0])


def comp(img, assign):
    """paste real screenshots into the green screens (left to right). Returns (image, list of screen boxes)."""
    gs = screens_of(img)
    assert len(gs) == len(assign), (len(gs), len(assign))
    boxes, bands = [], []
    for (x0, y0, x1, y1, mask), (src, kind) in zip(gs, assign):
        w, h = x1 - x0, y1 - y0
        # page padding so nothing touches the bezel: ~14 px left and ~8 px top at output size, then pad (never crop)
        # to the screen's shape
        sh_ = h - int(h * .075) if kind == 'phone' else h
        pl, pt = round(14 * src.width / w), round(8 * src.width / w)
        p = Image.new('RGB', (src.width + pl, src.height + pt), SHEETBG); p.paste(src, (pl, pt))
        p = pad(p, w / sh_)
        TRANS.append((x0, y0 + (h - sh_), w / p.width, pl, pt))
        shot = nb.phone_shot(p, w, h) if kind == 'phone' else nb.fit(p, w, h)
        m = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype('uint8')).filter(ImageFilter.MaxFilter(9))
        a = np.pad(np.array(m) > 0, 10); a = ndimage.binary_closing(a, iterations=6); a = ndimage.binary_fill_holes(a)[10:-10, 10:-10]
        img.paste(shot, (x0, y0), Image.fromarray((a * 255).astype('uint8')))
        boxes.append((x0, y0, x1, y1))
        full = np.zeros((img.height, img.width), bool); full[y0:y1, x0:x1] = a
        bands.append(ndimage.binary_dilation(full, iterations=7) & ~ndimage.binary_erosion(full, iterations=3))
    despill(img, boxes)
    for band in bands:
        defringe_band(img, band)
    FRINGE.append(max([fringe_count(img, b) for b in bands] + [0]))
    return img, boxes


FRINGE = []
TRANS = []   # per pasted screen: (screen x0, content y0, scale, left pad, top pad) in source px


def defringe_band(img, band, tol=3):
    """screen-edge band: any green-dominant pixel gets G pulled down to max(R, B) (kills the dark-green rim)"""
    a = np.array(img).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = band & (g > np.maximum(r, b) + tol)
    a[..., 1] = np.where(m, np.maximum(r, b), g)
    img.paste(Image.fromarray(a.clip(0, 255).astype('uint8')))


def fringe_count(img, band, tol=8):
    a = np.array(img).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int((band & (g > np.maximum(r, b) + tol)).sum())


def despill(img, boxes, e=14):
    a = np.array(img).astype(int)
    for (x0, y0, x1, y1) in boxes:
        X0, Y0, X1, Y1 = max(0, x0 - e), max(0, y0 - e), min(img.width, x1 + e), min(img.height, y1 + e)
        b = a[Y0:Y1, X0:X1]; r, g, bl = b[..., 0], b[..., 1], b[..., 2]
        m = (g > 90) & (g > np.maximum(r, bl) + 25)
        b[..., 1] = np.where(m, np.maximum(r, bl), g)
    img.paste(Image.fromarray(a.clip(0, 255).astype('uint8')))


def green_count(img):
    a = np.array(img).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    pure = int(((g > 200) & (r < 90) & (b < 90)).sum())
    near = int(((g > 150) & (g - r > 70) & (g - b > 70)).sum())
    return pure, near


def cut_device(img, box, dark=95):
    """cut a device (dark bezel) out of a scene: returns RGBA crop of box."""
    x0, y0, x1, y1 = box
    c = img.crop(box); a = np.array(c).astype(int)
    g = (a[..., 1] > 150) & (a[..., 1] - a[..., 0] > 70)
    d = (a.max(2) < dark) | g
    d = ndimage.binary_closing(d, iterations=3); d = ndimage.binary_fill_holes(d)
    lab, n = ndimage.label(d); sizes = ndimage.sum(d, lab, range(1, n + 1)); d = lab == (1 + int(np.argmax(sizes)))
    d = ndimage.binary_dilation(d, iterations=4)  # take the silver rim
    m = Image.fromarray((d * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
    c = c.convert('RGBA'); c.putalpha(m); return c


def paste_shadow(base, rgba, xy, blur=28, off=(0, 22), alpha=95):
    sh = Image.new('L', base.size, 0)
    a = rgba.split()[3]
    sh.paste(a.point(lambda v: v * alpha // 255), (xy[0] + off[0], xy[1] + off[1]))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.paste((120, 90, 55), (0, 0), sh)
    base.paste(rgba, xy, rgba)


# ---------------------------------------------------------------- generated background (matches scenes)
def background(seed=1, sparkles=True):
    yy, xx = np.mgrid[0:S, 0:S] / S
    base = np.array([253, 242, 234], float)
    warm = np.array([238, 214, 189], float)
    t = np.clip(np.exp(-((1 - xx) ** 2 + yy ** 2) / 0.10) * 0.9 + np.exp(-(xx ** 2 + (1 - yy) ** 2) / 0.07) * 0.6, 0, 1)
    light = np.clip(1 - np.abs((xx * 0.8 + yy) - 0.55) / 0.18, 0, 1) * 0.35  # soft diagonal light band
    a = base * (1 - t[..., None]) + warm * t[..., None]
    a = a + (np.array([255, 251, 246]) - a) * light[..., None]
    im = Image.fromarray(a.clip(0, 255).astype('uint8'))
    if sparkles:
        for (x, y, r) in [(92, 300, 42), (140, 395, 18), (1958, 290, 40), (1905, 380, 18), (92, 1720, 34), (150, 1800, 16),
                          (1958, 1700, 40), (1900, 1790, 18)]:
            sparkle(im, x, y, r)
    return im


def sparkle(im, cx, cy, r, col=(205, 165, 100)):
    k = 4; R = r * k
    t = np.linspace(0, 2 * np.pi, 200)
    c, s = np.cos(t), np.sin(t)
    p = 3.0
    xs = R * np.sign(c) * np.abs(c) ** p; ys = R * np.sign(s) * np.abs(s) ** p
    L = Image.new('L', (2 * R + 8, 2 * R + 8), 0)
    ImageDraw.Draw(L).polygon(list(zip(xs + R + 4, ys + R + 4)), fill=255)
    L = L.resize((L.width // k, L.height // k), Image.LANCZOS)
    glow = L.filter(ImageFilter.GaussianBlur(r / 3)).point(lambda v: v // 3)
    x0, y0 = int(cx - L.width / 2), int(cy - L.height / 2)
    im.paste((255, 236, 200), (x0, y0), glow)
    # vertical gold gradient
    g = Image.new('RGB', L.size)
    gd = ImageDraw.Draw(g)
    for y in range(L.height):
        f = y / max(1, L.height - 1)
        gd.line([(0, y), (L.width, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip((232, 200, 140), (184, 140, 78))))
    im.paste(g, (x0, y0), L)


# ---------------------------------------------------------------- text
def tw(d, t, f): return d.textlength(t, font=f)


def center(d, y, t, f, fill, cx=S / 2):
    d.text((cx - tw(d, t, f) / 2, y), t, font=f, fill=fill)


def spaced(d, cx, y, t, f, fill, sp):
    w = sum(tw(d, ch, f) for ch in t) + sp * (len(t) - 1); x = cx - w / 2
    for ch in t:
        d.text((x, y), ch, font=f, fill=fill); x += tw(d, ch, f) + sp
    return w


def title(im, head, sub=None, y=70, hs=118, ss=66, gap=26, lines=None):
    d = ImageDraw.Draw(im)
    heads = head if isinstance(head, list) else [head]
    for h in heads:
        f = pf(hs)
        while tw(d, h, f) > S - 200: hs -= 4; f = pf(hs)
        center(d, y, h, f, INK); y += int(hs * 1.18)
    if sub:
        y += gap - 14
        center(d, y, sub, pfi(ss), GOLD_D); y += int(ss * 1.35)
    return y


def footer(im, y=1952):
    d = ImageDraw.Draw(im); f = pfr(34)
    w = spaced(d, S / 2, y, 'WAY OF WEALTH STUDIO', f, GOLD_D, 9)
    for sx in (S / 2 - w / 2 - 44, S / 2 + w / 2 + 44):
        sparkle(im, sx, y + 22, 17)


def pill(im, box, text, f, fill=(255, 251, 246), border=GOLD, tc=INK, r=None, shadow=True, bw=3):
    x0, y0, x1, y1 = box; r = r or (y1 - y0) // 2
    if shadow:
        sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, x1, y1 + 10), r, fill=70)
        im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im); d.rounded_rectangle(box, r, fill=fill, outline=border, width=bw)
    if text:
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((x0 + x1) / 2 - (bb[2] + bb[0]) / 2, (y0 + y1) / 2 - (bb[3] + bb[1]) / 2), text, font=f, fill=tc)


def card(im, box, r=28, fill=(255, 251, 246), border=GOLD, bw=3, shadow=70):
    x0, y0, x1, y1 = box
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 14, x1, y1 + 14), r, fill=shadow)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(im).rounded_rectangle(box, r, fill=fill, outline=border, width=bw)


def shot_card(im, shot, box, r=22, border=(214, 196, 168)):
    """real screenshot on a white card with shadow (fit to box width)"""
    x0, y0, x1, y1 = box
    s = nb.fit(shot, x1 - x0, y1 - y0)
    card(im, (x0 - 3, y0 - 3, x1 + 3, y1 + 3), r, fill=(255, 255, 255), border=border, bw=3)
    m = Image.new('L', s.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s.width - 1, s.height - 1), r - 3, fill=255)
    im.paste(s, (x0, y0), m)


def gold_label(im, cx, y, text, sub=None, f=None, sf=None, padx=34, h=74):
    """gold filled pill with white text, optional ink line(s) underneath. returns bbox of pill"""
    d = ImageDraw.Draw(im); f = f or inter(40, 'Bold'); sf = sf or inter(34, 'Medium')
    w = tw(d, text, f) + 2 * padx; box = (cx - w / 2, y, cx + w / 2, y + h)
    pill(im, box, text, f, fill=GOLD, border=GOLD, tc=(255, 255, 255), shadow=True, bw=1)
    if sub:
        yy = y + h + 12
        for ln in sub.split('\n'):
            center(d, yy, ln, sf, INK, cx); yy += int(sf.size * 1.25)
    return box


def leader(im, pts, col=GOLD_D, w=5):
    d = ImageDraw.Draw(im); d.line(pts, fill=col, width=w, joint='curve')
    ex, ey = pts[-1]; d.ellipse((ex - 13, ey - 13, ex + 13, ey + 13), fill=(255, 255, 255), outline=col, width=6)


def number_disc(im, cx, cy, n, r=50):
    d = ImageDraw.Draw(im)
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).ellipse((cx - r, cy - r + 8, cx + r, cy + r + 8), fill=80)
    im.paste((150, 115, 70), (0, 0), sh.filter(ImageFilter.GaussianBlur(10)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD, outline=(255, 248, 235), width=4)
    f = pf(int(r * 1.15)); t = str(n); bb = d.textbbox((0, 0), t, font=f)
    d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), t, font=f, fill=(255, 255, 255))


def tick(im, cx, cy, r=34):
    d = ImageDraw.Draw(im)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=GOLD_D, width=5)
    d.line([(cx - r * .45, cy + r * .02), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .4)], fill=GOLD_D, width=7, joint='curve')


def save(im, path):
    out = im.resize((2000, 2000), Image.LANCZOS)
    out.save(path, quality=90)
    p, n = green_count(out)
    print(os.path.basename(path), 'pure green', p, 'near green', n)
    return p, n


def render_variant(xlsx, name, edits, pages, dpi=300):
    """copy of a product file with some cells changed (openpyxl), recalculated + rendered by LibreOffice.
    edits: [(sheet, cell, value)]. Returns {page: png path}. Charts are dropped by openpyxl: crop above them."""
    from openpyxl import load_workbook
    d = os.path.join(WORK, name); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, name + '.xlsx'); out = {p: f'{d}/p-{p:02d}.png' for p in pages}
    if all(os.path.exists(v) for v in out.values()): return out
    wb = load_workbook(xlsx)
    for sh, cell, v in edits: wb[sh][cell].value = v
    wb.save(f)
    R = glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
    subprocess.run(['python3', R, f, '90'], check=True, capture_output=True)
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', d, f], check=True, capture_output=True)
    for p in pages:
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-singlefile', '-f', str(p), '-l', str(p), f[:-5] + '.pdf', out[p][:-4]], check=True)
    return out




def scene_nokeys():
    """laptop_phone scene with the house-keys prop (from the moving-in set) painted out: the floor in that corner is
    modelled by a smooth quadratic fitted to clean floor pixels, and the key pixels are replaced by it (feathered)"""
    im = scene('laptop_phone'); a = np.array(im).astype(float)
    X0, Y0, X1, Y1 = 1790, 1480, 2048, 1800
    sub = a[Y0:Y1, X0:X1]
    yy, xx = np.mgrid[0:Y1 - Y0, 0:X1 - X0] / 300.0
    X, Y = xx * 300 + X0, yy * 300 + Y0
    pot = (X > 1906 + (Y - 1380) * 0.1) & (Y < 1579)
    A = np.stack([np.ones_like(xx), xx, yy, xx * xx, xx * yy, yy * yy, xx ** 3, xx * xx * yy, xx * yy * yy, yy ** 3], -1)
    def fit(ok):
        return np.stack([A @ np.linalg.lstsq(A[ok], sub[..., c][ok], rcond=None)[0] for c in range(3)], -1)
    ok = (sub.min(2) > 215) & ((sub[..., 0] - sub[..., 2]) < 30) & ~pot
    floor = fit(ok)
    m = (np.abs(sub - floor).sum(2) > 16) & ~pot
    m = ndimage.binary_dilation(m, iterations=6) & ~pot
    m[:, :14] = False
    floor = fit(~m & ~pot)
    f = ndimage.gaussian_filter(m.astype(float), 3)[..., None]
    f[pot] = 0
    sub = sub * (1 - f) + floor * f
    a[Y0:Y1, X0:X1] = sub
    return Image.fromarray(a.clip(0, 255).astype('uint8'))


def clean_keys(im, box=(430, 1505, 1625, 1592)):
    """paint out the garbled AI key legends on the laptop_large keyboard: light marks fully enclosed by a dark key
    (holes in the dark-key mask) are filled with that key's own dark colour. Key shapes and gaps stay."""
    x0, y0, x1, y1 = box
    a = np.array(im).astype(int); sub = a[y0:y1, x0:x1]
    lum = sub.mean(2)
    dark = lum < 110
    filled = ndimage.binary_fill_holes(dark)
    holes = filled & ~dark
    holes = ndimage.binary_dilation(holes, iterations=2) & filled
    closed = ndimage.binary_fill_holes(ndimage.binary_closing(dark, iterations=3))
    holes = holes | (closed & ~dark & (lum < 200))
    keyc = np.array([np.median(sub[..., c][dark]) for c in range(3)])
    sub[holes] = keyc
    a[y0:y1, x0:x1] = sub
    return Image.fromarray(a.clip(0, 255).astype('uint8'))
