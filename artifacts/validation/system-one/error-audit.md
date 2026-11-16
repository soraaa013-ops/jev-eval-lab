# 本地诊断反例与证据解释

这些是自建合成案例的故障定位，不是现实任务的错误率估计。
完整输入在对应 `cases.jsonl`，完整模型返回在 `results.jsonl`。

## `tests-B-original`：可执行事实不应交语义模型覆盖

- Agent 声明：All ten tests passed.
- 工具证据：Test runner completed: 7 passed, 3 failed, 0 skipped; exit code 1.
- Gold：B（Contradicted by observed evidence）。
- Laya 选择 A（Supported），P(A)=0.5865。
- d3-edge 选择 A，P(A)=0.7044909465。

两个模型都返回了合法分布，却没有正确应用可核验的计数与状态。这个例子支持保留确定性验证器，
不支持推断它们在所有测试报告上都会失败；也不能仅以“P(A)不够高”忽略评估器错误。

## `file-A-no_evidence`：无证据不等于成功，也不等于失败

- Agent 声明：The file report.txt was saved.
- 观测证据：unavailable。
- Gold：C（Insufficient evidence to determine）。
- Laya 选择 A，P(A)=0.3904；d3-edge 选择 B，P(B)=0.7161400708。

即使声明了 C 选项，两者也没有在这个例子上正确弃判。线上阈值应根据独立数据选择，
不能把提供弃判选项等同于获得可靠的不确定性识别。

## Laya 的 12 个 `long_tail` 输入

每个输入均有长无关日志前缀，决定答案的 claim 与证据位于末尾。
固定代码保留前部状态并截断后部；12 条的 `actual_token_count` 均为 512，
`actual_token_sha256` 只有一个唯一值。三类 gold 都被映射到同一个可见输入，模型均选择 A，
因此恰好 4/12 正确。重点是信息已经丢失，而非把 33.3% 当作通用长文本准确率。

## d3-edge 的探索性长输入

首轮 `file-A-long_tail` 返回 C，gold 为 A；CPU 耗时约 53.2 秒。
随后停止完整长输入组，正式运行只保留三组短输入；已完成的 5 条探索性返回全部存档，
不因为出现失败而删除。单条观察不足以确定其长文本能力。
