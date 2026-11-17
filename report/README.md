# Reports

新版实验讲解（17 页）：[可编辑 PPT](jev-eval-lab-experiments.pptx) · [PDF 预览](jev-eval-lab-experiments.pdf)。重点解释数据、评判方法与结果，展开 agent 完整轨迹评分，并区分 RewardBench 2 的优劣标签与模型评分。

实验导读：[中文实验讲解](../docs/tutorial.zh-CN.md)，用具体例子解释数据设计、评判方法、计分规则与三组实验结果。

一页汇报：[可编辑 PPT](jev-eval-lab-one-page.pptx) · [PDF 预览](jev-eval-lab-one-page.pdf)。
当前主线：[System One 如何评估 Agent](agent-judge-benchmark.md)。先讲清机制，再比较三个评委在 500 条真实轨迹上的判定。
旧回答质量实验和合成诊断保留为历史补充，避免混淆。
配套阅读：[System One 模型验证与通用 Agent 评估](system-one-agent-evaluation.md)，
包括固定实现核查、外部 2,100 个案例复算、本地小模型诊断、适用边界和研究路线。
[验证证据与复现入口](../artifacts/validation/system-one/README.md) 区分本地推理、外部重算、作者报告与建议。
安装 `python-pptx` 后运行 `python scripts/build_one_page_ppt.py` 可重新生成；
推荐字体为 Noto Sans CJK SC，PDF 由 LibreOffice 导出。

本仓库提供两个互补版本：

1. [研究报告版](report.md)：强调研究问题、实验协议、精确指标、限制和可复现性，
   适合技术评审、继续实验和引用结果。
2. [实验详解版](experiment-report.md)：不要求阅读源代码，逐步解释数据转换、请求
   payload、候选交换、ranking/rating、Ties 公式、缓存、逐条结果和指标计算。

完整逐条实验数据位于 [实验结果索引](../artifacts/README.md)。

