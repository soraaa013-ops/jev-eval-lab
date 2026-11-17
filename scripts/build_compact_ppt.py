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
 ['RewardBench 2\n1,865 条问题','chosen / rejected\n不是人工数值评分','三模型同题四选一：1,763 题\n另有 Jev 评分方法对比','谁更准？\n费用差多少？'],
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

s=b.slide('回答实验结果','四选一：GPT-5 83.95%，Jev 82.47%，mini 81.57%','RewardBench 2：1,763 题，三个模型看到相同候选与顺序，选中 chosen 就算对。')
b.table(s,['类别 / 题数','Jev','GPT-5','GPT-5 mini'],[
 ['事实正确性 / 475','80.42%','87.37%','85.68%'],['聚焦问题 / 495','93.54%','80.81%','77.78%'],['数学 / 183','72.68%','89.62%','90.71%'],['精确遵循要求 / 160','50.63%','65.63%','60.63%'],['安全 / 450','87.78%','88.00%','85.11%'],['总体 / 1,763','82.47%','83.95%','81.57%'],['整轮费用','$0.1610','$22.5146','$2.7800']], [5.3,3,3,3],y=2.2,rowh=.48,fs=20,highlight=5)
b.text(s,1.05,6.3,13.8,.72,'mini 比 GPT-5 少答对 42 题，费用约为其 12%；mini 与 Jev 总体差距尚不确定。\n另一组 JudgeBench 二选一：GPT-5 mini 85.71%，Jev 78.14%（350 对，各交换一次）。',19)
b.banner(s,'GPT 系列擅长数学，Jev 擅长聚焦问题；总分按题计，不是官方六类别榜单分数。')
s.notes_slide.notes_text_frame.text += '\n排除102条Ties；没有人工数值rating。GPT-5与mini均medium reasoning，Jev为历史同题Choice结果。mini−Jev的95%区间[-2.89,+1.13]pp；mini−GPT-5为[-4.08,-0.68]pp。费用仅四选一。'
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
b.text(s,10.05,2.98,4.85,1.17,'350 对回答，交换位置各评一次。\nGPT-5 mini 85.71%；Jev 78.14%。\n双顺序都对：80.57% vs 70.57%。',18)
b.rect(s,9.8,4.58,5.35,2.44,b.WHITE)
b.text(s,10.05,4.78,4.85,.45,'多回答评选｜RewardBench 2',22,b.TEAL,True)
b.text(s,10.05,5.4,4.85,1.43,'同题四选一 1,763 题，优劣标签隐藏。\nGPT-5 83.95% · Jev 82.47%\nGPT-5 mini 81.57%（费用 $2.78）\nmini 费用约为 GPT-5 的 12%。',18)
b.banner(s,'结论：Agent 判断 Jev 领先；四选一 GPT-5 总分较高，mini 费用更低。',y=7.35)
b.text(s,1.05,8.17,14,.25,'Agent 是事后判断，未验证在线收益。RB2 不含 Ties、非官方榜单分数；mini 与 Jev 总体差距尚不确定。',11,b.MUTED)
s.notes_slide.notes_text_frame.text += '\nAPB子集为BFCL/tau2各250条，100底层问题。完整轨迹包含未来信息，非仅历史前缀。GPT low reasoning。RB2为三模型同题比较，GPT-5与mini均medium reasoning。mini−Jev的95%区间[-2.89,+1.13]pp。'
save('jev-eval-lab-one-page.pptx')
