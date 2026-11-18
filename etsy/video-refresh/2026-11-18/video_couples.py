# Couples Money Conversation Starter 4478858153 - in-use video (real PDF pages, buyer's answers overlaid in pen-style ink)
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V=os.path.dirname(os.path.abspath(__file__)); W_=V+'/work'; CP=W_+'/cp'
F='/home/claude/fonts/'
pf=lambda s: ImageFont.truetype(F+'PF-700-normal.ttf',s); pfi=lambda s: ImageFont.truetype(F+'PF-400-italic.ttf',s); pfr=lambda s: ImageFont.truetype(F+'PF-400-normal.ttf',s)
HAND='/usr/share/fonts/truetype/google-fonts/ofl/comicrelief/ComicRelief-Regular.ttf'
ink=lambda s: ImageFont.truetype(HAND,s)
INK=(42,38,32); GOLD_D=(160,122,74); PEN=(36,62,140); OUT=1080; FPS=30; k=4
def bg():
    im=Image.new('RGB',(OUT,OUT)); d=ImageDraw.Draw(im)
    for y in range(OUT):
        t=y/OUT; d.line([(0,y),(OUT,y)],fill=tuple(int(a+(b-a)*t) for a,b in zip((252,244,236),(244,232,216))))
    d.text((OUT/2,1040),'W A Y   O F   W E A L T H   S T U D I O',font=pfr(22),fill=GOLD_D,anchor='mm')
    return im
BG=bg()
PG={p:Image.open(f'{CP}/h-{p:02d}.png').convert('RGB') for p in (1,4,10,11)}
LOG=[]  # (label, display scale px per 100-dpi px) for text-height check
def frame(src, title, sub, hl=None):
    im=BG.copy(); d=ImageDraw.Draw(im)
    d.text((OUT/2,92),title,font=pf(64),fill=INK,anchor='mm')
    d.text((OUT/2,168),sub,font=pfi(42),fill=GOLD_D,anchor='mm')
    W=1000; sc=W/src.width; h=round(src.height*sc)
    if h>760: sc=760/src.height; h=760; W=round(src.width*sc)
    x0=(OUT-W)//2; top=240+(760-h)//4
    sh=Image.new('L',(OUT,OUT),0); ImageDraw.Draw(sh).rounded_rectangle((x0,top+12,x0+W,top+h+12),20,fill=80)
    im.paste((150,115,70),(0,0),sh.filter(ImageFilter.GaussianBlur(16)))
    view=src.resize((W,h),Image.LANCZOS)
    m=Image.new('L',(W,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,W-1,h-1),20,fill=255)
    im.paste(view,(x0,top),m)
    if hl:
        a,b,c,e=hl; d.rounded_rectangle((x0+a*sc-6,top+b*sc-6,x0+c*sc+6,top+e*sc+6),12,outline=(176,128,60),width=6)
    return im, sc*k
def crop(page,b): return page.crop(tuple(int(v*k) for v in b))
def shot(page,b,title,sub,hl=None,label=None):
    c=crop(page,b); h=None
    if hl: h=tuple((v-o)*k for v,o in zip(hl,(b[0],b[1],b[0],b[1])))
    im,s=frame(c,title,sub,h)
    if label: LOG.append((label,s))
    return im
frames=[]
def hold(img,sec): frames.extend([img]*round(sec*FPS))
def fade(a,b,sec=0.3):
    n=round(sec*FPS)
    for i in range(n): frames.append(Image.blend(a,b,(i+1)/n))
ease=lambda t: t*t*(3-2*t)
def move(page,b0,b1,sec,title,sub):
    n=round(sec*FPS)
    for i in range(n):
        t=ease((i+1)/n); b=tuple(p+(q-p)*t for p,q in zip(b0,b1))
        frames.append(frame(crop(page,b),title,sub)[0])
hero=Image.open(W_+'/hero_c.jpg').convert('RGB').resize((OUT,OUT),Image.LANCZOS)

# 1 cover (real page 1)
cov=shot(PG[1],(40,20,790,540),'A real guide for two','Open it together, start on page one',label='cover subtitle')
hold(hero,1.2); fade(hero,cov); hold(cov,1.3)
# 2 the deck of question cards (real Track 4 prompt cards, page 10) - zoom in one card at a time
T2=('Real question cards','One prompt at a time, no fighting')
ALL=(50,410,780,765); C1=(52,414,286,632); C2=(297,414,531,632); C3=(543,414,777,632)
f1=shot(PG[10],C1,*T2,label='card text'); fade(cov,f1); hold(f1,1.0)
f2=shot(PG[10],C2,*T2); fade(f1,f2,0.25); hold(f2,0.9)
f3=shot(PG[10],C3,*T2); fade(f2,f3,0.25); hold(f3,0.9)
# 3 the quiz worksheet being filled in (page 4): name typed letter by letter, answers circled
Q=(35,145,300,250); T3=('Take the quiz alone','Your name, your honest answers')
def quiz(name,circles):
    p=PG[4].copy(); d=ImageDraw.Draw(p)
    if name: d.text((138*k,165*k),name,font=ink(15*k),fill=PEN,anchor='ls')
    for y in circles: d.ellipse((40*k,(y-7.5)*k,60*k,(y+6.5)*k),outline=PEN,width=int(1.3*k))
    return p
q0=shot(quiz('',[]),Q,*T3,label='quiz options'); fade(f3,q0); hold(q0,0.35)
for nm in ('S','Sa','Sam'): hold(shot(quiz(nm,[]),Q,*T3),0.2)
hold(shot(quiz('Sam',[]),Q,*T3),0.2)
qd=shot(quiz('Sam',[214]),Q,*T3,hl=(40,207,250,221)); hold(qd,0.8)
# 4 a prompt card answered in the blank space, word by word (page 10, Prompt 1)
T4=('Write your answers','Fill in the blanks together')
ans=['A home of our own,','and no credit card','debt by 2030']
def card(nw):
    p=PG[10].copy(); d=ImageDraw.Draw(p); words=' '.join(ans).split(); shown=words[:nw]; i=0
    for ln,line in enumerate(ans):
        n=len(line.split()); part=' '.join(shown[i:i+n]); i+=n
        if part: d.text((70*k,(553+21*ln)*k),part,font=ink(12.5*k),fill=PEN,anchor='ls')
    return p
c0=shot(card(0),C1,*T4); fade(qd,c0); hold(c0,0.3)
nwords=len(' '.join(ans).split())
for nw in (2,4,6,8,nwords): hold(shot(card(nw),C1,*T4),0.27)
cf=shot(card(nwords),C1,*T4,hl=(62,535,272,611)); hold(cf,0.5)
# 5 the 30-day plan (page 11): pan from Week 1 to Week 2, buyer ticks Week 1 done
T5=('Your 30-day plan','Tick off each week together')
B1=(36,228,470,385); B2=(380,318,796,470)
def cal(tick):
    p=PG[11].copy()
    if tick:
        d=ImageDraw.Draw(p); d.text((150*k,258*k),'done',font=ink(16*k),fill=PEN,anchor='ls')
        d.line([(200*k,250*k),(207*k,257*k),(222*k,239*k)],fill=PEN,width=int(2*k),joint='curve')
    return p
w1=shot(cal(False),B1,*T5,label='calendar text'); fade(cf,w1); hold(w1,0.4)
w1t=shot(cal(True),B1,*T5,hl=(45,236,345,368)); hold(w1t,0.6)
w2=shot(cal(True),B2,*T5,hl=(485,330,780,460)); fade(w1t,w2,0.25); hold(w2,0.9)
fade(w2,hero); hold(hero,0.9)

tmp=W_+'/frames_c'; shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp)
for i,f in enumerate(frames): f.save(f'{tmp}/f{i:04d}.png')
out=V+'/Couples Money Conversation Starter 4478858153 - video NEW.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{tmp}/f%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','24','-movflags','+faststart',out],check=True)
print(len(frames)/FPS,'s', os.path.getsize(out)); print(LOG)
