import sys; sys.path.insert(0,'/home/claude/nbkit'); import nb
from PIL import Image
P=lambda n: Image.open(f'hi/p-{n:02d}.png').convert('RGB')
def top(n,f): im=P(n); return im.crop((0,0,im.width,int(im.height*f)))
A={'01':[(P(1),'tab'),(top(9,0.55),'phone')],'03':[(P(8),'tab')],'04':[(P(9),'tab')],'05':[(P(10),'tab')],
   '06':[(P(13),'tab'),(P(14),'tab')],'07':[(P(16),'tab')],'08':[(P(2),'tab')]}
for k in sys.argv[1:] or ['01','02','03','04','05','06','07','08','09']:
    if k in A: nb.composite(f'raw/s{k}.png',f'photos/{k}.jpg',A[k])
    else: Image.open(f'raw/s{k}.png').convert('RGB').resize((2000,2000),Image.LANCZOS).save(f'photos/{k}.jpg',quality=90)
