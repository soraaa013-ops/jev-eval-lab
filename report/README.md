# 实验报告与演示文稿

新增：[下一轮数据集选型](benchmark-selection.md)。Agent 主实验优先 τ-bench 官方文本任务、BFCL 官方多轮任务，再扩展 WebArena；下列已完成成绩仍属于此前实验。

本次已更新 GPT-5 mini / GPT-5 / Jev 的 RewardBench 2 四选一结果：同样 1,763 题，准确率分别为 81.57% / 83.95% / 82.47%。报告与演示文稿聚焦数据、评判方法、结果及费用。

## 先读哪个？

- [结果报告](report.md)：三组实验的主要结果、类别差异和结论。
- [实验方法详解](experiment-report.md)：解释完整 trace、人工标签、四选一、打分后选择和计分规则。
- [中文完整讲解](../docs/tutorial.zh-CN.md)：用例子展开三组实验。

## 演示文稿

三个版本均已纳入新完成的三模型四选一对照，并保留 agent 评估内容。

| 版本 | 内容 | 文件 |
|---|---|---|
| 一页 | 三组实验核心结果 | [PPT](jev-eval-lab-one-page.pptx) · [PDF](jev-eval-lab-one-page.pdf) |
| 四页 | 数据设计、agent 方法与结果、四选一类别对比 | [PPT](jev-eval-lab-four-pages.pptx) · [PDF](jev-eval-lab-four-pages.pdf) |
| 详细版（19 页） | 完整实验讲解，含评分例子、费用和差距的不确定性 | [PPT](jev-eval-lab-experiments.pptx) · [PDF](jev-eval-lab-experiments.pdf) |

## 单项实验

- [三模型 RewardBench 2 四选一对照](rewardbench2-gpt5mini-comparison.md)：1,763 题全部完成，mini 正式费用 $2.7800。
- [Agent 过程评估](agent-judge-benchmark.md)：500 条真实轨迹，6,147 步人工标签。
- [此前 GPT-5 实验](rewardbench2-gpt5-comparison.md)：包含另行完成的 Ties 补充结果；未继续全量评分。
- [实验结果数据](../artifacts/README.md)。
