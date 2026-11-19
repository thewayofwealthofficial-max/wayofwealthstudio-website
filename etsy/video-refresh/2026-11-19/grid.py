# find table grid lines (vertical + horizontal) in a 400-dpi render
import numpy as np
from PIL import Image
def grid(path, box=None, thr=0.5):
    im=np.asarray(Image.open(path).convert('RGB')).astype(int)
    if box: x0,y0,x1,y1=box; im=im[y0:y1,x0:x1]
    else: x0=y0=0
    r,g,b=im[...,0],im[...,1],im[...,2]
    line=(r-b>40)&(r<230)&(r>120)   # brown/gold border pixels
    dark=(r<90)&(g<90)&(b<90)
    vs=np.where(line.mean(0)>thr)[0]; hs=np.where(line.mean(1)>thr)[0]
    def runs(a,o):
        out=[];
        for v in a:
            if out and v-out[-1][1]<=2: out[-1][1]=v
            else: out.append([v,v])
        return [((p+q)//2)+o for p,q in out]
    return runs(vs,x0), runs(hs,y0)
if __name__=='__main__':
    import sys; print(grid(sys.argv[1], tuple(map(int,sys.argv[2:6])) if len(sys.argv)>5 else None, float(sys.argv[6]) if len(sys.argv)>6 else 0.5))
