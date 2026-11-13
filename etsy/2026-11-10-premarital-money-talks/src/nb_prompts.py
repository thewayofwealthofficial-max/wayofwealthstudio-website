import sys, json
sys.path.insert(0,'/home/claude/nbkit'); import nb
R='/home/claude/refs/mit/'
S={
'01':("Headline on two lines: 'Premarital Money Talks' and 'Workbook'. Gold italic subtitle: '6 money conversations to have before I do'. "
 "Below: one large tablet in PORTRAIT orientation on the left-centre, and one smartphone in portrait on the right, NOT overlapping, with a gap between them, both with green screens, on a cream surface with a small sprig of white flowers and two gold wedding rings beside them. "
 "Top right a round gold seal badge with the text '18 PAGES'. Bottom row: three small gold line icons with short dark captions: 'Fillable + printable', 'A4 and US Letter', 'Any currency'.", [R+'01.jpg',R+'03.jpg']),
'02':("Headline: 'Everything That's Included'. Gold italic subtitle: '18 pages. Six talks. One money agreement.' Below, a neat vertical list of 8 cream rounded boxes with thin gold borders, each with a small gold line icon on the left, a bold serif name and a short italic description on the right: "
 "1 'Start Here' - 'How to use it and your talk plan'; 2 'Money Stories' - 'What money meant growing up'; 3 'Where We Stand' - 'Income, savings and debts'; 4 'Banking Together' - 'Joint, separate or hybrid'; 5 'Fair Split' - '50/50 or by income'; 6 'The Wedding' - 'Budget and who pays'; 7 'Family and Future' - 'Children, home, retirement'; 8 'Money Agreement' - 'Signed by both of you'. No devices on this image.", [R+'02.jpg',R+'10.jpg']),
'03':("Headline: 'Joint, Separate or Hybrid?'. Gold italic subtitle: 'Choose how you will bank together'. One large tablet in PORTRAIT orientation in the centre filling most of the height, green screen, on a cream surface. "
 "Two gold rounded label callouts with white sans text and a short dark description underneath, each with a thin gold line ending in a gold dot touching the tablet screen: left 'Three options' / 'Good points and watch-outs'; right 'Your reasons' / 'Each of you writes why'.", [R+'03.jpg',R+'06.jpg']),
'04':("Headline: 'A Fair Split, Worked Out'. Gold italic subtitle: '50/50 or by income, step by step'. One large tablet in PORTRAIT orientation in the centre filling most of the height, green screen, beside a cup of coffee. "
 "Two gold rounded label callouts with white sans text and a short dark description underneath, each with a thin gold line ending in a gold dot on the screen: left 'By income' / 'Same share of what you earn'; right 'Fun money' / 'Agreed before the bills'.", [R+'04.jpg',R+'03.jpg']),
'05':("Headline: 'Plan the Wedding Without the Fight'. Gold italic subtitle: 'Agree the budget before you fall for a venue'. One large tablet in PORTRAIT orientation in the centre filling most of the height, green screen, with a small bouquet of white flowers beside it. "
 "Two gold rounded label callouts with white sans text and a short dark description underneath, each with a thin gold line ending in a gold dot on the screen: left 'Your budget' / 'Savings and family help'; right 'Top 3 each' / 'Spend on what matters'.", [R+'06.jpg',R+'03.jpg']),
'06':("Headline: 'Your Money Agreement'. Gold italic subtitle: 'One page you both sign'. Two tablets in PORTRAIT orientation side by side with a clear gap between them, NOT overlapping, both green screens, on a cream surface with two gold rings. "
 "Two gold rounded label callouts with white sans text and a short dark description underneath, each with a thin gold line to a tablet: left 'Signed by both' / 'Your rules in one place'; right 'Money dates' / 'A check-in every month'.", [R+'08.jpg',R+'03.jpg']),
'07':("Headline: '20 Quick Questions for Date Night'. Gold italic subtitle: 'For a road trip, a walk or dinner out'. One large tablet in PORTRAIT orientation in the centre filling most of the height, green screen, beside two glasses of wine on a cream table. "
 "Below the tablet, a rounded cream pill box with thin gold border containing gold italic serif text: 'Saver or spender? Rent or buy? What does comfortable mean to you?'", [R+'07.jpg',R+'01.jpg']),
'08':("Headline: 'Start Tonight in 3 Steps'. Below it, three gold circles numbered 1, 2, 3 in white serif, joined by thin gold arrows, each with a bold sans label and a short serif line under it: 1 'DOWNLOAD' / 'Type in the PDF or print it'; 2 'TALK' / 'One talk a week, 30 to 45 minutes'; 3 'AGREE' / 'Sign your Money Agreement'. "
 "Below the steps, one tablet in PORTRAIT orientation in the centre, green screen. Under the tablet, gold italic serif line: 'Instant download. Nothing is posted.'", [R+'09.jpg',R+'01.jpg']),
'09':("Headline: '5 Reasons to Buy From Us'. Gold italic subtitle: 'Why couples choose Way of Wealth Studio'. Below, five cream rounded boxes with thin gold borders stacked vertically, each with a gold circle check-mark icon on the left, a bold serif line and a short gold italic line under it: "
 "'Made by a qualified financial planner' / 'MSc Behavioural Economics, not a template shop'; 'All about money' / 'Six full talks, not one page'; 'Type it or print it' / 'Fillable PDF plus print versions'; 'A4 and US Letter' / 'Any currency, any country'; 'Yours to keep' / 'Instant download. No subscription, no app.' No devices on this image.", [R+'10.jpg',R+'02.jpg']),
}
if __name__=='__main__':
    for k in sys.argv[1:]:
        p,refs=S[k]; nb.gen(nb.STYLE+p, refs, f'raw/s{k}.png')
