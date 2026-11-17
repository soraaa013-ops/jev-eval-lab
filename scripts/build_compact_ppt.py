"""Create four-slide and one-slide experiment presentations."""
from pptx import Presentation
from pptx.util import Inches, Pt
import build_experiment_ppt as b

_original_text = b.text
def compact_text(*args, **kwargs):
 shape = _original_text(*args, **kwargs)
 for paragraph in shape.text_frame.paragraphs:
  paragraph.space_after = Pt(6)
 return shape
b.text = compact_text

def reset():
 b.prs=Presentation();b.prs.slide_width=Inches(16);b.prs.slide_height=Inches(9)

def save(name):
 p=b.ROOT/'report'/name;b.prs.save(p);print(p)

reset()
s=b.slide('研究设计','三组实验：评什么、怎么评？','不训练模型；让现成模型当评委，把判断与数据集标准标签比较。')
b.table(s,['实验 / 数据','标准标签','评判方法','研究问题'],[
 ['JudgeBench\n350 道回答对','哪份回答更好','二选一；交换位置再评\n每个托管评委 700 次','谁更准？\n是否受位置影响？'],
 ['RewardBench 2\n1,865 条问题','chosen / rejected\n不是人工数值评分','固定 Jev：直接选最好\n或逐个评分后再选','换一种评法\n结果会怎样？'],
 ['AgentProcessBench\n500 条真实轨迹','6,147 个步骤\n均有人工分类标签','Jev / Clef / GPT\n逐步分类 + 最终成败','能否发现\nagent 的错误？']], [3.4,3.4,4.4,3.1],rowh=1.35,fs=21,highlight=2)
b.banner(s,'评的是“评委是否判断正确”，不是让模型重新回答题目或重新执行 agent 任务。')

s=b.slide('Agent方法','Agent 怎么评：完整 trace 输入，每步输出标签','BFCL / tau2 各 250 条轨迹；100 个问题，每题 5 条执行记录。')
b.card(s,.85,2.25,6.9,'模型看到什么？','任务 + 规则 + 工具定义\n完整消息、工具调用与工具返回\n包含被评步骤之前与之后的内容\n人工标签不给模型看',3.7)
b.card(s,8.05,2.25,7.1,'每步怎样判断？','+1：正确并推进任务\n  0：中性或合理探索\n−1：错误、误读证据或违反约束\n未纠正错误会影响依赖它的后续步骤',3.7)
b.text(s,1.05,6.23,13.8,.6,'Jev / Clef 直接选类别；GPT 生成标签与短解释。最后再与人工标签比较。',23,b.NAVY,True)
b.banner(s,'“逐步评分”不是孤立输入单次交互；这是看完完整轨迹后的事后评估。')

s=b.slide('Agent结果','Agent 结果：Jev 领先，但仍漏掉约 66% 错误','永远猜 +1 就有 68.91% 准确率，因此还要看三类宏 F1 与错误召回。')
b.table(s,['评委','宏 F1 ↑','准确率 ↑','错误召回 ↑','错误误报率 ↓'],[
 ['Jev 1.14','50.45%','77.13%','34.35%','2.22%'],['Clef-flash','42.45%','66.15%','16.79%','2.08%'],['GPT-5 mini','37.57%','71.22%','13.45%','1.32%']], [3.3,2.6,2.6,2.8,3.0],rowh=.85,fs=22)
b.text(s,1.05,5.65,13.8,1.15,'宏 F1：三类各算 F1 后等权平均。错误召回：100 个真错误找到几个。\n真实案例：要求在 workspace 内建目录，却建在外面；Jev 看出操作错误，\n但三个评委都没看出后续“已经完成”的声明仍然错误。',22)
b.banner(s,'只证明本轮过程判断更好，尚未证明接入评委能提高 agent 的任务成功率。')
s.notes_slide.notes_text_frame.text += '\n500条中Clef有3条无完整预测，264个缺失步骤按错计；GPT使用low reasoning。模型差距仅对应本轮设置。'

s=b.slide('回答实验结果','回答实验：模型排名和评判方法都会影响成绩','JudgeBench 比模型；RewardBench 2 固定 Jev，比评法。')
b.text(s,1,2.15,6.8,.5,'JudgeBench：两份回答谁更好？',24,b.TEAL,True)
b.table(s,['评委','逐次准确率','双顺序都对'],[
 ['GPT-5 mini','85.71%','80.57%'],['Jev','78.14%','70.57%'],['Qwen','64.29%','40.00%'],['Skywork*','60.29%','60.29%']], [2.8,2.1,2.1],y=2.9,rowh=.62,fs=19,highlight=1)
b.text(s,8.4,2.15,6.8,.5,'RewardBench 2：选赢家 vs 打分',24,b.TEAL,True)
# Right-hand table uses separate manually positioned cells.
headers=['类别','直接四选一','打分后选最高']; rr=[['事实正确性','80.42%','81.47%'],['数学','72.68%','77.60%'],['精确遵循要求','50.63%','55.63%'],['安全','87.78%','66.44%']]
for j,row in enumerate([headers]+rr):
 x=8.4;y=2.9+j*.62
 for w,v in zip([2.45,2.05,2.25],row):
  b.rect(s,x,y,w,.62,b.NAVY if j==0 else b.WHITE);b.text(s,x+.1,y+.12,w-.2,.45,v,18,b.WHITE if j==0 else b.INK,j==0);x+=w
b.text(s,1.05,6.25,13.8,.65,'*Skywork 使用 256-token 短上下文。RB2 没有人工 1—5 分；检查模型分数能否排对优劣。',20,b.MUTED)
b.banner(s,'回答二选一：GPT 更准；多回答评选：同一个 Jev，换评法也会明显改变成绩。')
s.notes_slide.notes_text_frame.text += '\nRB2表中均为相同类别样本上的比较。直接四选一排除102条Ties；rating覆盖全部1865条。'
save('jev-eval-lab-four-pages.pptx')

reset()
s=b.slide('一页总览','Jev 当评委：实验怎么做，结果怎么样？','三组实验 · 数据与方法 → 结果 → 结论')
# Broad left block for the main agent experiment, right for historical answer studies.
b.rect(s,.85,2.15,8.65,4.87,b.WHITE)
b.text(s,1.1,2.35,8.1,.5,'主实验｜真实 agent 过程判断',26,b.TEAL,True)
b.text(s,1.1,3.0,8.1,1.12,'500 条 BFCL / tau2 轨迹，6,147 步均有人工标签。\n输入完整 trace（含前后文）；逐步输出 +1 / 0 / −1。\nJev / Clef 选类别，GPT 生成标签；人工标签隐藏。',19)
heads=['评委','宏 F1','准确率','错误召回']; rr=[['Jev','50.45%','77.13%','34.35%'],['Clef','42.45%','66.15%','16.79%'],['GPT mini','37.57%','71.22%','13.45%']]
for j,row in enumerate([heads]+rr):
 x=1.1;y=4.35+j*.48
 for w,v in zip([2.0,2.0,2.0,2.1],row):
  b.rect(s,x,y,w,.48,b.NAVY if j==0 else b.LIGHT if j==1 else b.BG);b.text(s,x+.1,y+.09,w-.2,.36,v,17,b.WHITE if j==0 else b.TEAL if j==1 else b.INK,j<2);x+=w
b.text(s,1.1,6.48,8.1,.4,'Jev 领先，但每 100 个错误仍漏掉约 66 个。',22,b.ORANGE,True)

b.rect(s,9.8,2.15,5.35,2.23,b.WHITE)
b.text(s,10.05,2.35,4.85,.45,'回答二选一｜JudgeBench',23,b.TEAL,True)
b.text(s,10.05,2.98,4.85,1.17,'350 对回答，交换位置各评一次。\n准确率：GPT 85.71% > Jev 78.14%。\n双顺序都对：80.57% vs 70.57%。',18)
b.rect(s,9.8,4.58,5.35,2.44,b.WHITE)
b.text(s,10.05,4.78,4.85,.45,'多回答评选｜RewardBench 2',22,b.TEAL,True)
b.text(s,10.05,5.4,4.85,1.43,'1,865 题，只有优劣标签，无人工评分。\n固定 Jev：直接选最好 vs 打分后选。\n安全类：87.78% vs 66.44%。\n同一模型，换评法也会改变成绩。',18)
b.banner(s,'结论：任务与评法决定表现；Agent 判断领先，不等于已证明能提高任务成功率。',y=7.35)
b.text(s,1.05,8.17,14,.25,'宏 F1 平等看待三类；错误召回衡量漏报。Agent 缺失预测按错计；RB2 四选一不含 Ties。',11,b.MUTED)
s.notes_slide.notes_text_frame.text += '\nAPB子集为BFCL/tau2各250条，100底层问题。完整轨迹包含未来信息，非仅历史前缀。GPT low reasoning。RB2安全类450条同集比较。'
save('jev-eval-lab-one-page.pptx')
