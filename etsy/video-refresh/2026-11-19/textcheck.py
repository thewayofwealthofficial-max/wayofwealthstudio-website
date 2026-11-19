# Extract a frame every 1 s and measure the smallest text line (ink height, px) on the product screen.
import sys, subprocess, os, glob, numpy as np
from PIL import Image
def bands(a):
    rows=np.where((a.sum(1))>=3)[0]; out=[]
    for y in rows:
        if out and y-out[-1][1]<=1: out[-1][1]=y
        else: out.append([y,y])
    return [q-p+1 for p,q in out]
def check(mp4, outdir, skip=()):
    os.makedirs(outdir,exist_ok=True)
    for f in glob.glob(outdir+'/c*.png'): os.remove(f)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',mp4,'-vf','fps=1','-start_number','0',outdir+'/c%02d.png'],check=True)
    res=[]
    for f in sorted(glob.glob(outdir+'/c*.png')):
        t=int(f[-6:-4])
        if t in skip: res.append((t,'photo 1')); continue
        im=np.asarray(Image.open(f).convert('L')).astype(int)[232:1010,20:1060]
        dark=(im<110)
        # drop long solid runs (dark header fills): keep only rows of a band that are not mostly filled
        b=[h for h in bands(dark) if 12<=h<120]   # <12 px bands are bullets, rules and underscore lines, not text
        res.append((t,min(b) if b else None))
    return res
if __name__=='__main__':
    print(check(sys.argv[1],sys.argv[2],tuple(int(x) for x in sys.argv[3:])))
