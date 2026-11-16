"""Build the one-slide Chinese project overview (requires python-pptx).

Run from any directory: python scripts/build_one_page_ppt.py
All quantitative inputs are committed experiment metrics; no API calls are made.
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


box(0, 0, 20, 1.47, NAVY)
text(.55, .22, 15, .6, "Jev Eval Lab｜类型决策模型评估研究", 32, "FFFFFF", True)
text(.57, .93, 18.8, .35,
     "研究定位：比较类型化 judge、生成式 LLM 与开放奖励模型，衡量准确率、校准、稳定性、延迟与成本。", 19, "D6E5EE")
box(.5, 1.7, 19, .82, "DDEFF0")
text(.75, 1.87, 18.5, .48,
     "核心结论  Jev 准确率低于 GPT-5 mini，但费用约为其 1/42、p50 延迟约为其 1/32；可探索“先筛选、再升级”。", 23, TEAL, True)

box(.5, 2.75, 11.7, 5.06, "FFFFFF")
box(12.43, 2.75, 7.07, 5.06, "FFFFFF")
section(.75, 2.98, 11.2, "01  JudgeBench：四模型统一比较",
        "350 对客观正确性样本 × A/B 双顺序 × 4 模型＝2,800 条判断\n来源：MMLU-Pro 154 对、LiveBench 154 对、LiveCodeBench 42 对。")

cols = [3.04, 1.43, 1.48, 1.43, 1.27, 2.05]
heads = ["模型", "逐次准确率", "双顺序全对", "顺序一致率", "p50 延迟", "总费用 / 700 条"]
runs = [
    ("GPT-5 mini", "judgebench-gpt-5-mini"),
    ("Jev 1.14", "judgebench-jev-1.14"),
    ("Qwen3-30B-A3B", "judgebench-qwen3-30b-a3b-v2"),
    ("Skywork RM 0.6B*", "judgebench-skywork-rm-0.6b-256"),
]
metrics = []
rows = [heads]
for label, run in runs:
    m = json.loads((ROOT / "artifacts/runs" / run / "metrics.json").read_text())
    metrics.append(m)
    cost = f"${m['reported_total_cost']:.4f}" if not label.startswith("Skywork") else "$0 API 费*"
    rows.append([label, *(f"{m[k]:.2%}" for k in ("accuracy", "strict_swap_accuracy", "swap_consistency")),
                 f"{m['latency_ms_p50']/1000:.3f} s" if label == "Jev 1.14" else f"{m['latency_ms_p50']/1000:.2f} s", cost])
for i, row in enumerate(rows):
    yy = 4.25 + i * .48
    box(.75, yy, 10.7, .48, NAVY if i == 0 else ("DDEFF0" if i == 2 else ("F0F4F7" if i % 2 == 0 else "FFFFFF")))
    xx = .75
    for j, value in enumerate(row):
        text(xx + .08, yy + .1, cols[j] - .1, .32, value, 15.5 if i == 0 else 17,
             "FFFFFF" if i == 0 else INK, i in (0, 2))
        xx += cols[j]
text(.78, 6.8, 10.95, .76,
     "统计：按题聚类 bootstrap 10,000 次；Jev 对 GPT-5 mini 准确率差\n−7.57 个百分点（95% CI：−11.71～−3.43）；Jev 的 ECE 最低，为 0.041。", 18)
text(.78, 7.46, 11, .27, "* Skywork：CPU、256-token 左截断；计算成本另计；同分数派生交换结果，一致率由机制保证。", 14, MUTED)

section(12.68, 2.98, 6.58, "02  RewardBench 2：Jev 协议对照",
        "1,865 条独立评分＋1,763 条非 Ties 四选一\n覆盖事实、聚焦、数学、精确指令、安全、并列。")
text(12.7, 4.27, 3.1, .55, "82.47%", 34, TEAL, True)
text(16.03, 4.27, 3.1, .55, "77.91%", 34, NAVY, True)
text(12.72, 4.94, 3.05, .32, "四选一准确率（非 Ties）", 17, MUTED)
text(16.05, 4.94, 3.05, .32, "独立评分 top-1（全量）", 17, MUTED)
text(12.7, 5.55, 6.5, 1.3,
     "严格排序 77.75%；派生 pairwise 93.12%。\n安全：四选一 87.78% → 评分 66.44%。\n精确指令最弱：50.63% / 55.63%。", 19)
text(12.7, 6.94, 6.5, .64,
     "Ties：97.91%（官方公式＋自定义五档分数）。\n以上均为自定义适配，不能作为官方榜单成绩。", 17, TEAL, True)

box(.5, 8.04, 6.18, 2.49, "FFFFFF")
box(6.91, 8.04, 6.18, 2.49, "FFFFFF")
box(13.32, 8.04, 6.18, 2.49, "FFFFFF")
text(.75, 8.23, 5.7, .4, "03  工程交付与复现", 23, NAVY, True)
text(.75, 8.8, 5.68, 1.52,
     "6 个完整 run，6,428 条结果已入库。\nDecisions / Chat / 本地模型＋离线 mock；\nTOML 配置、断点续跑、哈希与原始响应；\n离线重算指标、置信区间、可靠性与错误审计。", 18)
text(7.16, 8.23, 5.7, .4, "04  应用价值与决策建议", 23, NAVY, True)
text(7.16, 8.8, 5.68, 1.52,
     "应用图谱：评委、RAG、路由、Agent 监督、\n审核、数据筛选、语义质量检查。\n本次验证评估场景；先做内部盲测与阈值校准，\n低置信升级强模型/人工，再评估后训练价值。", 18)
text(13.57, 8.23, 5.7, .4, "05  结论边界与后续研究", 23, NAVY, True)
text(13.57, 8.8, 5.68, 1.52,
     "合法输出不等于判断正确；校准不可跨域外推。\nRB2 仅测 Jev；Ties 高分待审计；API 会漂移。\n未测：原子 rubric、改写/长度/注入、中英对照、\n参考答案消融与版本漂移；需独立新实验。", 18)

text(.55, 10.78, 18.8, .25,
     "来源：report/report.md · report/experiment-report.md · artifacts/（指标与逐条证据）  |  实验 2026-11-09 · 研究 v1.0 / 2026-11-10  |  1 / 1", 13, MUTED)
slide.notes_slide.notes_text_frame.text = (
    "单页摘要，全部结果来自仓库固定实验，并非当前模型能力或价格承诺。\n"
    "报告：report/report.md；详细过程：report/experiment-report.md；证据索引：artifacts/README.md。\n"
    "严格双顺序要求同一道题两个方向都正确。Skywork 700 条为350对独立评分后派生的两个方向，非700次API请求。\n"
    "JudgeBench Jev准确率95% CI为74.29%–81.86%；相对Qwen +13.86pp [10.00,17.71]；"
    "相对Skywork +17.86pp [12.00,23.71]。\n"
    "RewardBench 2四选一费用$0.16098、平均446.6ms；rating费用$0.19796、平均475.2ms。"
    "六子集自定义宏平均80.49%不能与82.47%非Ties微平均混淆；不同协议不能直接作优劣比较。\n"
    "错误机制包括知识辨别、重新执行复杂推理与位置敏感性。Jev 153次错误中18次置信度≥0.8；"
    "GPT-5 mini为100/78；Qwen为250/196。\n"
    "Risk–coverage仅为描述：Jev置信度≥0.96覆盖12.14%、risk约2.35%；≥0.76覆盖50.29%、risk约7.95%。"
    "不能在测试集上选择业务阈值。\n"
    "已提交响应可离线复算；托管API无法保证逐比特重跑。数据许可与哈希见docs/dataset-provenance.md。\n"
    "复现：python scripts/build_one_page_ppt.py（依赖python-pptx；推荐安装Noto Sans CJK SC）。"
)
prs.core_properties.title = "Jev Eval Lab｜一页研究总结"
prs.core_properties.subject = "研究设计、模型结果、工程复现、应用与限制"
prs.core_properties.author = "Jev Eval Lab"
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
assert len(Presentation(OUT).slides) == 1
print(OUT)
