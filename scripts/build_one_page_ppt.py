"""Build the one-slide Chinese project overview (requires python-pptx).

Run from any directory: python scripts/build_one_page_ppt.py
Summarizes committed experiment metrics and cited external research; no API calls.
"""
from pathlib import Path
import json

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/jev-eval-lab-one-page.pptx"
FONT = "Noto Sans CJK SC"
NAVY, INK, MUTED, TEAL = "12283D", "20354A", "607487", "087F82"
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(20), Inches(11.25)
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = RGBColor.from_string("F3F6F8")


def box(x, y, w, h, fill):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background()
    return shape


def text(x, y, w, h, value, size=19, color=INK, bold=False, align=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = RGBColor.from_string(color)
        p.space_after = Pt(5)
        if align is not None:
            p.alignment = align
        for run in p.runs:
            ea = OxmlElement("a:ea")
            ea.set("typeface", FONT)
            run._r.get_or_add_rPr().append(ea)
    return shape


def section(x, y, w, title, subtitle):
    box(x, y, .055, .34, TEAL)
    text(x + .18, y - .015, w - .18, .4, title, 23, NAVY, True)
    text(x, y + .5, w, .68, subtitle, 18, MUTED)


# The single slide now explains and reports the real agent-trajectory experiment.
m = json.loads((ROOT / "artifacts/agentprocessbench/metrics.json").read_text())
box(0, 0, 20, 1.35, NAVY)
text(.55, .19, 18.9, .57, "System One 如何评估 Agent？", 34, "FFFFFF", True)
text(.57, .91, 18.9, .32, "同一份任务与执行证据 · Jev / Clef-flash / GPT-5 mini · 真实轨迹上的配对实验", 19, "D6E5EE")
box(.5, 1.55, 19, .68, "DDEFF0")
text(.75, 1.7, 18.5, .4, "评估对象是 agent 的行为：有没有推进任务、哪里出错、最后是否完成；再用人工标签检验评委。", 22, TEAL, True)
flow = [("输入证据", "任务 + 规则 + 工具定义\n完整消息 / 调用 / 工具返回"),
        ("两种评委", "System One：直接选择类别与概率\nLLM judge：生成标签与简短解释"),
        ("统一判断", "+1 正确推进 / 0 中性探索 / −1 错误\n逐步判定 + 最终任务成败"),
        ("人工对照", "比较宏 F1、漏报、误报\n同时记录费用与每条轨迹耗时")]
for i,(title,body) in enumerate(flow):
    x=.5+i*4.82
    box(x,2.48,4.54,1.12,"FFFFFF")
    text(x+.16,2.59,4.22,.3,title,20,TEAL,True)
    text(x+.16,2.96,4.22,.57,body,16)
    if i<3:text(x+4.57,2.82,.25,.3,"→",18,TEAL,True)
box(.5,3.87,5.8,4.18,"FFFFFF")
text(.74,4.08,5.3,.37,"01  这次究竟跑了什么",23,NAVY,True)
text(.75,4.68,5.25,.82,"500 条真实轨迹\n6,147 个人工标注步骤",27,TEAL,True)
text(.75,5.74,5.25,1.44,f"AgentProcessBench：BFCL / τ² 各 250 条。\n覆盖工具使用与多轮业务办理。\n完整输出 {sum(m['models'][k]['complete_trajectories'] for k in ['jev','clef','gpt5mini']):,} / 1,500 份。\n人工答案不进入输入，长轨迹不截断。",18)
text(.75,7.28,5.25,.57,"测评委与人工的一致性；尚未证明\n接入评委后 agent 成功率提高。",17,MUTED)
box(6.55,3.87,12.95,4.18,"FFFFFF")
text(6.8,4.08,12.3,.37,"02  相同证据、相同规则，直接比较",23,NAVY,True)
headers=["评委","宏 F1 ↑","准确率 ↑","错误召回 ↑","总费用 $","p50 秒"]
xs=[6.83,9.67,11.48,13.28,15.45,17.42]
ws=[2.7,1.75,1.75,2.12,1.9,1.6]
for x,w,h in zip(xs,ws,headers):text(x,4.72,w,.38,h,17,MUTED,True)
for i,(key,label) in enumerate([("jev","Jev"),("clef","Clef-flash"),("gpt5mini","GPT-5 mini"),("always_positive","始终判 +1")]):
    z=m["models"][key]; yy=5.29+i*.49
    vals=[label,f'{z["macro_f1"]:.1%}',f'{z["accuracy"]:.1%}',f'{z["error_recall"]:.1%}',f'{z["cost_usd_reported"]:.3f}' if key!="always_positive" else "—",f'{z["latency_seconds_p50"]:.2f}' if key!="always_positive" else "—"]
    for x,w,v in zip(xs,ws,vals):text(x,yy,w,.36,v,18,TEAL if key=="jev" else INK,key=="jev")
text(6.83,7.42,12.05,.43,"宏 F1 平等看待三类，避免多数正确步骤掩盖漏报；区间按 100 个问题聚类计算。",16,MUTED)
box(.5,8.3,9.35,1.94,"FFFFFF")
box(10.1,8.3,9.4,1.94,"FFFFFF")
text(.74,8.48,8.86,.35,"03  一个看得懂的真实错误",22,NAVY,True)
text(.75,9.02,8.85,.97,"要求在 workspace 内建 Projects；agent 却在 /alex 建目录。\n人工判 −1；Jev 判 −1，Clef / GPT 判 +1。随后成功声明\n三者均判 +1：工具执行成功，并不等于用户任务正确完成。",18)
text(10.35,8.48,8.85,.35,"04  对你的通用评估体系意味着什么",22,NAVY,True)
text(10.35,9.02,8.85,.97,"可执行验证器查结果 → 模型评委查过程 → 疑难 / 抽样复核。\n最高错误召回仅 34%；目前应作辅助评估信号。\n下一步：独立校准集定阈值，再做前缀评估与闭环 A/B。",18)
text(.57,10.47,18.9,.49,"范围：BFCL / τ² 两子集，非 APB 全榜；Clef 3 条超限，缺失按错计。费用与延迟含有记录的重试，未验证 agent 端到端收益。\n来源：arxiv.org/abs/2603.14465 · HF LulaCola/AgentProcessBench @ cd81f326 · repo: artifacts/agentprocessbench / report/agent-judge-benchmark.md",13,MUTED)
slide.notes_slide.notes_text_frame.text = (
    "Method: report/agent-judge-benchmark.md; artifacts/agentprocessbench/PROTOCOL.md. "
    "500 trajectories from 100 queries, five traces per query; 6,147 step labels. "
    "Three judge configurations, full trace available, no gold labels in requests. "
    "All-request primary metrics count missing labels as wrong. Clef failed 3 trajectories "
    "after 3 attempts; 264 step labels missing. Common-completion sensitivity: 497 traces. "
    "GPT-5 mini uses low reasoning and short generated explanations; no equal-compute claim. "
    "Jev minus GPT macro-F1: +12.88 percentage points, paired query-bootstrap 95% CI "
    "[9.10,16.41]. Accuracy alone is misleading because 68.91% of gold steps are +1. "
    "Final binary outcome analysis in the report excludes 20 neutral gold outcomes "
    "with transparent post-run accounting; primary step metrics retain all traces. "
    "Cost is reported API USD including recorded retries; unavailable failure charges unknown. "
    "Example bfcl:0:0 was selected post-hoc for explanation, not for aggregate scoring."
)
prs.save(OUT)
print(OUT)
