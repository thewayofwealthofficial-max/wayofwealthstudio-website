import subprocess, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('hi', exist_ok=True); os.makedirs('photos', exist_ok=True)
if not os.path.exists('hi/s-01.png'):
    subprocess.run(['pdftoppm', '-r', '170', '-png', 'out/A4-sample.pdf', 'hi/s'], check=True)
P = lambda n: Image.open(f'hi/s-{n:02d}.png').convert('RGB')
FD = '/usr/share/fonts/truetype/'
F = lambda f, s: ImageFont.truetype(FD + f, s)
SERB = 'crosextra/Caladea-Bold.ttf'; SB = 'google-fonts/Poppins-Bold.ttf'; SM = 'google-fonts/Poppins-Medium.ttf'; SR = 'google-fonts/Poppins-Regular.ttf'
CREAM = (245, 240, 232); SAGE = (184, 197, 176); DSAGE = (143, 165, 133); GOLD = (184, 149, 110); CHAR = (61, 61, 61); WHITE = (255, 255, 255)
S = 2000


def canvas(bg=CREAM):
    return Image.new('RGB', (S, S), bg)


def linen(base=(236, 228, 214)):
    random.seed(3)
    im = Image.new('RGB', (S, S), base)
    px = im.load()
    for y in range(0, S, 2):
        for x in range(0, S, 2):
            d = random.randint(-6, 6)
            c = tuple(max(0, min(255, v + d)) for v in base)
            px[x, y] = c
    return im.filter(ImageFilter.GaussianBlur(1.2))


def paper(img, w, angle=0, shadow=True):
    r = w / img.width
    im = img.resize((w, int(img.height * r)), Image.LANCZOS)
    pad = 40
    layer = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([pad + 6, pad + 10, pad + im.width + 6, pad + im.height + 10], fill=(80, 60, 40, 55))
        layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(14)))
    layer.paste(im, (pad, pad))
    return layer.rotate(angle, resample=Image.BICUBIC, expand=True)


def head(d, text, y, size=96, color=CHAR, font=SERB, w=S - 200):
    f = F(font, size)
    lines, cur = [], ''
    for word in text.split():
        t = (cur + ' ' + word).strip()
        if d.textlength(t, font=f) > w and cur:
            lines.append(cur); cur = word
        else:
            cur = t
    lines.append(cur)
    for ln in lines:
        d.text((S / 2, y), ln, font=f, fill=color, anchor='ma'); y += int(size * 1.15)
    return y


def pill(d, text, cx, y, size=44, bg=DSAGE, fg=WHITE):
    f = F(SM, size); tw = d.textlength(text, font=f)
    d.rounded_rectangle([cx - tw / 2 - 40, y, cx + tw / 2 + 40, y + size + 40], radius=(size + 40) // 2, fill=bg)
    d.text((cx, y + 20), text, font=f, fill=fg, anchor='ma')


def crop_zoom(n, box, w):
    im = P(n); W, H = im.size
    c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    return c.resize((w, int(c.height * w / c.width)), Image.LANCZOS)


def framed(im, base, x, y, border=6):
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([x - border, y - border, x + im.width + border, y + im.height + border], radius=18, fill=(225, 216, 200))
    base.paste(im, (x, y))


# 1 hero: printed pages on a linen table
im = Image.open('dl/bg.png').convert('RGB').resize((S, S), Image.LANCZOS).convert('RGBA')
im.alpha_composite(paper(P(9), 640, 0), (1060, 330))
im.alpha_composite(paper(P(1), 720, -2.5), (200, 300))
im = im.convert('RGB'); d = ImageDraw.Draw(im)
d.rectangle([0, 1540, S, S], fill=CREAM)
y = head(d, 'Premarital Money Talks Workbook', 1590, 104)
d.text((S / 2, y + 14), '6 money talks before you marry  ·  fillable + printable', font=F(SM, 50), fill=DSAGE, anchor='ma')
im.save('photos/01.jpg', quality=90)

# 2 what's inside: all 18 pages
im = canvas(); d = ImageDraw.Draw(im)
y = head(d, "What's inside", 70, 110)
d.text((S / 2, y + 5), '18 pages  ·  6 talks  ·  one page per step', font=F(SM, 54), fill=DSAGE, anchor='ma')
tw, gap = 290, 30; th = int(tw * 1.414)
x0 = (S - (6 * tw + 5 * gap)) // 2; y0 = 370
for i in range(18):
    t = P(i + 1).resize((tw, th), Image.LANCZOS)
    framed(t, im, x0 + (i % 6) * (tw + gap), y0 + (i // 6) * (th + 60), 4)
im.save('photos/02.jpg', quality=90)


def zoom_slide(fn, n, box, title, sub, badge=None):
    im = canvas(); d = ImageDraw.Draw(im)
    y = head(d, title, 70, 100)
    d.text((S / 2, y + 5), sub, font=F(SM, 50), fill=DSAGE, anchor='ma')
    top = y + 110
    z = crop_zoom(n, box, 1720)
    avail = S - top - (190 if badge else 70)
    if z.height > avail:
        z = z.resize((int(z.width * avail / z.height), avail), Image.LANCZOS)
    framed(z, im, (S - z.width) // 2, top, 8)
    if badge:
        pill(d, badge, S / 2, S - 150, 44, GOLD)
    im.save(f'photos/{fn}.jpg', quality=90)


zoom_slide('03', 9, (0, 0.04, 1, 0.66), 'Split bills fairly', '50/50 or by income, with the sums shown step by step')
zoom_slide('04', 6, (0, 0.04, 1, 0.652), 'No hidden debt', 'Income, savings and everything you each owe, in one place')
zoom_slide('05', 13, (0, 0.04, 1, 0.83), 'Finish with a Money Agreement', 'One page you both sign, plus monthly money dates')

# 6 tablet: type on any device
im = linen((228, 233, 224)); d = ImageDraw.Draw(im)
y = head(d, 'Type on any device or print it', 70, 100)
tx, ty, tw = 150, 330, 1700
page = P(4); page = page.crop((0, 0, page.width, int(page.height * 0.60))); th = int(page.height * (tw - 80) / page.width)
d.rounded_rectangle([tx, ty, tx + tw, ty + th + 80], radius=70, fill=(40, 40, 42))
im.paste(page.resize((tw - 80, th), Image.LANCZOS), (tx + 40, ty + 40))
pill(d, 'Works in Adobe Reader, Preview, Chrome and the iPhone Files app', S / 2, 1840, 40, CHAR)
im = im.crop((0, 0, S, S)); im.save('photos/06.jpg', quality=90)


def infographic(fn, title, items, bg=CREAM, card=WHITE):
    im = canvas(bg); d = ImageDraw.Draw(im)
    y = head(d, title, 90, 104)
    y += 40
    for i, (t, s) in enumerate(items):
        d.rounded_rectangle([140, y, S - 140, y + 270], radius=36, fill=card)
        d.ellipse([190, y + 75, 310, y + 195], fill=GOLD)
        d.text((250, y + 135), str(i + 1), font=F(SB, 64), fill=WHITE, anchor='mm')
        d.text((370, y + 52), t, font=F(SB, 58), fill=CHAR)
        d.text((370, y + 140), s, font=F(SR, 44), fill=(90, 88, 84))
        y += 300
    im.save(f'photos/{fn}.jpg', quality=90)


infographic('07', '5 highlights of this workbook', [
    ('Money is the whole book', 'Not one page in a general workbook'),
    ('A4 and US Letter', 'Any currency, no dollar or pound signs'),
    ('Short and plain', 'One page per step, 30 to 45 min a talk'),
    ('Clear how-to page', 'Type it on screen or print it out'),
    ('Ends in a plan', 'A signed Money Agreement + money dates')])
infographic('08', '5 reasons to buy from us', [
    ('Made by a money expert', 'Joel, MSc Behavioural Economics'),
    ('Couples are our specialty', 'A whole range of tools made for two'),
    ('Instant download', 'Fillable and print files, start tonight'),
    ('Real help if you need it', 'Email Joel with any question'),
    ('What you see is what you get', 'Real previews of the actual pages')], SAGE, CREAM)

zoom_slide('09', 16, (0.045, 0.126, 0.505, 0.436), 'Also inside: 20 quick questions', '5 of the 20. For a road trip, a walk or a dinner out')
print(sorted(os.listdir('photos')))
