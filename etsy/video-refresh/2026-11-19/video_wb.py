# ADHD Money Management Workbook 4474743614 - in-use video: real workbook pages filled in (pdftoppm 400 dpi), a page turn,
# then the FIXED companion tracker with one impulse purchase typed in (stages_wb.py, LibreOffice renders, formulas recalc).
# Review round 1: whole columns only (>=40 px side margin), hard cuts (the page turn is the only animated move), real KPI cards in place.
import os
from PIL import Image, ImageDraw
from vidlib import *
V=os.path.dirname(os.path.abspath(__file__)); W_=V+'/work'; PG=W_+'/pg'; S=W_+'/wbst'
r=Reel()
P11=Image.open(PG+'/h-11.png').convert('RGB'); P20=Image.open(PG+'/h-20.png').convert('RGB')
TYPE=(28,58,140)
def write(page,items):
    p=page.copy(); d=ImageDraw.Draw(p)
    for x,y,t in items: d.text((x,y),t,font=inter(54,500),fill=TYPE,anchor='ls')
    return p
# 1 Module 3 page (p11): impulse zones typed on the page's own blank lines (underline rows found in the render)
def _h():
    im=Image.open(f'{V}/work/wbst/s0-2.png').convert('RGB').crop((2313,150,3067,330))   # real Total Impulse Spend card, fixed file's own sample data
    return title_card(['ADHD Money','Management Workbook'],'Workbook pages + companion tracker',im,label='title card')
h=_h()
Z=(1712,738,3098,1812)   # 60 px of page below the last answer line
ans=[(1840,1290),(1840,1506),(1840,1723)]
T=('Fill in your workbook','Module 3: your impulse zones')
CH=[(0,'Late at night,'),(0,'Late at night, in bed'),(1,'My phone'),(2,'Tired,'),(2,'Tired, or a social ad')]
def zones(k):
    last={}
    for i,t in CH[:k]: last[i]=t
    return write(P11,[(ans[i][0],ans[i][1],t) for i,t in last.items()]).crop(Z)
r.hold(h,1.3); r.hold(frame(zones(0),*T,label='workbook zones'),0.35)
for k in range(1,6): r.hold(frame(zones(k),*T),0.24)
done=zones(5); r.hold(frame(done,*T,hl=(1820-Z[0],1230-Z[1],2900-Z[0],1745-Z[1])),0.6)
# 2 page turn to Module 8, card 3 (p20): wait times typed, "Yes" circled
C=(215,2470,1625,3420)
T2=('Turn the page, make a plan','Module 8: your pause times')
def plan(k,circle=False):
    p=write(P20,[(830,2865,'1 hour'),(778,2981,'24 hours'),(793,3101,'72 hours')][:k])
    if circle: ImageDraw.Draw(p).ellipse((722,3248,838,3358),outline=TYPE,width=8)
    return p.crop(C)
r.hold(frame(plan(0),*T2,label='workbook plan'),0.5)   # hard cut to Module 8
for k in (1,2,3): r.hold(frame(plan(k),*T2),0.27)
r.hold(frame(plan(3,True),*T2,hl=(740-C[0],2780-C[1],1060-C[0],3360-C[1])),0.6)
# 3 companion tracker, Impulse Spend Log (grid at 400 dpi: header 404-559, row 5 559-706, then 151 px rows)
X=dict(A=79,B=471,C=1227,D=1619,E=2284,F=2888,G=3311,H=3734,I=4580)
HEAD=(402,559); rt=lambda n: 559 if n==5 else 706+151*(n-6)
L=lambda st,p: Image.open(f'{S}/s{st}-{p}.png').convert('RGB')
def logv(st,c0,c1,r0=6,r1=8,img=None,extra=0):
    im=img or L(st,1); xa,xb=X[c0]-4,X[c1]+4
    hd=im.crop((xa,HEAD[0],xb,HEAD[1])); body=im.crop((xa,rt(r0),xb,rt(r1+1)+3+extra))
    c=Image.new('RGB',(body.width,hd.height+body.height),(255,255,255)); c.paste(hd,(0,0)); c.paste(body,(0,hd.height))
    y=hd.height+rt(8)-rt(r0); return c,(0,y,c.width,y+151)
T3=('Then log it in the tracker','Date, then what you bought')
for st,sec in ((0,0.3),(1,0.3),(2,0.3),(3,0.5)):
    c,b=logv(st,'A','C'); r.hold(frame(c,*T3,hl=b,label='tracker A:B'),sec)
TRIG=['Boredom','Stress','Dopamine Chase','Social Media Ad','Emotional Reward','Hyperfocus','Rejection Sensitivity','Tired','Other']
def dropdown(st):  # the Trigger column's own 9 options, open under the new row, inside column D
    im=L(st,1).copy(); d=ImageDraw.Draw(im); x0,x1=X['D']+8,X['E']-10; y0=rt(9)+2; ih=66
    d.rectangle((x0,y0,x1,y0+ih*len(TRIG)),fill=(255,255,255),outline=(150,130,110),width=3)
    for i,o in enumerate(TRIG):
        if o=='Tired': d.rectangle((x0+3,y0+i*ih+3,x1-3,y0+(i+1)*ih-3),fill=(232,240,254))
        d.text((x0+20,y0+i*ih+ih/2),o,font=inter(54),fill=(40,40,40),anchor='lm')
    return im
T4=('Amount, then the trigger','Pick it from the list')
for st,sec in ((3,0.25),(4,0.4)):
    c,b=logv(st,'C','E'); r.hold(frame(c,*T4,hl=b,label='tracker C:D'),sec)
c,b=logv(4,'C','E',8,8,img=dropdown(4),extra=(rt(9)+2+66*9+16)-(rt(9)+3)); r.hold(frame(c,*T4,hl=b,label='trigger list'),0.85)
c,b=logv(5,'C','E'); r.hold(frame(c,*T4,hl=b),0.45)
T5=('Did you pause first?','Pick how long you waited')
for st,sec in ((5,0.3),(6,0.6)):
    c,b=logv(st,'E','F'); r.hold(frame(c,*T5,hl=b,label='tracker E'),sec)
T6=('Still bought it? Regret?','Rate the regret 1 to 5')
for st,sec in ((6,0.25),(7,0.45),(8,0.6)):
    c,b=logv(st,'F','H'); r.hold(frame(c,*T6,hl=b,label='tracker F:G'),sec)
# 4 dashboard: the real KPI row, zoomed on one whole card at a time (E:F, then G:H), before / after
CY=(150,330); VB=(232,287)   # label row 178-232, value row 232-286
def card(st,x0,x1): return L(st,2).crop((x0-4,CY[0],x1+4,CY[1]))
HB=lambda c: (4,VB[0]-CY[0],c.width-4,VB[1]-CY[0])
for (x0,x1),sub0,sub1 in (((1571,2317),'Impulse purchases, before','After: one more logged'),((2317,3063),'Total impulse spend, before','After: up by $59')):
    c0=card(0,x0,x1); c1=card(8,x0,x1)
    r.hold(frame(c0,'Your dashboard updates',sub0,label='kpi card'),0.6); r.hold(frame(c1,'Your dashboard updates',sub1,hl=HB(c1)),0.9)
r.hold(h,0.9)
out=V+'/ADHD Money Management Workbook 4474743614 - video NEW.mp4'
print(r.save(out,W_+'/frames_w')); print(sorted(set(LOG)))
