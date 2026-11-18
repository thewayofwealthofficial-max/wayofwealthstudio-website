# Fixes for Therapist SE Tax Tracker (listing 4527554740) - writes a FIXED copy, original untouched
import openpyxl, sys, math, re
from copy import copy
from openpyxl.utils import column_index_from_string as ci, get_column_letter as gl
src,dst=sys.argv[1],sys.argv[2]
wb=openpyxl.load_workbook(src)
t=wb['Tax Summary']; it=wb['Income Tracker']; wel=wb['Welcome']
def style_from(src_row,dst_row):
    for col in 'BCD':
        s,d=t[f'{col}{src_row}'],t[f'{col}{dst_row}']
        d.font=copy(s.font); d.fill=copy(s.fill); d.border=copy(s.border); d.alignment=copy(s.alignment)
        d.number_format=s.number_format; d.protection=copy(s.protection)
# 1 blank file showed "Tax Year: 0"
t['C3']='=IF(Profile!B12="","",Profile!B12)'
it['F3']='=IF(Profile!B12="","",Profile!B12)'
# 2 Class 2 NI was charged on every file (GBP179.40 with zero income); compulsory Class 2 ended 6 April 2024
t['B22']='Class 2 NI (not due since Apr 2024)'
t['C22']=0
t['D22']='Not charged since 6 Apr 2024 (voluntary only)'
# 3 high incomes: personal allowance taper over GBP100k and the 45% additional rate
t['C15']='=MAX(0,12570-MAX(0,C12-100000)/2)'
t['D15']='£12,570, minus £1 per £2 of profit over £100,000'
t['C16']='=MAX(0,C12-C15)'
t['C18']='=MIN(C16,37700)*0.2'
t['B19']='Income Tax — Higher Rate (40%)'
t['C19']='=MAX(0,MIN(C16,125140)-37700)*0.4'
t['D19']='40% on taxable income £37,701 to £125,140'
style_from(20,21)                       # Total moves down one row (row 21 was an empty spacer)
style_from(19,20)
t['B20']='Income Tax — Additional Rate (45%)'; t['C20']='=MAX(0,C16-125140)*0.45'; t['D20']='45% on taxable income above £125,140'
t['B21']='Total Income Tax'; t['C21']='=C18+C19+C20'; t['D21']=None
t['C28']='=C21+C25'
# 4 payments on account: two instalments (31 Jan, 31 Jul), each half of this bill, only when the bill is GBP1,000+
t['B33']='Each Payment on Account (31 Jan & 31 Jul)'
t['C33']='=IF(C28>=1000,C28/2,0)'
t['D33']=("If this year's bill is £1,000 or more, HMRC usually asks for 2 advance payments towards next year "
          "(31 Jan and 31 Jul), each half of this bill (not needed if over 80% was taxed at source).")
# 5 gold amounts were low contrast (#B8956E on white/cream): darker gold #7A5A2E
for ws,a in ((t,'C32'),(t,'C33'),(it,'C3'),(wb['Expense Tracker'],'C3')):
    f=copy(ws[a].font); f.color='FF7A5A2E'; ws[a].font=f
# 6 long wrapped notes were cut off (only 15 pt per row): grow merged rows to fit the text
for ws in wb.worksheets:
    mr={str(m).split(':')[0]:str(m) for m in ws.merged_cells.ranges}
    for row in ws.iter_rows():
        for c in row:
            if not (isinstance(c.value,str) and len(c.value)>60 and not c.value.startswith('=')): continue
            if not c.alignment.wrap_text: continue
            rng=mr.get(c.coordinate,c.coordinate); a,b=(rng.split(':')+[rng])[:2]
            c0,r0=re.match(r'([A-Z]+)(\d+)',a).groups(); c1,r1=re.match(r'([A-Z]+)(\d+)',b).groups(); r0,r1=int(r0),int(r1)
            w=sum((ws.column_dimensions[gl(i)].width or 8.43) for i in range(ci(c0),ci(c1)+1))
            sz=c.font.sz or 11; per=w*1.05*10/sz
            lines=sum(max(1,math.ceil(len(part)/per)) for part in c.value.split('\n'))
            need=lines*sz*1.45+6
            have=sum((ws.row_dimensions[r].height or 15) for r in range(r0,r1+1))
            if need>have:
                for r in range(r0,r1+1): ws.row_dimensions[r].height=round(need/(r1-r0+1),1)
# 7 Tax Summary layout: wrapped notes get room, everything in B:D vertically centred, disclaimer not cut
for r in (12,18,19,20,22,23,28,32): t.row_dimensions[r].height=30
t.row_dimensions[15].height=32
t.row_dimensions[33].height=max(t.row_dimensions[33].height or 15,36)
t.row_dimensions[53].height=30; t.row_dimensions[54].height=30
for r in range(6,34):
    for col in 'BCD':
        c=t[f'{col}{r}']; a=copy(c.alignment); a.vertical='center'
        if col=='B' and r==33: a.wrap_text=True
        c.alignment=a
# 8 Welcome checklist rows 9-13: one even height, ticks centred
for r in range(9,14):
    wel.row_dimensions[r].height=19
    for col in 'BC':
        c=wel[f'{col}{r}']; a=copy(c.alignment); a.vertical='center'; c.alignment=a
# 9 polish: Expense Tracker "Total Expenses:" label was clipped; consistent money format and row heights; header years
wb['Expense Tracker'].column_dimensions['B'].width=17
t['C15'].number_format=t['C16'].number_format
for r in (21,24,25): t.row_dimensions[r].height=30
t['B14']='TAX CALCULATION — 2025/26 and 2026/27 (same thresholds)'
wb.save(dst)
