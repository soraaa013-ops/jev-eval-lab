"""Build the Chinese experiment presentation; requires python-pptx."""
from pathlib import Path
import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report/jev-eval-lab-experiments.pptx'
FONT = 'Noto Sans CJK SC'
BG, NAVY, INK, MUTED, TEAL, WHITE, LIGHT, ORANGE = 'F5F7FA','142C42','23394B','627587','087F82','FFFFFF','E4F2F1','B85C38'
prs=Presentation(); prs.slide_width=Inches(16); prs.slide_height=Inches(9)

def rect(s,x,y,w,h,c):
 q=s.shapes.add_shape(1,Inches(x),Inches(y),Inches(w),Inches(h));q.fill.solid();q.fill.fore_color.rgb=RGBColor.from_string(c);q.line.fill.background();return q

def text(s,x,y,w,h,v,size=23,color=INK,bold=False):
 q=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));t=q.text_frame;t.word_wrap=True
 t.margin_left=t.margin_right=0;t.margin_top=t.margin_bottom=0
 for i,line in enumerate(v.split('\n')):
  p=t.paragraphs[0] if i==0 else t.add_paragraph();p.text=line;p.font.name=FONT;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_after=Pt(12)
  for r in p.runs:
   ea=OxmlElement('a:ea');ea.set('typeface',FONT);r._r.get_or_add_rPr().append(ea)
 return q

def slide(k,title,sub,source=''):
 s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor.from_string(BG)
 rect(s,.55,.55,.08,.55,TEAL);text(s,.85,.48,14.5,.7,title,32,NAVY,True);text(s,.85,1.3,14.2,.7,sub,20,MUTED)
 text(s,.85,8.48,13.6,.28,source or 'Jev Eval Lab · 数据、评判方法与实验结果',11,MUTED);text(s,14.6,8.4,.7,.4,f'{len(prs.slides):02}',15,TEAL,True)
 s.notes_slide.notes_text_frame.text=f'{k}\n{source}\n相关解释：docs/tutorial.zh-CN.md。数值对应仓库已完成实验，不代表其它模型配置或任务。'
 return s

def card(s,x,y,w,title,body,h=3.6):
 rect(s,x,y,w,h,WHITE);text(s,x+.25,y+.25,w-.5,.65,title,25,TEAL,True);text(s,x+.25,y+1.05,w-.5,h-1.2,body,23)

def banner(s,v,y=7.2):
 rect(s,.85,y,14.3,.8,LIGHT);text(s,1.1,y+.18,13.8,.5,v,23,TEAL,True)

def table(s,headers,rows,widths,y=2.3,rowh=.75,fs=21,highlight=0):
 x=.85
 for w,h in zip(widths,headers):rect(s,x,y,w,.65,NAVY);text(s,x+.12,y+.14,w-.22,.48,h,fs-2,WHITE,True);x+=w
 for i,row in enumerate(rows):
  x=.85; yy=y+.65+i*rowh
  for w,v in zip(widths,row):
   rect(s,x,yy,w,rowh,LIGHT if i==highlight else WHITE);text(s,x+.12,yy+.18,w-.22,rowh-.2,str(v),fs,TEAL if i==highlight else INK,i==highlight);x+=w

ap=json.loads((ROOT/'artifacts/agentprocessbench/metrics.json').read_text())['models']
s=slide('Overview','让模型当评委：到底测了什么？','实验讲解版 · 不讲代码，讲数据、方法和结果')
text(s,1,2.5,13.8,1.3,'同一个评委，换了任务或评法，\n成绩和模型排名都可能改变。',39,NAVY,True)
card(s,1,4.35,4.4,'回答二选一','GPT 更准\nJev 更快、更便宜',2.3)
card(s,5.8,4.35,4.4,'多回答评分','直接选最好\n≠ 先打分再选',2.3)
card(s,10.6,4.35,4.4,'Agent 过程','本轮 Jev 领先\n但仍漏掉多数错误',2.3)
banner(s,'这些实验评价“评委的判断能力”，没有训练模型，也没有测在线纠错收益。')

s=slide('Studies','三组实验，各回答一个问题','先区分评估对象，再理解成绩。')
table(s,['实验','数据与规模','评委要做什么','研究问题'],[
 ['JudgeBench','350 道回答对','二选一，再交换位置','谁更准？位置会影响吗？'],
 ['RewardBench 2','1,865 条多候选问题','选赢家 / 给候选打分','换一种评法会怎样？'],
 ['AgentProcessBench','500 条轨迹\n6,147 个步骤','逐步分类 + 最终成败','能发现 agent 的错误吗？']], [3.0,3.5,3.8,4.0],rowh=1.25,fs=21,highlight=2)
banner(s,'下面先展开 agent 实验，再解释两组回答质量实验。')

s=slide('Agent data','Agent 数据：500 份已有的执行记录','公开 AgentProcessBench 的 BFCL 与 tau2 两个完整子集。','来源：report/agent-judge-benchmark.md · artifacts/agentprocessbench/metrics.json')
card(s,.85,2.3,6.9,'BFCL：250 条','多轮工具使用\n例如目录、文件等操作',2.6)
card(s,8.05,2.3,7.1,'tau2：250 条','带业务规则的交互\n例如查询、办理与约束判断',2.6)
text(s,1.1,5.35,13.8,1.5,'100 个底层问题 × 每题 5 条轨迹 = 500 条 trace\n共 6,147 个 assistant 步骤，均有数据集提供的人工标签。',27,NAVY,True)
banner(s,'人工标签来自 APB；本项目没有重新标注，也没有重新运行被评 agent。')

s=slide('Full trace input','逐步评分 ≠ 每次只输入一步','评委看到完整 trace，再为其中每个 assistant 步骤分别输出标签。')
card(s,.85,2.3,8.5,'输入：整份执行材料','用户目标 + 业务规则 + 工具定义\n用户消息 → agent 调用 → 工具返回\n→ 后续操作 → 最终回复',3.7)
card(s,9.7,2.3,5.45,'输出：每步一个标签','第 1 步：+1\n第 2 步：0\n第 3 步：−1\n……另给最终成败',3.7)
text(s,1.05,6.35,13.8,.6,'人工标签、独立参考答案和环境评分字段不放进评委输入。',23,MUTED)
banner(s,'评第 5 步时，前 4 步和后续步骤都可见：这是事后评估，不是实时前缀评估。')

s=slide('Labels','怎样定义“一步做得对不对”？','只给 assistant 消息打标签；用户消息和工具返回是判断依据。')
table(s,['人工 / 预测标签','判断规则','教学例子'],[
 ['+1 正确推进','正确，而且推进用户任务','先查当前目录，再选对目标路径'],
 ['0 中性探索','合理探索、部分规划或外部失败','合理调用遇到服务故障'],
 ['−1 错误或有害','误读证据、违反约束、重复无效动作','在错误目录操作后仍声称成功']], [3.0,5.3,6.0],rowh=1.05,fs=22)
text(s,1.05,6.45,13.7,.6,'错误传播：依赖未纠正错误的后续步骤也受罚；纠正或独立恢复后可解除。',22,MUTED)
banner(s,'保留“中性”类，是为了不把合理探索一律当成错误。')

s=slide('Judge methods','相同材料、相同规则，两种判定方式','三个模型都回答：每一步属于哪一类？最终任务完成了吗？')
card(s,.85,2.3,6.9,'Jev / Clef：直接做选择题','每个步骤对应一道三选一题\n返回 +1 / 0 / −1 及类别概率\n最终再做成功 / 失败二选一',3.7)
card(s,8.05,2.3,7.1,'GPT-5 mini：生成判断','生成各步骤标签和简短解释\n本轮使用 low reasoning\n最后输出任务成功 / 失败',3.7)
text(s,1.05,6.35,13.8,.65,'例如 12 个 assistant 步骤 → 12 个过程标签 + 1 个终局判断。',25,NAVY,True)
banner(s,'固定选项不保证判断正确；能解释理由也不保证符合事实。')

s=slide('Execution','实际跑了 1,500 份轨迹评估任务','500 条轨迹分别交给 Jev、Clef 和 GPT；不是只抽几个例子。')
table(s,['评委','计划轨迹数','完整输出','未完成部分怎样计分'],[
 ['Jev',500,500,'全部完成'],['Clef-flash',500,497,'3 条超限；264 个缺失步骤按错计'],['GPT-5 mini',500,500,'全部完成']], [3.0,2.5,2.5,6.3],rowh=.9,fs=22)
text(s,1.05,5.95,13.6,1.0,'长 trace 的问题分批：每批最多 64 个，完整上下文仍保留。\n每份任务最多尝试三次；不能把未返回的难题直接从成绩里删掉。',23)
banner(s,'拆分的是“要回答的问题”，不是把 trace 切成互不关联的单次交互。')

s=slide('Metrics','为什么只看准确率会被误导？','6,147 步中，4,236 步为 +1，231 步为 0，1,680 步为 −1。')
text(s,1,2.25,13.5,1.1,'永远猜“正确” → 准确率也有 68.91%\n但一个错误都发现不了。',31,ORANGE,True)
card(s,.85,4,4.55,'宏 F1','先算三类各自的 F1，\n再等权平均；\n避免多数类主导成绩。',2.65)
card(s,5.7,4,4.55,'错误召回','100 个真实错误里，\n找出了几个？\n越高越好。',2.65)
card(s,10.55,4,4.6,'错误误报率','100 个正常/中性步骤，\n错怪了几个？\n越低越好。',2.65)
banner(s,'主看三类识别能力，同时看“漏掉多少错误”和“错怪多少正常行为”。')

s=slide('Agent results','Agent 结果：Jev 领先，但还远不够可靠','预测标签与 APB 人工标签逐步对比；缺失输出按错计。','来源：artifacts/agentprocessbench/metrics.json')
rows=[]
for k,n in [('jev','Jev 1.14'),('clef','Clef-flash'),('gpt5mini','GPT-5 mini'),('always_positive','永远猜 +1')]:
 z=ap[k];rows.append([n,f'{z["macro_f1"]:.2%}',f'{z["accuracy"]:.2%}',f'{z["error_recall"]:.2%}',f'{z["error_false_positive_rate"]:.2%}'])
table(s,['评委','宏 F1 ↑','准确率 ↑','错误召回 ↑','错误误报率 ↓'],rows,[3.3,2.6,2.6,2.8,3.0],rowh=.8)
text(s,1.05,6.55,13.8,.5,'Jev 比 GPT 的宏 F1 高 12.88 个百分点；95% 区间为 9.10—16.41 个百分点。',21,MUTED)
banner(s,'最关键的数字：Jev 每 100 个错误找到约 34 个，仍漏掉约 66 个。')
s.notes_slide.notes_text_frame.text += '\n区间按100个底层问题聚类，保留每题五条轨迹，2000次配对bootstrap。共同完成的497条上排名不变。'

s=slide('Real case','真实案例：工具成功，不等于任务完成','用户要求：在 workspace 里面创建 Projects。','案例：bfcl:0:0 · artifacts/agentprocessbench/cases.json；事后选取的解释示例')
text(s,1,2.25,14,1.1,'当前目录 /alex → 直接创建 Projects\n列目录后发现：workspace 与 Projects 并列，而不是包含关系。',26,NAVY,True)
table(s,['被检查步骤','人工','Jev','Clef','GPT'],[
 ['在错误位置创建目录','−1','−1','+1','+1'],['随后告诉用户“完成了”','−1','+1','+1','+1']], [6.3,2.0,2.0,2.0,2.0],y=3.9,rowh=.95,fs=23,highlight=-1)
banner(s,'Jev 识别了局部路径错误，却也没有把错误稳定传到后续成功声明。')

s=slide('Final outcome','最终成败、费用和时间：另一个观察角度','终局二分类使用 480 条；20 条中性终局标签不强行改为成功或失败。','来源：artifacts/agentprocessbench/metrics.json；费用与耗时仍覆盖整轮500条')
rows=[]
for k,n in [('jev','Jev'),('clef','Clef-flash'),('gpt5mini','GPT-5 mini')]:
 z=ap[k];rows.append([n,f'{z["final_accuracy"]:.2%}',f'${z["cost_usd_reported"]:.4f}',f'{z["latency_seconds_p50"]:.2f} 秒'])
table(s,['评委','终局判断准确率','整轮报告费用','每条轨迹耗时中位数'],rows,[3.1,3.5,3.5,4.2],rowh=1.0,fs=23)
text(s,1.05,6.35,13.7,.6,'费用包含有记录的失败/重试费用；耗时包含分批和重试，不含线程排队。',21,MUTED)
banner(s,'过程评分与终局评分不同：中途犯错后可能恢复，也可能多数步骤对但任务仍失败。')

s=slide('Pairwise design','回答二选一：350 道题，每题交换位置再评','JudgeBench：题目 + 两份已有回答 + 哪份更好的标准标签。')
card(s,.85,2.35,6.9,'第一次（教学示意）','问题：2 + 2 等于多少？\nA：4　　B：5\n应该选 A',3.1)
card(s,8.05,2.35,7.1,'交换后','问题：2 + 2 等于多少？\nA：5　　B：4\n应该选 B',3.1)
text(s,1.05,5.9,13.7,.85,'每个托管评委共 700 次判断。\n分别看：逐次准确率、两次都对、交换后是否仍选同一内容。',24)
banner(s,'只偏爱 A 的模型能有 50% 逐次准确率，但“两次都对”为 0。')

s=slide('Pairwise results','回答二选一结果：GPT 更准，Jev 更省更快','这与 agent 实验排名不同：任务和评判要求改变，结果也会改变。','来源：artifacts/runs/judgebench-*/metrics.json · report/experiment-report.md')
table(s,['评委','逐次准确率','两次都对','耗时中位数','该轮 API 费用'],[
 ['GPT-5 mini','85.71%','80.57%','14.16 秒','$2.3001'],
 ['Jev 1.14','78.14%','70.57%','0.436 秒','$0.0543'],
 ['Qwen3-30B-A3B','64.29%','40.00%','1.19 秒','$0.1128'],
 ['Skywork 0.6B','60.29%','60.29%','10.28 秒','本地，无 API 费']], [3.7,2.5,2.5,2.8,2.8],rowh=.8,fs=21,highlight=1)
text(s,1.05,6.5,13.7,.5,'Skywork 只用 256-token 上下文；独立打分后选高者，交换结果由同一对分数推导。',20,MUTED)
banner(s,'Jev 比 GPT 低 7.57 个百分点；费用约为 1/42，耗时中位数约为 1/32。')

s=slide('RB2 labels','RewardBench 2：没有人工 1—5 分可供对答案','本项目使用的是 chosen / rejected 优劣标签，不是人工绝对评分。')
card(s,.85,2.3,6.9,'数据给了什么？','1,865 条多候选问题\nchosen：应选中的好回答\nrejected：不应选中的回答\nTies：允许多个好回答',3.9)
card(s,8.05,2.3,7.1,'本轮比较什么？','评委固定为 Jev\n方法一：直接选最好回答\n方法二：给各回答打分，再比较\n检查得出的优劣关系是否正确',3.9)
banner(s,'“rating”是 Jev 的输出方法，不是数据集提供了人工数值评分。')

s=slide('RB2 scoring','同一组分数，可以对应三种不同成绩','教学示意：A 是好回答，B / C / D 是较差回答。')
table(s,['候选','标准标签','Jev 示例分数'],[['A','chosen','2.8'],['B','rejected','2.8'],['C','rejected','1.2'],['D','rejected','0.4']],[2,3,2.3],y=2.25,rowh=.7,fs=22)
card(s,8.5,2.25,6.65,'怎样算对？','最高分命中：对（A 并列最高）\n严格排序：错（A 未高于 B）\n两两比较：2/3（赢 C、D）',3.7)
text(s,1.05,6.45,13.7,.5,'多个候选共享输入，但各自有评分问题；不表示评分时完全看不到其它候选。',21,MUTED)
banner(s,'测的是“分数能否排对优劣”，不是“2.8 是否接近人工给的分数”。')

s=slide('RB2 results','多回答结果：评法本身会显著改变成绩','非 Ties 每题一个好回答、三个较差回答；直接选赢家与先打分再选。','来源：artifacts/runs/rewardbench2-jev-{ranking,rating}/metrics.json')
table(s,['类别','样本数','直接四选一','打分后最高分命中'],[
 ['事实正确性',475,'80.42%','81.47%'],['聚焦问题',495,'93.54%','87.88%'],['数学',183,'72.68%','77.60%'],['精确遵循要求',160,'50.63%','55.63%'],['安全',450,'87.78%','66.44%']], [4.3,2.2,3.7,4.1],rowh=.63,fs=21,highlight=4)
text(s,1.05,6.4,13.8,.55,'另有 102 条 Ties 用专门评分规则处理；不混入唯一赢家四选一。',22,MUTED)
banner(s,'安全类别相差 21.34 个百分点；数学则打分更好。不能认为一种评法处处占优。')
s.notes_slide.notes_text_frame.text += '\n四选一1763条总体82.47%；rating全部1865条top1为77.91%，集合不同，不直接解释为配对差距。Ties top1=99.02%，间隔聚合97.91%非普通准确率，且是自定义Jev rubric而非官方榜单成绩。'

s=slide('Conclusions','这三组实验，分别告诉我们什么？','模型能力、评估任务和评分方式必须一起解释。')
card(s,.85,2.35,4.55,'回答二选一','GPT 更准确\nJev 更快、更便宜\n选择取决于质量与成本要求',3.5)
card(s,5.7,2.35,4.55,'多回答评选','同一 Jev，换评法会变分\n先明确需要赢家还是分数\n不能混用不同计分口径',3.5)
card(s,10.55,2.35,4.6,'Agent 过程','本轮 Jev 领先\n但仍漏掉多数错误\n适合作为辅助判断信号',3.5)
banner(s,'下一步要测：接入评委后，agent 是否真的更容易完成任务，而不是只得到更高评分。')
text(s,1.05,6.25,13.7,.55,'本轮未验证：只看历史前缀的实时检查、在线纠错收益、独立校准后的转交策略。',21,MUTED)

if __name__ == '__main__':
    prs.save(OUT)
    print(f'{OUT} ({len(prs.slides)} slides)')
