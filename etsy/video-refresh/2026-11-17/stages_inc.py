import openpyxl, datetime as dt, subprocess, os, sys, glob
V=os.path.dirname(os.path.abspath(__file__)); SRC=V+'/incfix/Self_Employed_Income_Tax_Tracker.xlsx'; OUT=V+'/s'
base=[(dt.date(2026,1,14),'Harper & Co rebrand','Client Work','INV-101',1800),
      (dt.date(2026,2,3),'Monthly retainer - Bloom','Retainer','INV-102',950),
      (dt.date(2026,3,22),'Template shop sales','Product Sales','-',420),
      (dt.date(2026,4,9),'Strategy call - Nova','Consulting','INV-103',600),
      (dt.date(2026,5,18),'Website refresh - Oak','Client Work','INV-104',2400),
      (dt.date(2026,7,2),'Monthly retainer - Bloom','Retainer','INV-105',950)]
new=(dt.date(2026,11,17),'Logo project - Ember','Client Work','INV-106',1500)
steps=[{},{'B':new[0]},{'B':new[0],'C':'Logo project'},{'B':new[0],'C':new[1]},{'B':new[0],'C':new[1],'D':new[2],'E':new[3]},{'B':new[0],'C':new[1],'D':new[2],'E':new[3],'F':new[4]}]
for i,st in enumerate(steps):
    wb=openpyxl.load_workbook(SRC)
    ws=wb['Income Log']
    for k,(d,c,cat,inv,amt) in enumerate(base):
        r=5+k; ws[f'B{r}']=d; ws[f'C{r}']=c; ws[f'D{r}']=cat; ws[f'E{r}']=inv; ws[f'F{r}']=amt
        ws[f'B{r}'].number_format='d mmm yyyy'
    r=5+len(base)
    for col,v in st.items():
        ws[f'{col}{r}']=v
    ws[f'B{r}'].number_format='d mmm yyyy'
    wb['Setup']['C5']='Alex Morgan'
    for s in wb.worksheets:
        s.sheet_state='visible'
        s.page_setup.orientation='landscape'; s.page_setup.fitToWidth=1; s.page_setup.fitToHeight=0
        s.sheet_properties.pageSetUpPr.fitToPage=True
    wb['Income Log'].print_area='A1:K16'
    wb['Dashboard'].print_area='A1:G40'
    wb.active=wb.sheetnames.index('Income Log')
    f=f'{OUT}/s{i}.xlsx'; wb.save(f)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',OUT,f],capture_output=True)
    for p in glob.glob(f'{OUT}/s{i}-*.png'): os.remove(p)
    subprocess.run(['pdftoppm','-r','200','-png',f'{OUT}/s{i}.pdf',f'{OUT}/s{i}'])
    print(i, sorted(os.path.basename(p) for p in glob.glob(f'{OUT}/s{i}-*.png')))
