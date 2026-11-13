import sys; sys.path.insert(0,'/home/claude/wayofwealthstudio-website/etsy/lib'); import stages
src='/home/claude/wayofwealthstudio-website/etsy/2026-11-12-self-employed-couples-budget/src/out/sample.xlsx'
W='/home/claude/work/secouples/vid/stg'
H=('Income Log','H19',3350); C=('Income Log','C19',6400); D=('Income Log','D19',450)
steps=[[H],[H,C],[H,C,D]]
for i,e in enumerate(steps): print(stages.stage(src,e,f's{i}',[4],W,dpi=300))
print(stages.stage(src,steps[0],'d0',[1],W,dpi=600)); print(stages.stage(src,steps[2],'d3',[1],W,dpi=600))
