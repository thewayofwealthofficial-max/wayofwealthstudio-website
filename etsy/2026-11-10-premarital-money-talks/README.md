# Premarital Money Talks Workbook (Etsy build, 10 Nov 2026)

Built by Fred (Etsy Operations) on 10 Nov 2026. Draft listing 4614109943 created 10 Nov 2026 (catch-up run) after a fresh review passed 7 of 7. GBP 8.59,
Couples Finance. Photos uploaded from photos/ here; zip and video saved in Drive (Ready to upload).

- `Premarital Money Talks Workbook.zip`: the product file (A4 + US Letter, fillable + print, README)
- `Premarital Money Talks Workbook - video.mp4`: listing video
- `photos/01.jpg`-`09.jpg`: listing photos in order (photo 1 desk background made with AI, disclosed in the description)
- `src/`: build scripts (`python3 build.py out`, `readme.py`, `imgs.py`, `video.py` need out/, hi/, hie/ renders; see scripts)

## Full rework, 13 Nov 2026 (house style)
- Photos 01-09 rebuilt with Nano Banana Pro (scene only, green screens) + real PDF pages composited (`src/nb_prompts.py`, `src/nb_comp.py`, kit `../lib/nb.py`). Slot order from AHappySpaceCo's Premarital Counseling Workbook (listing 1425626111): cover with page count, what's included, features, how-to, why us.
- Video rebuilt: fillable PDF being typed in (fair split, then the Money Agreement), 14.2 s (`src/video_inuse.py`).
- Product unchanged (18 money-only pages already deeper on money than the general premarital bestsellers); description updated (`src/copy.json`).
- Round 2 (13 Nov): screens re-composited with filled masks (no green fringe), pages fitted inside the screens, callout dots redrawn onto the right boxes (`src/nb_comp2.py`); sample answers on the banking, wedding and plan pages; 50/50 vs by-income and joint/separate/hybrid are now radio groups in the fillable PDF (zip rebuilt); video recropped.
- Round 3 (13 Nov, no new AI images): clean rounded screen masks; screens show the page content plus the top of the next page like a PDF viewer (`src/nb_comp3.py`); more sample answers (Talk 1, Talk 5, money dates); serif footer wordmark on every photo, quote marks on the cover subtitle, photo 04 callout text corrected to "Set after bills and savings" (`src/nb_post.py`).
- Round 4 prep (13 Nov): radio groups use ReportLab's square appearance (centred tick, no stray circle), zip rebuilt; video ticks 'We'll split by income' and the agreement crop stops above 'If we disagree'; photo 01 phone shows the fair-split page from the top.
