# Gates and standards for reviewers

## QUALITY GATES (reviewer grades each PASS/FAIL)
1 Competitor check vs the top 3. 2 Density: dashboard 6+ KPI cards, 4+ charts, data tables (PDF: equivalent depth). 3 Side-by-side: a buyer would choose ours over the best competitor; AT LEAST 5 specific written ways ours beats the benchmark (fewer than 5 = FAIL). 4 Formulas: recalc shows 0 errors. 5 Listing assets: photos follow the winning recipe slot by slot, 5+ photos, 2 infographics, real product on every screen; video = real product in use like the benchmark's video. 6 Copy: full 140-char title, 13 tags, description under 300 words with the 4 links, price on the ladder, works worldwide (or marked UK-only). 7 Unique, safe and proven: not a clone of anything in our shop, real competitor sales evidence. 8 Google Sheets renders correctly. 9 Nano Banana house style vs Moving In Together: not flatter/paler/less polished, no copied or fake text, no green left, every screen the real product; video readable on a phone.


## BEHAVIOUR LAYER — required on every NEW spreadsheet and every full rework of a spreadsheet (Joel, 17 Nov evening)
Add a "Monthly Money Check-in" tab:
 a) a summary box built from formulas that writes the month in plain words in ONE cell ready to copy (e.g. ="This month we earned "&TEXT(income,"£#,##0")&" and spent "&...), covering income, spending vs plan by category, the biggest overspend, and progress to the goal or debt-free date. Use the buyer's currency setting (build the TEXT format from the currency cell).
 b) 3-5 behavioural reflection questions written for that product's buyer in Joel's coaching style (plain, warm, no jargon), e.g. "Which spend this month felt good, and which do you wish you could take back?", "What was going on the day you overspent?", "What is one small habit you'll try next month?". Pale input boxes next to each for answers. Write them yourself for this buyer.
 c) one optional line under the questions: "Want a second opinion? Copy your summary and these questions into any AI assistant you use (ChatGPT, Gemini, Copilot) and ask it to reply like a kind, honest money coach."
 d) It must work fully with no AI at all.
 ETSY RULE: this tab is a feature, never the product. Never use the words "prompt", "prompt pack", "AI coach" or "ChatGPT" in titles, tags, photo headlines or the first line of the description. The listing may say "monthly money check-in with guided reflection questions". Give it ONE feature photo ("Monthly check-in: see your month in plain words").
 For a PDF product, the equivalent is a printable/fillable "Monthly Money Check-in" page with the same questions (and, if the product includes a spreadsheet, the tab as above).


## Photos (gate 5 + gate 9)
- 8-10 photos, 2000x2000 JPG quality 90, house style = Moving In Together 4613098009 (warm cream studio, big bold Playfair headline in dark brown-black #2A2620, gold italic subtitle #B8956E, gold sparkles, glossy devices, footer 'WAY OF WEALTH STUDIO'). Look at etsy/2026-11-12-moving-in-together-rework/photos/*.jpg before designing.
- Slot order from the benchmark's winning recipe (cover; everything included; 4-6 feature slides with callouts; 3 steps; 5 reasons to buy from us). 2 infographics (what's included / 5 highlights; 5 reasons to buy from us).
- Every device screen shows the REAL product (renders of the real file at 300 dpi via LibreOffice/pdftoppm). 0 pure-green pixels left (nb.green_left == 0). No fake text anywhere. Text readable on a phone. Photo 1: one clear promise.
- Make two side-by-side images for the reviewer: (1) benchmark photo 1-4 vs ours 1-4 (download benchmark images from i.etsystatic.com il_fullxfull URLs with curl; they are for comparison only, never reuse them), (2) ours vs Moving In Together photos 1-4.

## Video (gate 5 + gate 9)
13-15 s, silent, 1080x1080, H.264, under 3 MB (ffmpeg -crf 24 or higher). THE REAL PRODUCT IN USE matching what the benchmark's video shows — never a slideshow of the photos, never AI video. Method: openpyxl copies of the example file with an entry typed in step by step, LibreOffice renders each (formulas recalc), then frames: 1.3 s photo 1, the full tab, zoom into the row being typed, typing steps, pan to the result with a gold box, dashboard before/after with the changed number boxed, photo 1 again. Short Playfair headline + gold italic line above the screen each step. Table text at least 30 px high in the 1080 frame. For a PDF: show the real pages being filled in (typed answers appearing in the fillable fields), page turns, zoom.

