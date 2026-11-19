# Video refresh, 19 Nov 2026 (review rounds 1 and 2 applied)

## Round 2 changes
- The old listing photo 1 is gone, because its tablet showed numbers that are not in the real file.
- Both videos now open and close on a house-style title card. It has a cream background, the Playfair product name, a gold italic line and a real dashboard render, shown large:
  - Spending: the whole Total Spent card ($357.23) from the fixed EXAMPLE file.
  - Workbook: the whole Total Impulse Spend card ($120.00) from the fixed tracker's own sample data.
- The footer is now "WAY OF WEALTH STUDIO" in Playfair at 42 px, with a cap height of about 30 px.
- Workbook: the page turn is now a hard cut to Module 8.
- Workbook: the Module 3 crop has 60 px of page below the last answer line.
- Spending: on the blank file, the dashboard's ADHD Insight (F5) used to say "Your impulse rate is low — great pattern awareness." It now says "Log a few purchases and your pattern will show here." until something is logged. The fixed zip was rebuilt, and all three xlsx files recalc with 0 errors.
- Workbook video: 14.83 s, 331,667 bytes. Spending video: 14.17 s, 316,489 bytes.
- textcheck, one frame every 1 s:
  - Workbook: t = 0-14 gave 38, 33, 31, 31, 31, (113, a blue circle merges three lines into one band), 50, 32, 51, 57, 48, 41, 38, 41, 41.
  - Spending: t = 0-13 gave 54, 33, 33, 34, 44, 44, 32, 32, 43, 43, 54, 54, 54, 54.
- I checked every 0.5 s frame by eye: no cut words and no overlaps.


Both videos are 1080x1080, H.264 (yuv420p), 30 fps, silent (no audio stream), crf 24. They use the same look as the 17 and 18 Nov videos: a Playfair headline and a gold italic line above the screen on every step, a rounded screen and gold boxes. Nothing on Etsy, Drive or Gmail was changed.

## Round 1 changes
- Every table view shows whole columns only, with no partial-column pans.
- The screen is at most 980 px wide. That leaves at least 50 px of margin on each side, and the gold box stays at least 44 px from the frame edge.
- Every change of view is a hard cut. There are no cross-fades, so no headlines overlap.
- The only animated move is the workbook's page turn (0.5 s). Its headline switches at the start, so two headlines never overlap. During the turn, the page is squeezed sideways; no words are cropped.
- The dashboards now show the real KPI cards in place. Each frame zooms on one whole card (a whole merged cell). Nothing is rearranged.

## ADHD Money Management Workbook 4474743614 - video NEW.mp4
14.67 s, 536,954 bytes (0.54 MB).
1. Photo 1 (1.0 s).
2. Module 3, p11 of the real PDF, rendered at 400 dpi. Three answers are typed onto the page's own blank lines: "Late at night, in bed", "My phone" and "Tired, or a social ad". They then get a gold box.
3. Page turn to Module 8, card 3 (p20). The answers "1 hour", "24 hours" and "72 hours" are typed in, "Yes" is circled and the answers get a gold box.
4. The Impulse Spend Log in the FIXED tracker. LibreOffice renders each step, so the formulas recalculate. A new row is typed in step by step:
   - Columns A:B show the date, then "Trainers", then "Trainers — 1am scroll".
   - Columns C:D show $59.00. Then the Trigger list opens with all 9 of the file's options, and Tired is picked.
   - Column E shows "Yes - Waited 24hrs".
   - Columns F:G show Still Bought "Yes", then Regret 2.
5. The dashboard KPI row, before and after:
   - The Impulse Purchases card goes from 3 to 4.
   - The Total Impulse Spend card goes from $120.00 to $179.00.
   - Both are boxed in the after frame.
6. Photo 1.

## ADHD Spending Tracker 4483114999 - video NEW.mp4
14.07 s, 411,623 bytes (0.41 MB). The demo profile is Maya with $2,800, and the log has 9 example purchases. One new impulse purchase is typed in, and each step is rendered with LibreOffice.
1. Photo 1 (1.3 s).
2. The Spending Log, columns B:C, rows 5-15.
3. Columns B:C: the date, then "Wireless", then "Wireless earbuds".
4. Columns D:E: $39.99, then Online Shopping.
5. Columns F:G:
   - The Impulse? list opens with the file's own options (Planned / Impulse / Semi-Impulse), and Impulse is picked.
   - Then Satisfaction is set to 2.
6. Column H: "11pm, bored," then "11pm, bored, saw an ad".
7. Column I: the Pattern Note formula fills in "Low satisfaction impulse — check your trigger", which is boxed.
8. Dashboard: the whole Total Spent card goes from $317.24 to $357.23, boxed in the after frame.
9. Photo 1.

## Self-check
I looked at contact sheets every 0.5 s for words cut at a frame or screen edge and found none. textcheck.py measures the smallest ink line height on the screen, one frame every 1 s. It ignores bands under 12 px, which are bullets and rules.
- **Workbook:** t = 1-13 s gave 33, 32, (page turn), 36, (113, a blue circle merges three lines into one band), 50, 48, 51, 57, 48, 41, 41, 41. t = 0 and t = 14 are photo 1.
- **Spending:** t = 1-12 s gave 33, 33, 34, 44, 44, 32, 32, 43, 43, 54, 54, 54. t = 0 and t = 13 are photo 1.
- **Smallest steady text:** 32 px.

## Product bugs found while filming and fixed (fix_products.py, run on the original download)
The fixed zips sit in this folder and use the same file names inside as the originals. LibreOffice recalc shows 0 errors on every file: 25 formulas in the companion tracker and 176 in each of the spending blank and EXAMPLE files. Data validations, conditional formats and charts are all kept.

**ADHD_Money_Companion_Tracker.xlsx** ("ADHD Money Management Workbook 4474743614 - FIXED download file.zip". The PDF and README are unchanged.)
1. The Dashboard bar chart (D14:I37) covered half of the pie (D6:I29) and the section headings. The charts now sit at F7:K21 and F23:K44.
2. The pie labels read "No - Avoided; Count; 1; 20%". They now show the category and percent only.
3. Dashboard column A cut off the trigger names ("Dopamine Chas"). It is now width 22.
4. Dashboard G4, Total Impulse Spend, also counted purchases marked "No - Resisted" or "Returned It". It is now =SUMIF('Impulse Spend Log'!F5:F100,"Yes",'Impulse Spend Log'!C5:C100).
5. The empty log rows were fixed at 15 pt, which cut wrapped entries in half. Impulse Spend Log rows 8-100 and Money Task Log rows 10-150 are now 27.75 pt.
6. "Wednesday" and "Completed?" wrapped in the Money Task Log. Column B is now width 12 and column E width 13. Impulse Spend Log column E is now width 20, because "Did Not Think To" filled the cell edge to edge.
7. The Dashboard KPI card labels in row 3 were 9 pt. They are now 11 pt, and the row is now 18 pt.

**ADHD_Spending_Tracker.xlsx** ("ADHD Spending Tracker 4483114999 - FIXED download file.zip". The README is unchanged.)
1. The Spending Log Pattern Note (column I, width 20) showed only its middle line. The column is now width 40, so every note fits on one line.
2. The "Spending by Category" chart covered the Satisfaction Insights table. The chart now starts at B41.
3. Profile column C cut off the dropdown answers. Columns C and D are now widths 42 and 50.
4. NEW: the listing promises an "Example Spreadsheet with sample data", but the zip had only the blank file. The zip now also holds ADHD_Spending_Tracker_EXAMPLE.xlsx (make_example.py). It is the fixed file with:
   - a filled Profile (Maya, $2,800, Online Shopping, Dopamine Shopping);
   - the 10 demo purchases from the video;
   - one Mindset Check week.

## Not changed
- The live title of 4483114999 ends ", MSc Economist", which differs from the brief.
- Both trackers use $ labels.

## Rebuild
1. Run `pdftoppm -r 400` on PDF pages 11 and 20 to work/pg/h-11.png and work/pg/h-20.png.
2. Run `fix_products.py`, then `make_example.py`, render the EXAMPLE file's Dashboard (A1:F12) to work/ex/sp with render.py, then run `stages_spend.py`, `stages_wb.py`, `video_spend.py` and `video_wb.py`.
3. Check the text sizes with `textcheck.py <mp4> <dir> 0`.

The work/ folder was deleted after the build.
