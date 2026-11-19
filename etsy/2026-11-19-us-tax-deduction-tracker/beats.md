# US Self-Employed Tax Deduction and Quarterly Tax Tracker: how it beats the benchmark

Benchmark: HeyMorning "Ultimate Tax Deduction" tracker, https://www.etsy.com/listing/1832554436. Bestseller, 41 reviews, £8.55. 10 photos and a 15 s video.
Benchmark slot order: 1 hero (big title, laptop, round badges) · 2 what's included (6 tabs) · 3 log your deductions · 4 track your mileage · 5 annual dashboard ·
6 multi-year dashboard · 7 tax form dashboard · 8 ready for your accountant · 9 designed to fit your needs (Excel 365 + Sheets) · 10 video walkthrough and reviews.
Our slot order (the brief's recipe): 1 hero · 2 what's included · 3 log your deductions · 4 track your mileage · 5 quarterly tax (4 due-date cards) · 6 annual dashboard ·
7 Schedule C summary · 8 ready for your accountant · 9 monthly check-in + works in Excel and Google Sheets · 10 how it works in 3 steps + 5 reasons to buy from us.

## Competitor check (top 3)
| Listing | Proof | Gap we fill |
|---|---|---|
| HeyMorning Tax Deduction Tracker | Bestseller, 41 reviews, £8.55 | Deductions and mileage only. No quarterly estimated tax, no SE tax, no safe harbor. Its photo 2 says "Only works with Microsoft 365". Reviews: beginners got lost, no written instructions. |
| PrioriDigitalStudio tax deduction tracker | 13 reviews, £7.98 | Deduction log only. No 1040-ES dates or tax estimate. |
| HeyOrganized (new) | No reviews yet | Same deduction-tracker format. |
Keyword demand (16 Nov research): tax deductions 49,500 searches / 609 Etsy listings; self employed taxes 33,100 / 217; schedule c 33,100 / 2,676;
estimated taxes 18,100 / 99; mileage tracker 6,600 / 1,284; quarterly tax 5,400 / 252.

## 8 ways ours beats the benchmark
1. **Works in Microsoft Excel and Google Sheets.** The benchmark says "Only works with Microsoft 365", which is where the "doesn't work with my Excel version" complaint comes from. We use Excel 2016 functions only (no FILTER, SORT, UNIQUE, XLOOKUP or LET) and no macros. Checked with a LibreOffice round trip: 0 errors, 0 changed figures.
2. **Quarterly estimated tax is built in.** The four 1040-ES due dates for 2026 and 2027, a safe-harbor target (100% or 110% of last year's tax, or 90% of this year's), the amount to pay each quarter with catch-up if one was short, a payment log and a tax savings pot. The benchmark has none of this.
3. **Real US tax figures.** Self-employment tax at 15.3% on 92.35% of profit, capped at the 2026 Social Security wage base ($184,500, or $192,300 for 2027). Half the SE tax is deducted. The federal income tax estimate uses the 2026 or 2027 brackets, the standard deduction for your filing status and the QBI deduction. There is an optional state %. Hand-checked against a separate Python calculation: SE tax, taxable income, income tax and the safe-harbor amount all match.
4. **Schedule C line numbers, not made-up categories.** 27 dropdown choices, each tied to its line (4, 8 to 27b). The Schedule C tab shows lines 1 to 31 in the wording of the current form. The mileage tab answers Part IV (lines 43 to 47).
5. **IRS mileage rate picked by trip date.** 72.5 cents to Jun 30, 2026 and 76 cents from Jul 1, 2026 (IRS Notice 2026-10 and Announcement 2026-11). Both rates sit in one editable cell each. The benchmark makes you type your own rate.
6. **Paste a CSV of invoices.** Text dates and "$1,250.00" amounts are read for you. Rows can go in any order, and the list on the right sorts itself (newest first). It also totals by client and flags which clients should send a 1099-NEC (the new $2,000 threshold).
7. **One tax-year dropdown.** It switches the logs, due dates, brackets, mileage rate and wage base together. There are no start and end dates to get wrong, which was a benchmark complaint.
8. **Never lost setting up.** A written 5-step Start Here tab, a filled EXAMPLE file (Jordan, a freelance UX designer) and a BLANK file. The README also covers both the Excel and the Google Sheets steps.
Also: a Monthly Money Check-in that writes the month in plain words (behaviour layer). It is a feature only and is not named in the title, tags or the first line.

## Why this is not a clone of our own listings
- 4480979288 Self Employed Quarterly Tax Estimator: a generic estimator, not built on US forms. This tracker uses US forms: Schedule C lines, 1040-ES dates, safe harbor, SE tax at the SSA wage base and IRS brackets.
- 4475265519 Self Employed Expense Tracker: generic expense categories. This tracker maps each expense to a Schedule C line, applies IRS mileage and the 50% meals rule, and puts the figures into a tax estimate.
- 4467642534 Self Employed Income Spreadsheet: tracks income only. Here, income is just one tab that feeds the 1099 check and the quarterly tax.
The US twist (Schedule C lines, 1040-ES dates, safe harbor, mileage at the IRS rate, SE tax) is what makes it different. It sits in the same Self-Employed Finance section and cross-sells the Expense Tracker.

## Sources (checked 19 Nov 2026)
IRS 2025 Schedule C instructions (irs.gov/instructions/i1040sc) · IRS IR-2025-128 / Notice 2026-10 (72.5 cents) · IRS Announcement 2026-11 via CPA Practice Advisor (76 cents from Jul 1, 2026) ·
SSA wage base $184,500 (2026) and $192,300 (2027), via the Journal of Accountancy and APA · IRS IR-2025-103 / Rev. Proc. 2025-32 and Tax Foundation 2026 brackets ·
Rev. Proc. 2026-35 via Tax Foundation and CPA Practice Advisor (2027 brackets) · OBBBA 1099-NEC $2,000 threshold.
