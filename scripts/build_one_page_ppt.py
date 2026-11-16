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


# The slide separates measured results, external model descriptions, and a proposed roadmap.
box(0, 0, 20, 1.36, NAVY)
text(.55, .19, 19, .6, "Jev Eval Lab｜从模型评测走向 Agent 评估体系", 32, "FFFFFF", True)
text(.57, .91, 19, .3, "研究问题：同类模型如何选？如何用低成本过程信号，改善可验证的任务质量与评估效率？", 19, "D6E5EE")
box(.5, 1.56, 19, .72, "DDEFF0")
text(.75, 1.73, 18.5, .4, "核心判断  System One 可承担高频、原子的语义检查；是否改善 agent，必须用独立真值与端到端实验验证。", 22, TEAL, True)
text(.57, 2.48, 18.9, .58,
     "已有实测：6,428 条判断；JudgeBench Jev 78.14% vs GPT-5 mini 85.71%，费用约 1/42、p50 约 1/32。\nRB2：四选一 82.47% / rating top-1 77.91%（协议及样本范围不同）；均为回答评估，尚无 agent 成功率提升证据。", 18, MUTED)

box(.5, 3.27, 9.35, 4.65, "FFFFFF")
box(10.08, 3.27, 9.42, 4.65, "FFFFFF")
text(.75, 3.47, 8.9, .4, "01  同类对照：比较路线，而非拼榜单", 23, NAVY, True)
text(.75, 4.0, 8.85, .3, "以下为外部模型资料；除 Jev 外，均未在本仓库实测。", 16, MUTED)
rows = [
    ("模型", "主要差异", "评估候选与边界"),
    ("Jev", "托管类型决策 API", "快速基线；需验证域内校准"),
    ("Laya", "开放小型编码器", "短证据 / 可微调；注意截断"),
    ("Kev", "开放 Qwen 决策模型", "自托管 / 可训练；计入算力成本"),
    ("Clef / Flash", "开放 27B / 9B · 64K", "长证据 / 多问题；收益待实测"),
    ("Decision 3.0", "开放多模态决策家族", "GUI 状态检查；须环境验证"),
]
widths = [1.7, 3.12, 4.02]
for i, row in enumerate(rows):
    yy = 4.47 + i * .42
    box(.75, yy, 8.84, .42, NAVY if i == 0 else ("EEF4F6" if i % 2 == 0 else "FFFFFF"))
    xx = .75
    for j, val in enumerate(row):
        text(xx + .07, yy + .085, widths[j] - .12, .3, val, 16,
             "FFFFFF" if i == 0 else INK, i == 0)
        xx += widths[j]
text(.76, 7.12, 8.82, .62,
     "外部配对研究：Jev 在 11 类 agent 决策点中 9 类领先 Laya；\n但两者零样本模型路由均未超过随机水平，不能泛化为全能评委。[1]", 16, TEAL)

text(10.33, 3.47, 8.9, .4, "02  对 Agent 评估：过程信号＋分层复核", 23, NAVY, True)
text(10.33, 4.02, 8.9, .65,
     "离线评委：标注轨迹、定位失败、回归筛查、分配人工审核。\n在线控制：重试 / 停止 / 升级，会改变行为，必须重跑任务。", 18)
for yy, title, detail in [
    (4.94, "A  规则 / 环境真值", "检查测试、文件、状态变化与硬约束；保存证据。"),
    (5.7, "B  System One 检查", "工具是否适用？返回是否支持结论？是否虚假报成功？"),
    (6.46, "C  强模型 / 人工复核", "处理证据不足、复杂推理与重要分歧；允许弃判。"),
]:
    box(10.33, yy, 2.78, .54, "DDEFF0")
    text(10.47, yy + .12, 2.55, .3, title, 17, TEAL, True)
    text(13.3, yy + .1, 5.9, .45, detail, 17)
text(10.34, 7.27, 8.85, .4,
     "看真实执行证据，不凭 agent 自述；单步分数 ≠ 最终任务成功率。", 18, TEAL, True)

text(.55, 8.17, 19, .4, "03  发展路线：先评估评委，再评估整套系统；数据稳定后才考虑后训练", 23, NAVY, True)
phases = [
    ("①  建真值与轨迹集", "定义成功条件与原子 rubric；\n环境验证＋人工仲裁。\n按任务族分训练 / 校准 / 测试。"),
    ("②  同协议比较评委", "规则 / 强 LLM / Jev / 开放模型；\n测漏检、误报、校准、风险覆盖；\n扰动顺序、长度、语言与注入。"),
    ("③  影子运行 → 闭环消融", "先只打标，再比较是否干预。\n看成功率、违规率、过早停止；\n算每次成功总费用与端到端 p95。"),
    ("④  校准与专用训练", "阈值只在独立校准集选择；\n累积真实错误和分歧再微调。\n保留锁定盲测、漂移监控与回归。"),
]
for i, (title, body) in enumerate(phases):
    xx = .5 + i * 4.8
    box(xx, 8.79, 4.6, 1.76, "FFFFFF")
    text(xx + .19, 8.97, 4.25, .35, title, 20, NAVY, True)
    text(xx + .19, 9.46, 4.25, .94, body, 17)
text(.55, 10.78, 19, .25,
     "来源：本仓库 report/ 与 artifacts/；同类模型官方资料；[1] arXiv:2610.02267（外部研究，限定其版本与任务）。详见备注与配套报告。  |  2026-11-16 · 1 / 1", 12, MUTED)
slide.notes_slide.notes_text_frame.text = (
    "通用 Agent 评估方向；没有假设某个具体项目。\n"
    "证据分层：本仓库已有实测；外部论文/作者资料；尚未执行的发展建议。其他决策模型尚未在本仓库运行。\n"
    "配套说明与完整引用：report/system-one-agent-evaluation.md。原报告：report/report.md、report/experiment-report.md。\n"
    "JudgeBench为350对双顺序，4模型共2800条；RB2 rating1865条、ranking1763条，共6428。\n"
    "JudgeBench逐次/严格双顺序/顺序一致：GPT-5 mini 85.71/80.57/89.71；Jev 78.14/70.57/84.86；"
    "Qwen 64.29/40.00/51.43；Skywork 60.29/60.29/100。Skywork为CPU 256-token左截断、同分数派生交换。\n"
    "Jev ECE0.041；对GPT-5 mini准确率差-7.57pp，95%CI[-11.71,-3.43]；按题10000次bootstrap。\n"
    "RB2四选一仅非Ties；rating为全量，严格排序77.75%，派生pairwise93.12%。本项目自定义适配，非官方榜单。\n"
    "工程：Decisions/Chat/本地模型/mock；TOML、断点续跑、版本/数据/请求哈希、原始响应、离线重算与错误审计。\n"
    "外部资料核查于2026-11-16；模型版本不同，不拼接异构benchmark排名：\n"
    "Laya：https://huggingface.co/convaiinnovations/laya\n"
    "Kev：https://github.com/jaredpalmer/kev\n"
    "Clef：https://developers.cloudflare.com/changelog/post/2026-10-01-clef-workers-ai/\n"
    "d3：https://huggingface.co/vllm-sr/d3\n"
    "[1] https://arxiv.org/abs/2610.02267 （Jev/Laya配对研究，非本仓库实测；该版本不能代表后续模型）\n"
    "控制基线还应包括开放LLM直接读取选项logits，以及简单决策头微调：https://arxiv.org/abs/2610.17205\n"
    "实施：先轨迹契约与独立真值，再评委验证、影子运行、闭环实验，最后考虑训练。计入证据提取、重试、升级与人工成本。\n"
    "风险覆盖、路由阈值须独立校准。不能以旧轨迹离线判断证明新控制策略能改善真实任务。"
)
prs.core_properties.title = "Jev Eval Lab｜System One 对照与通用 Agent 评估路线"
prs.core_properties.subject = "已有实测、同类模型、过程评估与闭环验证"
prs.core_properties.author = "Jev Eval Lab"
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
assert len(Presentation(OUT).slides) == 1
print(OUT)
