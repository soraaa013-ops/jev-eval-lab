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


# All diagnostics and reanalysis figures below come from committed JSON artifacts.
validation = ROOT / "artifacts/validation/system-one"
laya = json.loads((validation / "laya-probes/metrics.json").read_text())
d3 = json.loads((validation / "d3-edge-probes/metrics.json").read_text())
external = json.loads((validation / "external-reanalysis/metrics.json").read_text())

def count(m, key):
    return f"{m[key]['correct']}/{m[key]['n']}"

box(0, 0, 20, 1.36, NAVY)
text(.55, .2, 19, .6, "System One 模型｜验证结果与 Agent 评估方向", 32, "FFFFFF", True)
text(.57, .92, 19, .3, "Jev Eval Lab · 新增：4 类公开实现核查 / 外部 2,100 案例复算 / 2 个小模型本地诊断", 19, "D6E5EE")
box(.5, 1.56, 19, .72, "DDEFF0")
text(.75, 1.73, 18.5, .4, "核心结论  优先做执行证据检查与失败分诊；便宜、类型化的输出，不等于可信的最终成功判定。", 23, TEAL, True)
text(.57, 2.48, 18.9, .55,
     "已有基线：6,428 条判断；JudgeBench Jev 78.14% vs GPT-5 mini 85.71%，费用约 1/42、p50 约 1/32。\nRB2 四选一 82.47%（自定义协议）；以上是回答质量实验，尚未证明 agent 端到端收益。新增诊断不并入原计数。", 18, MUTED)

for xx in [.5, 6.92, 13.34]:
    box(xx, 3.25, 6.16, 4.73, "FFFFFF")
text(.73, 3.45, 5.7, .4, "01  同类模型：机制决定边界", 22, NAVY, True)
models = [
    ("Laya｜本地推理 60 次", "编码器，默认 512 tokens；长轨迹会截断。"),
    ("d3-edge｜本地推理 36 次", "0.59B code readout；本轮仅验证文本。"),
    ("Kev｜固定作者模型卡", "可训练 pointer head；域外能力须另测。"),
    ("Clef-flash｜配置 / 代码核查", "9B 联合 schema；吞吐与问题干扰待测。"),
]
for i, (title, body) in enumerate(models):
    yy = 4.05 + i * .79
    text(.75, yy, 5.65, .33, title, 19, TEAL, True)
    text(.75, yy + .36, 5.65, .36, body, 17)
text(.75, 7.36, 5.65, .43, "同一 API ≠ 相同概率语义、证据预算与计算量。", 16, MUTED)

text(7.15, 3.45, 5.7, .4, "02  验证证据：按任务判断", 22, NAVY, True)
text(7.16, 4.0, 5.67, .3, "外部原始响应复算 · 历史 Jev / Laya", 17, TEAL, True)
rows = [("正确率", "Jev", "Laya")]
for label, key in [("工具选择", "B_tool_selection"), ("模型路由", "A_model_router"), ("RAG 门控", "D_rag_gate")]:
    m = external[key]
    rows.append((label, f"{m['jev_accuracy']:.2%}", f"{m['laya_accuracy']:.2%}"))
for i, vals in enumerate(rows):
    yy = 4.46 + .36*i
    box(7.16, yy, 5.67, .36, NAVY if i == 0 else ("EDF4F6" if i % 2 == 0 else "FFFFFF"))
    for j, val in enumerate(vals):
        offset, width = [(0, 2.28), (2.28, 1.65), (3.93, 1.74)][j]
        text(7.23+offset, yy+.055, width-.12, .28, val, 16, "FFFFFF" if i == 0 else INK, i==0)
text(7.16, 6.04, 5.67, .3, "本地诊断 · 正确数（Laya / d3-edge）", 17, TEAL, True)
text(7.16, 6.48, 5.67, .7,
     f"短证据：{count(laya,'original')} / {count(d3,'original')}；缺证据：{count(laya,'no_evidence')} / {count(d3,'no_evidence')}。\nLaya：12 条长输入截断后，仅剩 1 种 token 序列。", 17)
text(7.16, 7.43, 5.67, .35, "合成诊断仅定位故障，不排名通用能力；细节见报告。", 14, MUTED)

text(13.57, 3.45, 5.7, .4, "03  Agent 评估：先做什么", 22, NAVY, True)
for yy, title, body in [
    (4.05, "优先｜证据支持＋失败分诊", "看工具返回与实际状态，核验成功声明；\n输出支持 / 反驳 / 证据不足，允许复核。"),
    (5.18, "保留｜结果验证＋独立审核", "规则检查硬约束，模型检查语义；\n抽查高置信通过，测漏检与版本回归。"),
    (6.31, "后置｜在线停止 / 重试 / 路由", "它们会改变 agent 行为，必须重跑任务；\n验收成功率、误拦、总费用与端到端 p95。"),
]:
    text(13.59, yy, 5.65, .35, title, 19, TEAL, True)
    text(13.59, yy+.39, 5.65, .65, body, 17)
text(13.59, 7.57, 5.65, .26, "步骤分数不能替代真实任务结果。", 16, MUTED)

text(.55, 8.2, 19, .4, "04  发展路线：先证明评委可靠，再证明系统收益；数据稳定后考虑专用训练", 23, NAVY, True)
phases = [
    ("①  建立独立真值", "任务条件＋状态证据＋人工仲裁；\n训练 / 校准 / 测试按任务族隔离。"),
    ("②  评估评委本身", "AgentRewardBench 测最终判定；\nAgentProcessBench 测步骤质量。"),
    ("③  影子运行 → 闭环实验", "先不干预，再比较规则 / 快评委 /\n升级策略；计入提取与复核成本。"),
    ("④  校准 → 训练 → 回归", "以漏检—覆盖—成本选择模型；\n保留锁定盲测与域外、漂移检查。"),
]
for i, (title, body) in enumerate(phases):
    xx = .5 + i * 4.8
    box(xx, 8.81, 4.6, 1.71, "FFFFFF")
    text(xx+.19, 9.0, 4.25, .35, title, 20, NAVY, True)
    text(xx+.19, 9.51, 4.25, .78, body, 17)
text(.55, 10.78, 19, .25,
     "来源与边界：report/system-one-agent-evaluation.md · artifacts/validation/system-one/；本地诊断、外部重算、作者报告分开。底部路线尚待实施。  |  2026-11-16 · 1/1", 12, MUTED)
slide.notes_slide.notes_text_frame.text = (
    "配套报告：report/system-one-agent-evaluation.md；本轮证据：artifacts/validation/system-one/README.md。\n"
    "已有benchmark与新验证严格分开：原6,428条；外部复算2,100案例、两个模型；本地正式诊断Laya60条、d3-edge36条，均为合成。\n"
    "d3原60-case探索在5条后因CPU长文本约53秒/次中断；包括失败的原始结果保留在d3-edge-exploratory。\n"
    "缺证据组有4个唯一输入，各重复3次；所有变体相关，不能视为独立样本。不据此做通用排名。\n"
    "外部复算固定sys1-eval commit e74dfb6d99ed041f5f5240af386ba5272de84cdd；Jev1.13.0与历史Laya，不是当前模型的新对战。\n"
    "完整六轨道复算正确率：Jev76.71%，Laya63.10%；作者修正的C轨道覆盖旧行；当前未重新人工核验外部标签。\n"
    "模型源与SHA256见catalog.json，各本地run包含代码/权重哈希、实际库版本、精度和原始返回。\n"
    "Laya confidence为1-归一化熵，不是P(correct)。应统一校准实际选中答案概率。\n"
    "Kev与Clef未在本机推理；d3只测文本，不验证其视觉、多模态或长轨迹能力。CPU延迟不能与厂商GPU或API延迟直接比较。\n"
    "规则验证器也需审核能否接受正确替代路径。在线控制仅看当时可见信息，离线全轨迹不能冒充在线能力。\n"
    "AgentRewardBench: https://arxiv.org/abs/2504.08942v2\n"
    "AgentProcessBench: https://arxiv.org/abs/2603.14465v2\n"
    "System One配对研究: https://arxiv.org/abs/2610.02267\n"
    "System1-Arena: https://arxiv.org/html/2610.21244v1 ；相同步准确率不保证相同闭环成功率，详见报告。\n"
    "模型固定来源及其他论文链接详见配套报告。底部为建议的后续实验，本轮没有运行上述两个agent benchmark。\n"
    "简化级联成本=C_extract+C_fast+q*C_strong，必须在相同质量约束下比较；还需计入失败重试、自托管与人工工时。"
)
prs.core_properties.title = "System One 模型验证与通用 Agent 评估建议"
prs.core_properties.subject = "固定实现、外部复算、本地诊断与证据化评估路线"
prs.core_properties.author = "Jev Eval Lab"
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
assert len(Presentation(OUT).slides) == 1
print(OUT)
