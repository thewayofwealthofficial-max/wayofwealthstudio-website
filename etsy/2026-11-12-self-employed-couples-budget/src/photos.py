"""Listing photos for the Self-Employed Couples Budget, slot for slot on the benchmark (8 photos, 2700x2025)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
from photos import *
from PIL import Image

O = os.path.join(HERE, 'out'); HI = os.path.join(O, 'hi'); C = os.path.join(O, 'crops'); os.makedirs(C, exist_ok=True)


def crop(src, box, name):
    p = os.path.join(C, name); Image.open(os.path.join(HI, src)).crop(box).save(p); return p


dash_top = crop('T-1.png', (0, 0, 2000, 1100), 'dash_top.png')
dash_main = crop('T-1.png', (0, 0, 2000, 1760), 'dash_main.png')
settings = crop('t-3.png', (0, 0, 1060, 1440), 'settings.png')
income = crop('t-4.png', (40, 320, 1860, 1150), 'income.png')
taxpot = crop('t-5.png', (30, 320, 2190, 1170), 'taxpot.png')
nextpay = crop('t-5.png', (1230, 1030, 2190, 1170), 'nextpay.png')
buffer = crop('T-6.png', (60, 960, 4100, 2460), 'buffer.png')
taxm = crop('t-5.png', (1230, 360, 2190, 1170), 'taxm.png')
split = crop('T-8.png', (60, 680, 4720, 2100), 'split.png')
bills = crop('T-7.png', (100, 700, 4640, 1680), 'bills.png')
pays = crop('t-5.png', (30, 360, 1200, 600), 'pays.png')
TICK = lambda items, size=46: ''.join(f'<div class="tick" style="font-size:{size}px;margin-bottom:30px"><div class="bx">{n}</div><div>{t}</div></div>' for n, t in items)
pages = []
pages.append(page(
    title('Self-employed <b>couples</b> budget', 'tax pot first · steady pay · fair bill split', 70, 124, ssize=48)
    + laptop(dash_top, 170, 330, 1900)
    + '<div class="badge" style="left:2290px;top:390px">Tax pot<br>built in</div>'
    + '<div class="badge" style="left:2290px;top:760px">Steady<br>pay</div>'
    + '<div class="badge" style="left:2290px;top:1130px">Fair<br>split</div>'
    + '<div class="strip">Google Sheets <i>|</i> Excel <i>|</i> 9 tabs <i>|</i> any country</div>'
    + '<div class="seal"><span>WoW</span>qualified<br>planner</div>', foot=False))
pages.append(page(
    title('How it works', 'one regular paycheck, one income that goes up and down', 90, 120)
    + '<div style="position:absolute;left:170px;top:500px;width:1150px">'
    + '<div class="step"><h3>1 · Your details</h3><p>Names, currency, tax pot % and how to split: by income, 50-50 or your own %.</p></div><br><br>'
    + '<div class="step"><h3>2 · Log the month</h3><p>Money in and business costs for the self-employed partner, take-home pay for the other.</p></div><br><br>'
    + '<div class="step"><h3>3 · Spend calmly</h3><p>Tax is set aside, pay stays steady, bills are split. One safe-to-spend number for you both.</p></div></div>'
    + f'<div class="card" style="left:1440px;top:400px;width:1100px"><img src="{img(settings)}"></div>'))
L0, T0, CW = 600, 400, 1500
co = [('Safe to spend together, after tax and bills', 40, 745, 520, 'right', L0, 775),
      ('Your next step, chosen for you', 40, 966, 520, 'right', L0, 996),
      ('Income vs steady pay, month by month', 40, 1450, 520, 'right', L0, 1480),
      ('Tax pot and steady pay', 2150, 674, 520, 'left', L0 + CW, 704),
      ('Buffer and low months', 2150, 831, 520, 'left', L0 + CW, 861),
      ('Money talk: 12 questions to agree', 2150, 1101, 520, 'left', L0 + CW, 1131),
      ('Who pays the shared costs', 2150, 1450, 520, 'left', L0 + CW, 1480)]
pages.append(page(
    title('Your dashboard', 'one screen · every number worked out for you', 90, 120)
    + f'<div class="card" style="left:{L0}px;top:{T0}px;width:{CW}px"><img src="{img(dash_main)}"></div>'
    + callouts(co)))
sc = 1.3; IW = int(1820 * sc); X0 = (2700 - IW) // 2; Y0 = 400; BOT = Y0 + int(830 * sc)
pages.append(page(
    title('Income log', 'one row a month · the tax share is worked out for you', 90, 120)
    + f'<div class="card" style="left:{X0}px;top:{Y0}px;width:{IW}px"><img src="{img(income)}"></div>'
    + callouts([('Money in and business costs', 120, 1640, 560, 'up', X0 + int(330 * sc), BOT, 1500),
                ('Tax pot % set aside automatically', 760, 1640, 600, 'up', X0 + int(1180 * sc), BOT, 1540),
                ('What is left after tax', 1440, 1640, 520, 'up', X0 + int(1450 * sc), BOT, 1580),
                ('Highs, lows and the average', 2060, 1640, 540, 'up', X0 + int(1700 * sc), BOT, 1620)])))
BW = 1880; BH = int(BW * 1500 / 4040); BB = 400 + BH
pages.append(page(
    title('The buffer', 'good months fill it · low months draw on it', 90, 120)
    + f'<div class="card" style="left:80px;top:400px;width:{BW}px"><img src="{img(buffer)}"></div>'
    + f'<div class="card" style="left:2010px;top:400px;width:620px"><img src="{img(taxm)}"></div>'
    + '<div style="position:absolute;left:2010px;top:980px;width:620px;font-size:40px;line-height:1.35;color:#5A4A52">'
    + 'Tax Pot tab: set aside, paid out, and whether the pot covers the next tax bill.</div>'
    + callouts([('Same pay every month, whatever came in', 120, 1560, 700, 'up', 80 + int(BW * 1620 / 4040), BB, 1400),
                ('In or out of the buffer', 860, 1560, 520, 'up', 80 + int(BW * 2220 / 4040), BB, 1440),
                ('Low months flagged and covered', 1420, 1560, 620, 'up', 80 + int(BW * 3200 / 4040), BB, 1480)])))
pages.append(page(
    title('5 things it does for you', 'tax, steady pay and a fair split, all year', 90, 120)
    + f'<div class="card" style="left:90px;top:390px;width:1640px"><img src="{img(bills)}"></div>'
    + f'<div class="card" style="left:90px;top:800px;width:1640px"><img src="{img(split)}"></div>'
    + f'<div class="card" style="left:90px;top:1360px;width:1640px"><img src="{img(pays)}"></div>'
    + '<div style="position:absolute;left:1790px;top:420px;width:860px">'
    + TICK([('✓', '<b>Tax pot</b>: your % set aside first'), ('✓', '<b>Tax dates</b>: US, UK or your own'),
            ('✓', '<b>Steady pay</b>: a buffer for low months'), ('✓', '<b>Fair split</b>: by income, 50-50 or your %'),
            ('✓', '<b>Money talk</b>: 12 questions to agree')], 46)
    + '</div>'))
pages.append(page(
    title('Getting started', 'instant download · no subscription', 90, 120)
    + '<div style="position:absolute;left:170px;top:520px;width:1050px">'
    + '<div class="step"><h3>Buy it</h3><p>Your files are ready on Etsy straight away.</p></div><br><br>'
    + '<div class="step"><h3>Open it</h3><p>Excel file with an example copy and a blank copy, plus a short guide for Google Sheets.</p></div><br><br>'
    + '<div class="step"><h3>Use it</h3><p>Add your names, tax % and pay. The rest is worked out for you.</p></div></div>'
    + laptop(dash_top, 1330, 520, 1560)))
pages.append(page(
    title('5 reasons to buy from us', 'Way of Wealth Studio', 90, 120)
    + '<div style="position:absolute;left:260px;top:480px;width:2200px">'
    + TICK([(1, '<b>Made by a qualified financial planner</b>, not a template shop'),
            (2, '<b>Real help</b> - questions answered by email by Joel himself'),
            (3, '<b>Example and blank copies</b>, plus a step-by-step guide'),
            (4, '<b>Google Sheets and Excel</b> - formulas locked in Excel so nothing breaks'),
            (5, '<b>Instant download</b> - no subscription, no app, yours to keep')], 58)
    + '</div><div class="card" style="left:260px;top:1200px;width:2180px;padding:50px 70px;border-radius:24px">'
    + '<div style="font-family:Lora,serif;font-weight:600;font-size:66px;color:#4A2C3D;margin-bottom:18px">Good to know</div>'
    + '<div style="font-size:46px;line-height:1.4;color:#5A4A52">Digital download: nothing is posted to you. '
    + 'Works in Google Sheets (free) and Microsoft Excel. A planning tool, not tax advice.</div></div>'))
render(pages, os.path.join(O, 'photos'))
print('done')
