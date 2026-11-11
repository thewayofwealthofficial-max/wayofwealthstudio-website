import json, re
title = "Couples Money Year in Review Spreadsheet, 2027 Financial Goals Planner Google Sheets Excel, Annual Budget Review, Monthly Check In Tracker"
tags = ["couples budget", "year in review", "couples goals 2027", "financial goals", "annual budget review", "new year money", "money date",
        "couples finance", "net worth tracker", "goal tracker sheet", "january reset", "joint finances", "money planner 2027"]
desc = """Look back at your money year together, then plan the next one. Six short steps, one tab each: your year in numbers, where the money went (and whether it was worth it), net worth start vs end, eight look-back questions, 3 to 5 shared goals, and a monthly check-in for each goal.

See more of our Couples Finance tools here: https://www.etsy.com/shop/WayofWealthStudio?section_id=57077407
See the rest of our shop here: https://www.etsy.com/shop/WayofWealthStudio
Start the talk with our best seller, the Couples Money Conversation Starter: https://www.etsy.com/listing/4478858153
Go deeper with our Couples Money Mindset Workbook: https://www.etsy.com/listing/4461192508

WHAT WE FIXED FROM OTHER PLANNERS
- Your own file, not a web app: works in Google Sheets or Excel, no new app or sign-up
- The whole year: all 12 months, not one sample month
- One step per tab, so it never gets complicated
- Every formula tested (0 errors), locked in Excel so sums can't break

WHAT'S INSIDE
- Dashboard: 8 headline numbers, 5 charts, 3 summary tables
- 10 tabs incl. a goal reality check and a 30-minute money date agenda
- Example copy (filled in) and a blank copy
- 11 printable pages, A4 and US Letter
- README with setup steps

DETAILS
- Any currency, works anywhere
- Instant digital download, nothing is posted
- Questions: joel@wayofwealthcoaching.com

Made by Joel (MSc Behavioural Economics). Photos show the real files; the desk background in photos 1 and 7 was made with AI. General information, not financial advice."""
print(len(title), [w for w in title.split() if re.match(r'^[A-Z]{2}', w)])
print([t for t in tags if len(t) > 20], len(tags))
print(len(re.findall(r"\S+", desc)), 'words')
json.dump({"title": title, "tags": tags, "description": desc, "price": 8.19, "taxonomyId": 12476}, open('copy.json', 'w'), indent=1)
