import openpyxl, datetime as dt, subprocess, os, glob
V=os.path.dirname(os.path.abspath(__file__)); SRC=V+'/exp/Self_Employed_Expense_Tracker.xlsx'; OUT=V+'/se'
base=[(dt.date(2026,1,8),'Software & Subscriptions','Design software, yearly plan',240,'Credit Card'),
      (dt.date(2026,2,12),'Office Supplies','Printer ink and paper',46,'Debit Card'),
      (dt.date(2026,3,3),'Marketing & Advertising','Business cards, 500',58,'PayPal'),
      (dt.date(2026,5,20),'Travel & Transport','Train to client workshop',72,'Debit Card'),
      (dt.date(2026,7,14),'Professional Development','Online pricing course',150,'Credit Card'),
      (dt.date(2026,9,2),'Insurance','Public liability, annual',95,'Bank Transfer')]
new=(dt.date(2026,11,17),'Equipment','New laptop stand and keyboard',135,'Credit Card')
steps=[{},{'B':new[0]},{'B':new[0],'C':new[1]},{'B':new[0],'C':new[1],'D':'New laptop stand'},{'B':new[0],'C':new[1],'D':new[2]},{'B':new[0],'C':new[1],'D':new[2],'E':new[3],'F':new[4]}]
for i,st in enumerate(steps):
    wb=openpyxl.load_workbook(SRC); ws=wb['Expense Log']
    for k,(d,c,desc,amt,pm) in enumerate(base):
        r=5+k; ws[f'B{r}']=d; ws[f'C{r}']=c; ws[f'D{r}']=desc; ws[f'E{r}']=amt; ws[f'F{r}']=pm
    r=5+len(base)
    for col,v in st.items(): ws[f'{col}{r}']=v
    for s in wb.worksheets:
        s.page_setup.orientation='landscape'; s.page_setup.fitToWidth=1; s.page_setup.fitToHeight=0; s.sheet_properties.pageSetUpPr.fitToPage=True
    ws.print_area='A1:H16'; wb['Dashboard'].print_area='A1:H30'; wb['Tax Summary'].print_area='A1:G26'
    f=f'{OUT}/s{i}.xlsx'; wb.save(f)
    subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',OUT,f],capture_output=True)
    for p in glob.glob(f'{OUT}/s{i}-*.png'): os.remove(p)
    subprocess.run(['pdftoppm','-r','100','-png',f'{OUT}/s{i}.pdf',f'{OUT}/s{i}'])
print(sorted(os.path.basename(p) for p in glob.glob(f'{OUT}/s5-*.png')))
