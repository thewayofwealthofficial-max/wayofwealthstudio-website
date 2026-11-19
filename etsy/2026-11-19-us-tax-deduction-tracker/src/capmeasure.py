"""Cap-height meter for video frames: ink pixels (far from the panel background), split into text lines by row
projection, then the 90th-percentile height of the glyph components in each line: capitals, digits and ascenders (cap height)."""
import numpy as np
from scipy import ndimage


def lines_cap(img, box=None, thresh=70, min_comp=3):
    a = np.array(img.convert('L') if box is None else img.convert('L').crop(box)).astype(int)
    bg = np.median(a)
    ink = np.abs(a - bg) > thresh
    rows = ink.any(1); out = []
    lab, n = ndimage.label(rows)
    for i in range(1, n + 1):
        ys = np.where(lab == i)[0]; y0, y1 = ys.min(), ys.max() + 1
        if y1 - y0 < 6: continue
        seg = ink[y0:y1]
        cl, m = ndimage.label(seg)
        hs = [sl[0].stop - sl[0].start for sl in ndimage.find_objects(cl) if (sl[1].stop - sl[1].start) > 2 and (sl[0].stop - sl[0].start) > 4]
        if len(hs) >= min_comp:
            out.append((int(y0), round(float(np.percentile(hs, 90)), 1)))
    return out
