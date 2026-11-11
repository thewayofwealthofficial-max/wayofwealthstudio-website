import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'))
os.makedirs('photos', exist_ok=True)
FD = '/usr/share/fonts/truetype/'
F = lambda f, s: ImageFont.truetype(FD + f, s)
SERB = 'crosextra/Caladea-Bold.ttf'; SB = 'google-fonts/Poppins-Bold.ttf'; SM = 'google-fonts/Poppins-Medium.ttf'; SR = 'google-fonts/Poppins-Regular.ttf'
CREAM = (245, 240, 232); SAGE = (184, 197, 176); DSAGE = (143, 165, 133); GOLD = (184, 149, 110); CHAR = (61, 61, 61); WHITE = (255, 255, 255)
S = 2000
X = lambda n: Image.open(f'hi/c-{n:02d}.png').convert('RGB')      # spreadsheet tabs (cropped renders)
P = lambda n: Image.open(f'hi/p-{n:02d}.png').convert('RGB')      # printable pages
TAB = {'dash': 1, 'start': 2, 'settings': 3, 'numbers': 4, 'spend': 5, 'nw': 6, 'review': 7, 'goals': 8, 'ci': 9, 'date': 10}


def canvas(bg=CREAM):
    return Image.new('RGB', (S, S), bg)


def head(d, text, y, size=96, color=CHAR, font=SERB, w=S - 200):
    f = F(font, size); lines, cur = [], ''
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


def shadowed(img, angle=0, blur=16, off=(8, 12), alpha=60):
    pad = 50
    layer = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad + off[0], pad + off[1], pad + img.width + off[0], pad + img.height + off[1]], fill=(60, 45, 30, alpha))
    layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(blur)))
    layer.paste(img.convert('RGBA'), (pad, pad))
    return layer.rotate(angle, resample=Image.BICUBIC, expand=True)


def laptop(screen, w):
    """Simple laptop drawn around a real screenshot."""
    sw = w - 70
    sc = screen.resize((sw, int(screen.height * sw / screen.width)), Image.LANCZOS)
    sh_ = int(sw * 0.64)
    sc = sc.crop((0, 0, sw, min(sh_, sc.height)))
    lid_h = sh_ + 70
    im = Image.new('RGBA', (int(w * 1.16), lid_h + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0 = int(w * 0.08)
    d.rounded_rectangle([x0, 0, x0 + w, lid_h], radius=28, fill=(38, 38, 40))
    im.paste(sc, (x0 + 35, 35))
    d.rounded_rectangle([0, lid_h - 4, im.width, lid_h + 30], radius=14, fill=(200, 200, 204))
    d.rounded_rectangle([im.width / 2 - 110, lid_h - 4, im.width / 2 + 110, lid_h + 10], radius=6, fill=(170, 170, 175))
    return im


def zoom(n, box, w):
    im = X(n); W, H = im.size
    c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    return c.resize((w, int(c.height * w / c.width)), Image.LANCZOS)


def framed(im, base, x, y, border=8):
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([x - border, y - border, x + im.width + border, y + im.height + border], radius=18, fill=(225, 216, 200))
    base.paste(im, (x, y))


# 1 hero: laptop with the real dashboard + a printed page on a desk
bg = Image.open('../desk_bg_ai.png').convert('RGB').resize((S, S), Image.LANCZOS).convert('RGBA')
dash = X(TAB['dash'])
dash = dash.crop((0, 0, dash.width, int(dash.height * 0.62)))
lap = laptop(dash, 1360)
bg.alpha_composite(shadowed(P(8).resize((560, int(560 * 1.414))), -6), (60, 560))
bg.alpha_composite(lap, (440, 300))
im = bg.convert('RGB'); d = ImageDraw.Draw(im)
d.rectangle([0, 1470, S, S], fill=CREAM)
y = head(d, 'Couples Money Year in Review', 1515, 104)
d.text((S / 2, y + 2), '+ next year\'s goals with monthly check-ins', font=F(SM, 54), fill=DSAGE, anchor='ma')
xs = [S / 2 - 560, S / 2, S / 2 + 560]
for x, t in zip(xs, ['Google Sheets + Excel', 'Printable A4 + US Letter', 'Any currency']):
    pill(d, t, x, 1760, 40, GOLD if t.startswith('Google') else DSAGE)
im.save('photos/01.jpg', quality=90)

# 2 what's inside
im = canvas(); d = ImageDraw.Draw(im)
y = head(d, "What's inside", 70, 110)
d.text((S / 2, y + 5), '10-tab spreadsheet  +  11 printable pages', font=F(SM, 54), fill=DSAGE, anchor='ma')
tabs = [('Dashboard', 'dash'), ('1 Year in numbers', 'numbers'), ('2 Spending review', 'spend'),
        ('4 Looking back', 'review'), ('5 Goals', 'goals'), ('6 Monthly check-ins', 'ci')]
tw, th = 580, 400; gap = 40; x0 = (S - (3 * tw + 2 * gap)) // 2; y0 = 330
for i, (lab, k) in enumerate(tabs):
    src = X(TAB[k]); cw = int(src.width * 0.62); chh = int(cw * th / tw)
    if chh > src.height:
        chh = src.height; cw = int(chh * tw / th)
    t = src.crop((0, 0, cw, chh)).resize((tw, th), Image.LANCZOS)
    x = x0 + (i % 3) * (tw + gap); yy = y0 + (i // 3) * (th + 95)
    framed(t, im, x, yy, 5)
    d.text((x + tw / 2, yy + th + 18), lab, font=F(SM, 38), fill=CHAR, anchor='ma')
d.text((S / 2, 1305), '+ Settings, Net worth, Money date agenda and Start here tabs', font=F(SR, 36), fill=(90, 88, 84), anchor='ma')
pw, ph = 270, int(270 * 1.414); gap = 24
x0 = (S - (6 * pw + 5 * gap)) // 2; yy = 1385
for i, n in enumerate([1, 3, 4, 8, 9, 10]):
    framed(P(n).resize((pw, ph), Image.LANCZOS), im, x0 + i * (pw + gap), yy, 4)
d.text((S / 2, yy + ph + 30), 'Printable pages: the same six steps on paper', font=F(SM, 40), fill=CHAR, anchor='ma')
im.save('photos/02.jpg', quality=90)


def zoom_slide(fn, n, box, title, sub, badge=None):
    im = canvas(); d = ImageDraw.Draw(im)
    y = head(d, title, 70, 100)
    d.text((S / 2, y + 5), sub, font=F(SM, 50), fill=DSAGE, anchor='ma')
    top = y + 110
    z = zoom(n, box, 1800)
    avail = S - top - (190 if badge else 80)
    if z.height > avail:
        z = z.resize((int(z.width * avail / z.height), avail), Image.LANCZOS)
    framed(z, im, (S - z.width) // 2, top, 8)
    if badge:
        pill(d, badge, S / 2, S - 150, 44, GOLD)
    im.save(f'photos/{fn}.jpg', quality=90)


zoom_slide('03', TAB['dash'], (0, 0, 1, 1), 'Your whole year on one page', '8 headline numbers, charts and goal progress',
           'Fills in by itself as you type')
zoom_slide('04', TAB['spend'], (0, 0.165, 0.66, 0.82), 'Was it worth it? Decide together', 'Protect what matters, then choose what to cut')
zoom_slide('05', TAB['goals'], (0, 0.165, 0.6, 0.655), 'Goals that actually fit', 'Monthly amount worked out, plus a reality check',
           'Checks your goals against last year')
im = canvas(); d = ImageDraw.Draw(im)
y = head(d, 'Check in every month', 70, 100)
d.text((S / 2, y + 5), 'Log each goal, see On track or Behind at a glance', font=F(SM, 50), fill=DSAGE, anchor='ma')
top = y + 105
z1 = zoom(TAB['ci'], (0, 0.158, 0.555, 0.47), 1600)
framed(z1, im, (S - z1.width) // 2, top, 8)
z2 = zoom(TAB['ci'], (0, 0.49, 0.80, 0.79), 1840)
framed(z2, im, (S - z2.width) // 2, top + z1.height + 40, 8)
print('p6 bottom', top + z1.height + 40 + z2.height)
pill(d, 'Status updates itself after each money date', S / 2, 1560, 44, GOLD)
im.save('photos/06.jpg', quality=90)

# 7 printable on the desk
bg = Image.open('../desk_bg_ai.png').convert('RGB').resize((S, S), Image.LANCZOS).convert('RGBA')
bg.alpha_composite(shadowed(P(6).resize((760, int(760 * 1.414))), 3), (180, 260))
bg.alpha_composite(shadowed(P(10).resize((760, int(760 * 1.414))), -2), (1000, 300))
im = bg.convert('RGB'); d = ImageDraw.Draw(im)
d.rectangle([0, 0, S, 230], fill=CREAM)
head(d, 'Prefer paper? Print it', 50, 100)
d.text((S / 2, 165), 'A4 and US Letter, write by hand', font=F(SM, 46), fill=DSAGE, anchor='ma')
im.save('photos/07.jpg', quality=90)


def infographic(fn, title, items, bg=CREAM, card=WHITE):
    im = canvas(bg); d = ImageDraw.Draw(im)
    y = head(d, title, 90, 104); y += 40
    for i, (t, s) in enumerate(items):
        d.rounded_rectangle([140, y, S - 140, y + 270], radius=36, fill=card)
        d.ellipse([190, y + 75, 310, y + 195], fill=GOLD)
        d.text((250, y + 135), str(i + 1), font=F(SB, 64), fill=WHITE, anchor='mm')
        d.text((370, y + 52), t, font=F(SB, 56), fill=CHAR)
        d.text((370, y + 140), s, font=F(SR, 42), fill=(90, 88, 84))
        y += 300
    im.save(f'photos/{fn}.jpg', quality=90)


infographic('08', '5 highlights of this planner', [
    ('Your own file, not a web app', 'Google Sheets or Excel, no subscription'),
    ('The whole year, month by month', 'All 12 months, not one sample month'),
    ('One step per tab', '6 steps: numbers to monthly check-ins'),
    ('Every sum tested', '0 formula errors, locked in Excel'),
    ('Paper version included', 'Printable pages in A4 and US Letter')])
infographic('09', '5 reasons to buy from us', [
    ('Made by a money expert', 'Joel, MSc Behavioural Economics'),
    ('Couples are our specialty', 'A whole range of tools made for two'),
    ('Example + blank copy', 'See it filled in, then start your own'),
    ('Real help if you need it', 'Email Joel with any question'),
    ('What you see is what you get', 'Every screen shown is the real file')], SAGE, CREAM)
print(sorted(os.listdir('photos')))
