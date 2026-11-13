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
