#!/bin/bash
# hi-res per-tab renders, cropped to content -> out/hi/t-N.png
cd "$(dirname "$0")/out" && mkdir -p hi && rm -f hi/*.png && pdftoppm -r 220 -png sample.pdf hi/raw && python3 - <<'P'
import glob
from PIL import Image, ImageChops
for f in sorted(glob.glob('hi/raw-*.png')):
    im=Image.open(f).convert('RGB'); bg=Image.new('RGB',im.size,(255,255,255))
    bb=ImageChops.difference(im,bg).getbbox(); n=int(f.split('-')[-1].split('.')[0])
    im.crop(bb).save(f'hi/t-{n}.png'); print(n, im.crop(bb).size)
P
cd "$(dirname "$0")/out" 2>/dev/null || true
for p in 1 6 7 8; do pdftoppm -r 480 -png -f $p -l $p sample.pdf hi/big$p; done
python3 - <<'P'
import glob
from PIL import Image, ImageChops
for f in sorted(glob.glob('hi/big*.png')):
    im=Image.open(f).convert('RGB'); bg=Image.new('RGB',im.size,(255,255,255))
    bb=ImageChops.difference(im,bg).getbbox(); n=f.split('/')[-1][3:].split('-')[0]
    im.crop(bb).save(f'hi/T-{n}.png'); print('T',n, im.crop(bb).size)
P
