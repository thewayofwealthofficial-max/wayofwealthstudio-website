# Video refresh, 18 Nov 2026 (review rounds 1 and 2 applied)

Both videos: 1080x1080, H.264 (yuv420p), 30 fps, silent, crf 24. They use the same look as the 17 Nov videos (cream gradient, Playfair 700 headline, gold Playfair italic line, rounded screen with shadow, gold highlight box). Each one starts and ends on the listing's current photo 1, curled from its fullSizeUrl.

## Couples Money Conversation Starter 4478858153 - video NEW.mp4
14.77 s, 765,474 bytes (0.73 MB). Source: the real PDF from Drive, pages rendered with pdftoppm at 400 dpi. No pages were invented.
1. Photo 1 (1.2 s).
2. Real cover (page 1). There are about 29 px of margin around the title.
3. Track 4 prompt cards (page 10): Prompt 1, 2 and 3, each a full close-up, joined with quick cross-fades. There is no five-card overview and no pan.
4. Money Personality Quiz (page 4). The name "Sam" is written letter by letter (S, Sa, Sam) into the real PARTNER A name field. The crop has about 10 px of left padding, then answer (b) is circled and boxed.
5. Prompt 1 card. The buyer's answer appears word by word in blue pen-style ink (Comic Relief) in the card's empty space, then gets a gold box.
6. 30-Day Conversation Calendar (page 11), used as the closing summary. The first hold shows the Week 1 block, cropped at the gap before Week 3 with about 15 px of left padding, and "done" plus a tick are written. A quick cross-fade then shows the Week 2 block, cropped at the gap before Week 4, with a gold box. Nothing is cut mid-sentence and there is no pan.
7. Photo 1.

Note: the PDF has no "agreements" page. The closest real summary page is the 30-Day Calendar, so that is what the video shows.

## Therapist Self Employed Tax Tracker 4527554740 - video NEW.mp4
14.07 s, 781,672 bytes (0.75 MB). Method: openpyxl copies (stages_ther.py) of the FIXED file are filled with example data (profile, 8 income rows, 6 expense rows). One new session is then typed in step by step, and each step is rendered with LibreOffice, so the formulas recalculate.
1. Photo 1.
2. Income Tracker tab.
3. The new row is zoomed and typed in order: date 17/11/2026, then Private Client Session, then "Client", then "Client C-027", then £75.00.
4. Total Income before and after: £23,180.00 becomes £23,255.00. The gold box sits well inside the screen (about 38 px from the bottom edge).
5. Tax Summary before and after. The label cells and amount cells of the real render are stacked so the labels read at about 44 px. Monthly set-aside goes from £142.89 to £144.52 (gold box), and each payment on account goes from £857.35 to £867.10.
6. Photo 1.

## Smallest text measured (ink height of a text line in the 1080 frame)
- 31 px: the cover subtitle and the Income Tracker full-tab rows.
- 33 px: the quiz options and the calendar text.
- 43-46 px: the Tax Summary labels.
- 40-50 px: the cards and the typing zooms.
- The small "WAY OF WEALTH STUDIO" pill printed on the PDF cover is smaller than 30 px. It is decoration, not reading text.

## All product changes (Therapist tracker), in the FIXED zip
File: 4527554740 Therapist Self Employed Tax Tracker - FIXED download file.zip (fixed xlsx + the original README). The changes are scripted in fix_ther.py and applied to the original download.

### Recalc check
LibreOffice recalc (re-run after the last changes) shows 0 errors and no ### on the blank file and on profit tests at £14k, £60k, £110k and £160k. Each test matches a hand calculation:

| Profit | Total tax + NI |
|---|---|
| £14,000 | £371.80 |
| £60,000 | £13,888.60 |
| £110,000 | £36,888.60 (allowance £7,570) |
| £160,000 | £62,659.60 (allowance £0, 45% tax £15,687) |

### Changes
1. Tax Year showed "0" on a blank file. Tax Summary C3 and Income Tracker F3 now use =IF(Profile!B12="","",Profile!B12).
2. Class 2 NI: C22 was =3.45*52 on every file. It is now 0. B22 reads "Class 2 NI (not due since Apr 2024)" and D22 reads "Not charged since 6 Apr 2024 (voluntary only)". Before the fix, a blank file showed a £179.40 tax bill.
3. High incomes:
   - C15 (personal allowance) was a fixed 12570. It is now =MAX(0,12570-MAX(0,C12-100000)/2). D15 reads "£12,570, minus £1 per £2 of profit over £100,000".
   - C16 is now =MAX(0,C12-C15).
   - C18 is now =MIN(C16,37700)*0.2.
   - C19 is now =MAX(0,MIN(C16,125140)-37700)*0.4, with D19 "40% on taxable income £37,701 to £125,140".
   - New row 20: "Income Tax — Additional Rate (45%)" =MAX(0,C16-125140)*0.45, with D20 "45% on taxable income above £125,140".
   - Total Income Tax moved to row 21 (the old empty spacer row) as =C18+C19+C20.
   - C28 is now =C21+C25.
4. Payments on account:
   - B33 changed from "Quarterly Payment on Account" to "Each Payment on Account (31 Jan & 31 Jul)", and it wraps.
   - C33 changed from =IF(C28>0,C28/4,0) to =IF(C28>=1000,C28/2,0).
   - D33 now reads: "If this year's bill is £1,000 or more, HMRC usually asks for 2 advance payments towards next year (31 Jan and 31 Jul), each half of this bill (not needed if over 80% was taxed at source)."
5. Gold amounts had low contrast. Tax Summary C32:C33 and the C3 totals on the Income Tracker and Expense Tracker changed from #B8956E to #7A5A2E.
6. Wrapped notes that were cut off now have taller rows, auto-fitted to their text:
   - Welcome B5 and B24:G25
   - Profile B21:C22
   - Income Tracker B106:G107
   - Expense Tracker B106:F108
   - Mindset Check B5:C6 (the intro was visibly clipped), B9, B29, B39:C40 and B44
7. Tax Summary layout:
   - Rows 12, 18, 19, 20, 22, 23, 28 and 32 are 30 pt.
   - Row 15 is 32 pt.
   - Row 33 is auto-fitted to its note (93 pt).
   - The disclaimer rows 53 and 54 are 30 pt each.
   - All of B:D in rows 6-33 is vertically centred, including rows 16, 19 and 29.
8. Welcome rows 9-13 (the "What's inside" checklist) are one even height of 19 pt. B:C are vertically centred, so the ticks line up.
9. Expense Tracker column B widened from 14 to 17, so the "Total Expenses:" label is no longer clipped. Nothing else shifts badly.
10. Tax Summary C15 now uses the £#,##0.00 format like the other amounts. Rows 21, 24 and 25 are 30 pt to match their neighbours.
11. Tax Summary header B14 changed from "TAX CALCULATION (2026/27 Estimates)" to "TAX CALCULATION — 2025/26 and 2026/27 (same thresholds)". It fits on one line across B:C.

### Is the video still accurate?
The Therapist video was not re-rendered, because none of the values it shows changed:
- Monthly set-aside: £142.89 before and £144.52 after.
- Each payment on account: £857.35 before and £867.10 after. Both bills are over £1,000, so the new rule gives the same figures.
- Total income: £23,180 before and £23,255 after.
I skipped the optional 8 px padding under £867.10, because it would need a full re-render on the new layout.

### README and listing copy
The README PDF does not mention quarterly payments, payments on account or Class 2 NI, so it needs no change.
The live Etsy description does need a change, which I did not make: it says "Class 2 and Class 4 National Insurance" and "quarterly payment on account figures".
