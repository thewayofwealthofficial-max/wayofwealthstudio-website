# openpyxl copies of the real Therapist tracker with one new session typed in step by step; LibreOffice renders each (formulas recalc)
import openpyxl, datetime as dt, subprocess, os, sys, glob
V=os.path.dirname(os.path.abspath(__file__))
SRC=sys.argv[1] if len(sys.argv)>1 else V+'/src_ther/Therapist_SE_Tax_Tracker.xlsx'
OUT=V+'/work/st'; os.makedirs(OUT,exist_ok=True)
D=dt.date
inc=[(D(2026,4,30),'Private Client Session','Clients C-001 to C-016 (Apr)',3360,'Bank Transfer','INV-101'),
     (D(2026,5,29),'Private Client Session','Clients C-001 to C-018 (May)',3640,'Bank Transfer','INV-102'),
     (D(2026,6,12),'Insurance/EAP Referral','EAP referrals x6',390,'Insurance Payment','INV-103'),
     (D(2026,6,30),'Private Client Session','Clients C-002 to C-019 (Jun)',3500,'Bank Transfer','INV-104'),
     (D(2026,7,31),'Private Client Session','Clients C-003 to C-021 (Jul)',3710,'Bank Transfer','INV-105'),
     (D(2026,9,18),'Workshop/Training','Grief workshop',600,'Bank Transfer','INV-106'),
     (D(2026,9,30),'Private Client Session','Clients C-004 to C-024 (Sep)',3920,'Card Payment','INV-107'),
     (D(2026,10,30),'Private Client Session','Clients C-005 to C-026 (Oct)',4060,'Card Payment','INV-108')]
exp=[(D(2026,4,1),'Therapy Room Rental','Room hire Apr-Oct',2450,'Yes','Yes - fully'),
     (D(2026,4,15),'Clinical Supervision','Monthly supervision',630,'Yes','Yes - fully'),
     (D(2026,5,2),'Professional Insurance','Indemnity cover',140,'Yes','Yes - fully'),
     (D(2026,5,20),'Professional Body Fees','Annual membership',195,'Yes','Yes - fully'),
     (D(2026,7,9),'CPD / Training','Trauma CPD course',420,'Yes','Yes - fully'),
     (D(2026,8,3),'Software / Tools','Notes and booking app',180,'Yes','Yes - fully')]
new=(D(2026,11,17),'Private Client Session','Client C-027',75,'Card Payment','INV-109')
B,C,Dd,E,F,G=0,1,2,3,4,5
steps=[{},{'B':new[B]},{'B':new[B],'C':new[C]},{'B':new[B],'C':new[C],'D':'Client'},
       {'B':new[B],'C':new[C],'D':new[Dd]},{'B':new[B],'C':new[C],'D':new[Dd],'E':new[E]},
       {'B':new[B],'C':new[C],'D':new[Dd],'E':new[E],'F':new[F],'G':new[G]}]
only=[int(a) for a in sys.argv[2:]] or range(len(steps))
for i in only:
    st=steps[i]
    wb=openpyxl.load_workbook(SRC)
    p=wb['Profile']; p['B6']='Dr Jamie Ellis'; p['B9']='Integrative counselling, private practice'; p['B12']='2026/27'; p['B15']=30000
    ws=wb['Income Tracker']
    for k,row in enumerate(inc):
        r=5+k
        for col,v in zip('BCDEFG',row): ws[f'{col}{r}']=v
    r=5+len(inc)
    for col,v in st.items(): ws[f'{col}{r}']=v
    we=wb['Expense Tracker']
    for k,row in enumerate(exp):
        for col,v in zip('BCDEFG',row): we[f'{col}{5+k}']=v
    for s in wb.worksheets:
        s.page_setup.orientation='landscape'; s.page_setup.fitToWidth=1; s.page_setup.fitToHeight=0
        s.sheet_properties.pageSetUpPr.fitToPage=True
    wb['Income Tracker'].print_area='A1:H16'
    wb['Tax Summary'].print_area='A1:E34'
    wb['Expense Tracker'].print_area='A1:G14'
    wb.active=wb.sheetnames.index('Income Tracker')
    f=f'{OUT}/s{i}.xlsx'; wb.save(f)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',OUT,f],capture_output=True)
    for q in glob.glob(f'{OUT}/s{i}-*.png'): os.remove(q)
    subprocess.run(['pdftoppm','-r','400','-png',f'{OUT}/s{i}.pdf',f'{OUT}/s{i}'])
    print(i, sorted(os.path.basename(q) for q in glob.glob(f'{OUT}/s{i}-*.png')))
