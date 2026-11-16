"""Regenerate the measured-results section of the Chinese report from frozen metrics."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def pct(x):return f'{x*100:.2f}%'
def main():
    m=json.loads((ROOT/'artifacts/agentprocessbench/metrics.json').read_text());models=m['models'];names={'jev':'Jev 1.14','clef':'Clef-flash','gpt5mini':'GPT-5 mini','always_positive':'始终判 +1'}
    lines=['<!-- RESULTS -->','## 4. 实测结果：谁更会评，差距在哪里？','',
    '**本轮 Jev 的过程判断最好、延迟也最低；但三个评委都漏掉大量错误，不能据此作为唯一错误拦截器。** 这是指定模型版本、提示、任务范围下的结果，不能推广为 System One 架构普遍优于所有 LLM。','',
    '### 4.1 过程判断：主结果','',
    '总计 1,680 个错误步骤、231 个中性步骤、4,236 个正向步骤。始终猜 +1 已有 68.91% 准确率，因此必须同时看三类宏 F1 和错误召回。缺失输出按错计入主结果。','',
    '| 评委 | 完整轨迹输出 | 宏 F1 | 逐步准确率 | 错误召回 ↑ | 正常/中性步骤误报率 ↓ |',
    '|---|---:|---:|---:|---:|---:|']
    for key,v in models.items():lines.append(f'| {names[key]} | {v["complete_trajectories"]}/500 | {pct(v["macro_f1"])} | {pct(v["accuracy"])} | {pct(v["error_recall"])} | {pct(v["error_false_positive_rate"])} |')
    d=m['paired_differences']['jev minus gpt5mini']['macro_f1'];lo,hi=d['paired_query_bootstrap_95ci']
    lines += ['',f'Jev 相对 GPT-5 mini 的宏 F1 高 **{d["difference"]*100:.2f} 个百分点**，按 100 个底层问题进行 2,000 次配对 bootstrap 的 95% 区间为 **[{lo*100:.2f}, {hi*100:.2f}] 个百分点**。Jev 本身宏 F1 的区间为 [{pct(models["jev"]["macro_f1_95ci"][0])}, {pct(models["jev"]["macro_f1_95ci"][1])}]。这说明本轮差距并非仅凭一个案例得出，但不消除提示配置、数据污染和任务范围限制。','',
    f'实际含义：每 100 个已标注错误，Jev 约发现 {models["jev"]["error_recall"]*100:.0f} 个，仍漏掉约 {(1-models["jev"]["error_recall"])*100:.0f} 个。较低误报率不能弥补如此高的漏报。Clef 的宏 F1 高于 GPT，但总准确率更低，也说明一个总准确率不足以比较三分类评委。','',
    '| 子集 | Jev 宏 F1 | Clef 宏 F1 | GPT-5 mini 宏 F1 |', '|---|---:|---:|---:|']
    for ds in ['bfcl','tau2']:lines.append('| '+ds+' | '+' | '.join(pct(models[k]['subsets'][ds]['macro_f1']) for k in ['jev','clef','gpt5mini'])+' |')
    lines += ['',f'**覆盖率敏感性检查（事后补充）**：只比较三个模型均完整返回的 {m["common_complete_trajectories"]} 条轨迹 / 5,883 个步骤，Jev、Clef、GPT 的宏 F1 分别为 '+ '、'.join(pct(m['common_complete_metrics'][k]['macro_f1']) for k in ['jev','clef','gpt5mini'])+'，顺序不变。该表只帮助区分接口失败与判断能力，不替代包含失败的主结果。','',
    '### 4.2 最终结果、费用和耗时','',
    '| 评委 | 最终成败准确率（480 条） | 识别最终失败的召回 | 全部请求报告费用 USD | 每条轨迹 p50 / p95 秒 |', '|---|---:|---:|---:|---:|']
    for k in ['jev','clef','gpt5mini']:
        v=models[k];lines.append(f'| {names[k]} | {pct(v["final_accuracy"])} | {pct(v["final_failure_recall"])} | ${v["cost_usd_reported"]:.4f} | {v["latency_seconds_p50"]:.2f} / {v["latency_seconds_p95"]:.2f} |')
    lines += ['', '**口径修正必须说明**：分析时发现源数据有 20 条 `final_label=0`，但官方评委提示及本轮沿用的终局输出只有 ±1。因此辅助终局二分类指标使用其余 480 条；不把 0 擅自改成成功或失败。所有 500 条的逐步标签仍完整纳入主指标。全 500 条终局精确匹配率也保留在 JSON 中：Jev / Clef / GPT 为 '+ ' / '.join(pct(models[k]['final_accuracy_all_500_exact_match']) for k in ['jev','clef','gpt5mini'])+'。这是事后发现并披露的协议与标签差异，不是事先选掉困难样本。','',
    f'三模型主实验总报告费用 **${sum(models[k]["cost_usd_reported"] for k in ["jev","clef","gpt5mini"]):.4f}**，不含单独的预检。费用计入有 usage 的失败 / 重试响应；没有 usage 的失败是否收费未知。延迟包含分批和重试，不包括线程排队；并发为 12，并非硬件归一化吞吐。本轮 GPT 使用 low reasoning 与短解释，不能由此推断更强模型或更大推理预算的表现。','',
    '### 4.3 真实案例：工具成功不等于任务成功','',
    '来自 `bfcl:0:0`，原始证据见 [cases.json](../artifacts/agentprocessbench/cases.json)：','',
    '- 用户要求：在 `workspace` 里面创建 `Projects`。',
    '- 工具 `pwd` 返回当前目录 `/alex`。agent 随后直接调用 `mkdir(dir_name="Projects")`，没有先进入 `workspace`。',
    '- `ls` 显示 `workspace` 与 `Projects` 并列，因此目录位置不符合要求。agent 随后仍向用户宣称创建成功。','',
    '| 被检查步骤（原消息编号） | 人工标签 | Jev | Clef | GPT |', '|---|---:|---:|---:|---:|',
    '| 5：在当前目录直接创建 Projects | −1 | −1 | +1 | +1 |',
    '| 9：对用户宣称创建成功 | −1 | +1 | +1 | +1 |','',
    '评委需要比较的是“执行结果是否满足要求”，不能只看到调用成功就给高分。这个案例中 Jev 识别了路径错误，却也没有把问题稳定反映到后续成功声明。案例为事后选择的解释示例；排名来自完整集合，不由这个案例决定。','',
    f'概率同样不保证正确：Jev 最大类别概率 ≥0.9 的 {models["jev"]["probability_ge_0.9_steps"]} 个步骤中，仍有 {pct(models["jev"]["probability_ge_0.9_error_rate"])} 与人工标签不一致；Clef 对应 {models["clef"]["probability_ge_0.9_steps"]} 个步骤的不一致率为 {pct(models["clef"]["probability_ge_0.9_error_rate"])}。这只是该子集的描述统计，不等于完成了概率校准或阈值选型。','',
    '### 4.4 实验是否跑完？有没有运行错误？','',
    '**已按固定协议结束全部 1,500 份提交，完整输出 1,497 份。没有仍在后台等待的实验。** 共计划 18,441 个步骤标签，264 个因 Clef 三条终止失败而缺失；它们在主结果中按错计。','',
    '- 预检：Clef 一次 96 个问题被拒绝（上限 64），修正为分批请求；全量证据保持不变。预检不计入主指标。',
    '- 正式 Clef：7 条轨迹出现合计 16 次 HTTP 422 token-limit 拒绝；4 条经重试完成，`tau2:35:4`、`tau2:44:4`、`tau2:48:4` 在最多三次尝试后仍失败。预检曾接受同一最长轨迹，正式服务仍可能拒绝，不能靠一次 smoke 宣称覆盖所有长度。',
    '- 正式 GPT：7 条轨迹出现合计 9 次漏 / 多步骤编号的输出校验错误，重试后全部完成。没有悄悄补造缺失标签；原始响应保留。',
    '- Jev：500 条均在首次轨迹尝试完整返回。此处仅说明接口 / 输出可用性，不等于标签全对。',
    '- 除上述接口与输出问题，分析还发现了终局标签 0 与二分类提示的口径差异，已按上一节披露。',
    '- 缓存已验证：再次运行主实验显示 `Pending 0`；不会为终止失败自动超出三次尝试，也不会重复计费。','',
    '原始响应、所有重试、模型返回版本与逐项预测均保存在仓库。数据审计 / 标签映射 / 缺失计分等 11 个测试通过。','<!-- /RESULTS -->','']
    path=ROOT/'report/agent-judge-benchmark.md';text=path.read_text();start=text.index('<!-- RESULTS -->');end=text.index('## 5. 如何发展');path.write_text(text[:start]+'\n'.join(lines)+'\n'+text[end:])
if __name__=='__main__':main()
