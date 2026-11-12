"""15s listing video: the real example file in use (a month logged, tax pot and buffer update), from recalculated stage copies."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import video, stages
O = os.path.join(HERE, 'out'); W = os.path.join(O, 'stg'); H = lambda f: os.path.join(O, 'hi', f)
src = os.path.join(O, 'sample.xlsx')
base = stages.stage(src, [], 'base', [1, 4], W, dpi=300)
nov = stages.stage(src, [('Income Log', 'C19', 6400), ('Income Log', 'D19', 450), ('Income Log', 'H19', 3350)], 'nov', [1, 4], W, dpi=300)
k = 300 / 220
IB = (int(40 * k), int(320 * k), int(1860 * k), int(1000 * k))
DB = (0, 0, int(2000 * 300 / 480), int(1100 * 300 / 480))
sec = video.make([
    (2.5, H('T-1.png'), 'Safe to spend, together', 'zoom', (0, 0, 2000, 1760)),
    (3.5, [(0, base[4], 'Log the month...'), (0.45, nov[4], '...tax set aside for you')], '', 'hold', IB),
    (3.0, [(0, base[1], 'Before November...'), (0.45, nov[1], '...after: tax pot covers the bill')], '', 'hold', DB),
    (2.0, H('T-6.png'), 'Steady pay, even in low months', 'zoom', (60, 960, 4100, 2460)),
    (2.0, H('T-8.png'), 'Bills split fairly', 'zoom', (60, 680, 3300, 2100))],
    (2.0, ['Self-Employed', 'Couples Budget'], ['Tax pot · buffer · fair split', 'Google Sheets + Excel', 'Example + blank copy']),
    os.path.join(O, 'video.mp4'), os.path.join(O, 'vf'))
print(sec, 'seconds')
