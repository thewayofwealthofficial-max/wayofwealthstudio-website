"""15s listing video: the real example file in use (split switched, a bill added), rendered from recalculated stage copies."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import video, stages
from PIL import Image
O = os.path.join(HERE, 'out'); W = os.path.join(O, 'stg'); H = lambda f: os.path.join(O, 'hi', f)
src = os.path.join(O, 'sample.xlsx')
fifty = stages.stage(src, [('Settings', 'C12', '50-50')], 'fifty', [5], W)
base = stages.stage(src, [], 'base', [1, 5], W, dpi=300)
added = stages.stage(src, [('Shared Bills', 'B18', 'Parking permit'), ('Shared Bills', 'C18', 'Transport'), ('Shared Bills', 'D18', 120),
                           ('Shared Bills', 'E18', 'Monthly'), ('Shared Bills', 'G18', 'Our split')], 'added', [1, 5], W, dpi=300)


def glue(p, name, dpi):
    k = dpi / 220
    im = Image.open(p)
    a = im.crop((int(30 * k), int(270 * k), int(440 * k), int(720 * k))); b = im.crop((int(1254 * k), int(270 * k), int(2010 * k), int(720 * k)))
    g = Image.new('RGB', (a.width + b.width, a.height), 'white'); g.paste(a, (0, 0)); g.paste(b, (a.width, 0))
    out = os.path.join(W, name + '.png'); g.save(out); return out


g50 = glue(fifty[5], 'g50', 220); gin = glue(os.path.join(O, 'hi', 't-5.png'), 'gin', 220)
k = 300 / 220
DB = (0, 0, int(1970 * 300 / 480), int(1100 * 300 / 480))
sec = video.make([
    (2.5, H('T-1.png'), 'Your move, planned together', 'zoom', (0, 0, 1970, 1720)),
    (3.5, [(0, g50, 'Split the bills 50-50...'), (0.45, gin, '...or by income: shares update')], '', 'hold', None),
    (3.0, [(0, base[1], 'Add a bill...'), (0.45, added[1], '...and every total updates')], '', 'hold', DB),
    (2.0, H('T-7.png'), 'Who owes whom, worked out', 'zoom', (0, 380, 2400, 1300)),
    (2.0, H('T-6.png'), 'Your first 12 months', 'pan', (0, 0, 3255, 2619))],
    (2.0, ['Moving In', 'Together'], ['Money planner', 'Google Sheets + Excel', 'Example + blank copy']),
    os.path.join(O, 'video.mp4'), os.path.join(O, 'vf'))
print(sec, 'seconds')
