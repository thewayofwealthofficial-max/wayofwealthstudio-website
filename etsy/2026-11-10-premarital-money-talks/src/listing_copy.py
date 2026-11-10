import json,re
title="Premarital Money Talks Workbook, Engaged Couples Finance Questions Before Marriage, Fillable PDF Printable, Wedding Budget Money Agreement"
tags=["premarital workbook","engaged couple gift","marriage money talk","couples finance pdf","engagement gift","wedding budget plan","newlywed money","bride to be planner","joint account plan","fair bill split","money agreement","premarital questions","couples money date"]
desc="""Most premarital workbooks give money one page. This one is all about money: six short talks that cover what couples most often skip before the wedding, ending in a one-page Money Agreement you both sign.

Answer on your own first (Partner A, Partner B), then fill in the "together" part. One page per step, about 30 to 45 minutes a talk.

See more of our Couples Finance tools here: https://www.etsy.com/shop/WayofWealthStudio?section_id=57077407
See the rest of our shop here: https://www.etsy.com/shop/WayofWealthStudio
Go deeper on money habits with our Couples Money Mindset Workbook: https://www.etsy.com/listing/4461192508
Start with our No. 1 seller, the Couples Money Conversation Starter: https://www.etsy.com/listing/4478858153

WHAT'S INSIDE (18 pages)
- Start here how-to page and a six-talk plan
- Talk 1: our money stories and what money means to us
- Talk 2: income, savings, credit and a table of everything you each owe
- Talk 3: joint, separate or hybrid accounts, plus a fair-split worksheet (50/50 or by income, sums shown step by step)
- Talk 4: wedding budget, who pays, each partner's top 3
- Talk 5: children, career breaks, family support, home and retirement
- Talk 6: Money Agreement and a 12-month money date tracker
- When we disagree guide, 20 quick questions, notes

DETAILS
- Fillable PDF (type on a laptop, tablet or phone) plus print-friendly versions
- A4 and US Letter, any currency, no currency signs printed
- README with how-to steps
- Instant digital download, nothing is posted
- Questions: joel@wayofwealthcoaching.com

Made by Way of Wealth Studio, run by Joel (MSc Behavioural Economics). Photos show the real pages. The desk background in photo 1 was made with AI; the workbook pages on it are real. General information, not financial or legal advice."""
print(len(title), [w for w in title.split() if re.match(r'^[A-Z]{2}',w)])
print([t for t in tags if len(t)>20], len(tags))
print(len(re.findall(r"\S+",desc)),'words')
json.dump({"title":title,"tags":tags,"description":desc},open('copy.json','w'))
