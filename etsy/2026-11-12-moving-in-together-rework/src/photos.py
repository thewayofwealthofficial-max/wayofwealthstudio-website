"""Listing photos for the Moving In Together Money Planner, slot for slot on the benchmark (8 photos, 2700x2025)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
from photos import *
from PIL import Image

O = os.path.join(HERE, 'out'); HI = os.path.join(O, 'hi'); C = os.path.join(O, 'crops'); os.makedirs(C, exist_ok=True)


def crop(src, box, name):
    p = os.path.join(C, name); Image.open(os.path.join(HI, src)).crop(box).save(p); return p


dash_top = crop('T-1.png', (0, 0, 1970, 1100), 'dash_top.png')
dash_main = crop('T-1.png', (0, 0, 1970, 1720), 'dash_main.png')
settings = crop('t-3.png', (0, 0, 1020, 1120), 'settings.png')
billsL = crop('t-5.png', (30, 270, 1256, 720), 'billsL.png')
billsR = crop('t-5.png', (1474, 270, 2010, 720), 'billsR.png')
settle = crop('T-7.png', (0, 380, 3060, 1500), 'settle.png')
year = crop('T-6.png', (0, 0, 3255, 2400), 'year.png')
sav = crop('T-8.png', (0, 640, 3699, 1720), 'sav.png')
talk = crop('t-9.png', (40, 320, 2190, 1000), 'talk.png')
TICK = lambda items, size=46: ''.join(f'<div class="tick" style="font-size:{size}px;margin-bottom:30px"><div class="bx">{n}</div><div>{t}</div></div>' for n, t in items)

pages = []
# 1 cover
pages.append(page(
    title('Moving in <b>together</b>', 'Money planner · move-in costs · shared bills · who pays what', 70, 132, ssize=48)
    + laptop(dash_top, 170, 330, 1900)
    + '<div class="badge" style="left:2290px;top:390px">Fair split<br>by income</div>'
    + '<div class="badge" style="left:2290px;top:760px">Both<br>incomes</div>'
    + '<div class="badge" style="left:2290px;top:1130px">12-month<br>view</div>'
    + '<div class="strip">Google Sheets <i>|</i> Excel <i>|</i> 9 tabs <i>|</i> any currency</div>'
    + '<div class="seal"><span>WoW</span>qualified<br>planner</div>', foot=False))
# 2 how it works
pages.append(page(
    title('How it works', '9 tabs · ready in three steps', 90, 120)
    + '<div style="position:absolute;left:170px;top:520px;width:1150px">'
    + '<div class="step"><h3>1 · Your details</h3><p>Names, take-home pay and currency. Choose the split: by income, 50-50 or your own %.</p></div><br><br>'
    + '<div class="step"><h3>2 · Your costs</h3><p>Type in what the move will cost and every bill you will share.</p></div><br><br>'
    + '<div class="step"><h3>3 · Day to day</h3><p>Log shared spending as it happens. It shows who owes whom and what is due each month.</p></div></div>'
    + f'<div class="card" style="left:1420px;top:410px;width:1150px"><img src="{img(settings)}"></div>'))
# 3 dashboard, dots on the card edge
L0, T0, CW = 600, 400, 1500
co = [('Shared bills and each person\'s part', 40, 743, 520, 'right', L0, 773),
      ('Your next step, chosen for you', 40, 959, 520, 'right', L0, 989),
      ('Charts that update on their own', 40, 1443, 520, 'right', L0, 1473),
      ('Move-in costs, savings, what is left', 2150, 674, 520, 'left', L0 + CW, 704),
      ('Settle up: who owes whom', 2150, 838, 520, 'left', L0 + CW, 868),
      ('First year of bills and the biggest month', 2150, 1101, 520, 'left', L0 + CW, 1131),
      ('Who pays the move, at a glance', 2150, 1443, 520, 'left', L0 + CW, 1473)]
pages.append(page(
    title('Your dashboard', 'one screen · every number worked out for you', 90, 120)
    + f'<div class="card" style="left:{L0}px;top:{T0}px;width:{CW}px"><img src="{img(dash_main)}"></div>'
    + callouts(co)))
# 4 shared bills zoom, dots on the card's bottom edge
sc = 1.48
LW, RW = int(1226 * sc), int(536 * sc); X0 = (2700 - LW - RW - 40) // 2; Y0 = 420; Hh = int(450 * sc); BOT = Y0 + Hh
pages.append(page(
    title('Shared bills', 'every bill you share, split fairly', 90, 120)
    + f'<div class="card" style="left:{X0}px;top:{Y0}px;width:{LW}px"><img src="{img(billsL)}"></div>'
    + f'<div class="card" style="left:{X0+LW+40}px;top:{Y0}px;width:{RW}px"><img src="{img(billsR)}"></div>'
    + callouts([('Any bill: weekly, monthly, quarterly or yearly', 80, 1420, 600, 'up', X0 + int(1040 * sc), BOT, 1220),
                ('Quarterly and yearly bills land in the right month', 740, 1420, 600, 'up', X0 + int(1160 * sc), BOT, 1270),
                ('Turned into a monthly amount', 1420, 1420, 540, 'up', X0 + LW + 40 + int(100 * sc), BOT, 1320),
                ('Each person\'s share, worked out', 2040, 1420, 560, 'up', X0 + LW + 40 + int(400 * sc), BOT, 1370)])))
# 5 settle up
SW = 2460; SX = 120; SH = int(SW * 1120 / 3060); SB = 400 + SH
pages.append(page(
    title('Settle up', 'log shared spending · one line says who owes whom', 90, 120)
    + f'<div class="card" style="left:{SX}px;top:400px;width:{SW}px"><img src="{img(settle)}"></div>'
    + callouts([('Log what you spent', 160, 1600, 560, 'up', SX + int(SW * 700 / 3060), SB, 1460),
                ('Who paid, and who it was for', 900, 1600, 640, 'up', SX + int(SW * 1500 / 3060), SB, 1500),
                ('Each person\'s share and the balance, worked out', 1700, 1600, 820, 'up', SX + int(SW * 2600 / 3060), SB, 1540)])))
# 6 five highlights
pages.append(page(
    title('5 things it does for you', 'plan the move and your first year together', 90, 120)
    + f'<div class="card" style="left:110px;top:390px;width:1150px"><img src="{img(year)}"></div>'
    + f'<div class="card" style="left:110px;top:1290px;width:1150px"><img src="{img(talk)}"></div>'
    + f'<div class="card" style="left:1330px;top:390px;width:1260px"><img src="{img(sav)}"></div>'
    + '<div style="position:absolute;left:1340px;top:860px;width:1280px">'
    + TICK([('✓', '<b>Fair split</b>: by income, 50-50 or your own %'),
            ('✓', '<b>12-month view</b>: big months spotted early'),
            ('✓', '<b>Move fund</b>: what to save each month'),
            ('✓', '<b>Settle up</b>: who owes whom, worked out'),
            ('✓', '<b>Money talk</b>: 12 questions to agree first')], 52)
    + '</div>'))
# 7 getting started
pages.append(page(
    title('Getting started', 'instant download · no subscription', 90, 120)
    + '<div style="position:absolute;left:170px;top:520px;width:1050px">'
    + '<div class="step"><h3>Buy it</h3><p>Your files are ready on Etsy straight away.</p></div><br><br>'
    + '<div class="step"><h3>Open it</h3><p>Excel file with an example copy and a blank copy, plus a short guide for Google Sheets.</p></div><br><br>'
    + '<div class="step"><h3>Use it</h3><p>Add your names and pay. The rest is worked out for you.</p></div></div>'
    + laptop(dash_top, 1330, 520, 1560)))
# 8 five reasons to buy from us + good to know
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
    + 'Works in Google Sheets (free) and Microsoft Excel, on a computer, tablet or phone app.</div></div>'))
render(pages, os.path.join(O, 'photos'))
print('done')
