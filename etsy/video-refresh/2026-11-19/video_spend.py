# ADHD Spending Tracker 4483114999 - in-use video from LibreOffice renders of openpyxl copies (stages_spend.py, FIXED file).
# Review round 1: whole columns only (>=40 px side margin), hard cuts, no pans, no cross-fades.
import os
from PIL import Image, ImageDraw
from vidlib import *
V=os.path.dirname(os.path.abspath(__file__)); W_=V+'/work'; S=W_+'/sp'
L=lambda st,p: Image.open(f'{S}/s{st}-{p}.png').convert('RGB')
X=dict(B=153,C=498,D=1238,E=1584,F=2028,G=2422,H=2768,I=3507,J=4494)   # column edges (grid.py, 400 dpi)
HEAD=(290,412); RH=66.67; rt=lambda r: 412+RH*(r-5); NEW=14
def logv(st,c0,c1,r0=9,r1=15,img=None,hl=True):
    im=img or L(st,1); xa=X[c0]-4; xb=X[c1]+4
    head=im.crop((xa,HEAD[0]-2,xb,HEAD[1])); body=im.crop((xa,round(rt(r0)),xb,round(rt(r1+1))+3))
    c=Image.new('RGB',(head.width,head.height+body.height),(255,255,255)); c.paste(head,(0,0)); c.paste(body,(0,head.height))
    y=head.height+(rt(NEW)-rt(r0)); return c,((0,y,c.width,y+RH) if hl else None)
def dropdown(st):
    """the Impulse? column's own validation list (Planned / Impulse / Semi-Impulse), open under the new row, inside column F"""
    im=L(st,1).copy(); d=ImageDraw.Draw(im); x0,x1=X['F']+6,X['G']-8; y0=rt(NEW+1)+2; ih=70; opts=['Planned','Impulse','Semi-Impulse']
    d.rectangle((x0,y0,x1,y0+ih*3),fill=(255,255,255),outline=(150,130,110),width=3)
    for i,o in enumerate(opts):
        if o=='Impulse': d.rectangle((x0+3,y0+i*ih+3,x1-3,y0+(i+1)*ih-3),fill=(232,240,254))
        d.text((x0+16,y0+i*ih+ih/2),o,font=inter(50),fill=(40,40,40),anchor='lm')
    return im
r=Reel()
ex=Image.open(W_+'/ex/sp-1.png').convert('RGB').crop((167,362,1039,704))   # EXAMPLE file: the real Total Spent card (column B)
h=title_card(['ADHD Spending Tracker'],'Track why you spend, not just what',ex,label='title card')
c,_=logv(0,'B','D',5,15,hl=False); r.hold(h,1.4); r.hold(frame(c,'Your Spending Log','Every purchase in 30 seconds',label='full log'),1.4)
T=('Log an impulse buy','Date, then what you bought')
for st,sec in ((0,0.25),(1,0.4),(2,0.35),(3,0.55)):
    c,b=logv(st,'B','D'); r.hold(frame(c,*T,hl=b,label='B:C'),sec)
T=('Amount and category','Type it, pick it')
for st,sec in ((3,0.3),(4,0.45),(5,0.6)):
    c,b=logv(st,'D','F'); r.hold(frame(c,*T,hl=b,label='D:E'),sec)
T=('Planned or impulse?','Pick it, then rate it 1-5')
for st,dd,sec in ((5,0,0.25),(5,1,0.75),(6,0,0.45),(7,0,0.55)):
    c,b=logv(st,'F','H',9,18,img=dropdown(st) if dd else None); r.hold(frame(c,*T,hl=b,label='F:G'),sec)
T=('What set it off?','A quick note on the trigger')
for st,sec in ((7,0.25),(8,0.4),(9,0.6)):
    c,b=logv(st,'H','I'); r.hold(frame(c,*T,hl=b,label='H'),sec)
c,b=logv(9,'I','J'); r.hold(frame(c,'Your pattern, spotted','The note fills in by itself',hl=b,label='I'),1.4)
# dashboard: the real KPI cards in columns B:C (Total Spent, # Purchases), before / after
def dash(st): return L(st,2).crop((167,362,1039,704))   # the whole Total Spent card (column B)
b2=(4,90,868,338)
r.hold(frame(dash(0),'Dashboard updates','Before the earbuds',label='dash'),1.0)
r.hold(frame(dash(9),'Dashboard updates','After: total spent goes up',hl=b2),1.8); r.hold(h,1.0)
out=V+'/ADHD Spending Tracker 4483114999 - video NEW.mp4'
print(r.save(out,W_+'/frames_s')); print(sorted(set(LOG)))
