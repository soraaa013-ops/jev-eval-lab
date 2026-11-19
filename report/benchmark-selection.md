# 新一轮数据集选型：以公认 Agent 基准为主

选型日期：2026-11-19。本文是下一轮实验方案，尚未产生新成绩。

**决定：Agent 主实验优先用 τ-bench 官方文本任务和 BFCL 官方多轮工具任务，WebArena 作为第三个场景。AgentProcessBench 保留为逐步错误分析的补充，不再单独支撑主要结论。回答质量评估保留 RewardBench 系列。**

## 1. 为什么选这三组？

| 优先级 | 基准 | 可核实的认可度依据 | 对本项目最有用的部分 |
|---|---|---|---|
| 第一 | τ-bench / τ²-bench | Sierra 发布；Anthropic 系统卡采用 τ²-bench；Google DeepMind 的 gbench 集成 TAU-2 | 客服场景中，工具调用、业务规则、用户沟通是否共同完成任务 |
| 第一 | BFCL | UC Berkeley 发布；ICML 2025 论文；持续维护的多模型榜单；Google DeepMind gbench 集成 | 多轮工具操作后的状态和响应是否符合要求 |
| 第二 | WebArena | CMU 发布；Microsoft Research 的 AutoSurfer 使用；ServiceNow BrowserGym 集成 | 网页操作是否真的完成，而不是只口头宣称成功 |

这里的“认可度”依据是原作者之外的采用和可检查的评价规则，不是声称任何基准都没有争议。

来源：[Anthropic Sonnet 4.6 系统卡](https://www-cdn.anthropic.com/bbd8ef16d70b7a1665f14f306ee88b53f686aa75/Claude%20Sonnet%204.6%20System%20Card.pdf)、[Google DeepMind gbench 收录列表](https://github.com/google-deepmind/gbench/blob/main/docs/RESOURCES.md)、[BFCL 官方榜单与论文信息](https://gorilla.cs.berkeley.edu/leaderboard.html)、[WebArena 原作者主页](https://webarena.dev/og/)、[Microsoft Research AutoSurfer](https://www.microsoft.com/en-us/research/publication/autosurfer-teaching-web-agents-through-comprehensive-surfing-learning-and-modeling/)、[ServiceNow BrowserGym](https://github.com/ServiceNow/BrowserGym)。第三方集成证明采用情况，不意味着其改动后的分数可直接与原榜单比较。

## 2. 具体选什么、怎么用？

### τ-bench：第一优先，判断任务是否真正完成

选择官方文本任务，覆盖 airline、retail、telecom 三个业务域。优先使用完整的固定任务集合，不只取文件开头或只挑有趣案例。当前仓库已发布 v2.0.0，初轮采用该版本的英文文本范围；若不覆盖其完整多语言官方评测框架，必须明确写作英文子集，不能声称完整官方榜单成绩。

例如，用户要求取消符合条件的订单。评委要结合业务规则、用户授权、查询与取消工具返回，判断是否完成，不能只看最后一句“已取消”。

标准结果使用该版本的官方评价组件。必须分别保留数据库状态检查、沟通要求和自然语言断言等分项：其中有些是程序检查，有些依赖 LLM，不能一概称为“客观人工真值”。主报两类结果：评委与数据库状态检查的一致性，以及与官方完整任务判定的一致性。前者仅说明状态达成，不能代替完整业务合规。

官方参考动作序列是得到目标状态的一种路径，不是唯一正确步骤。不能因为 agent 没有照着参考动作逐字执行就判错。[官方计分说明](https://github.com/sierra-research/tau2-bench/blob/main/docs/evaluation.md)

版本边界：v2.0.0 改动了提示、用户模拟器和部分计分，官方明确说明不能直接与 1.x 比分。行业系统卡中的历史 τ²-bench 成绩证明其采用基础，不是本项目新版本可直接对照的分数。[官方版本说明](https://github.com/sierra-research/tau2-bench/releases)

### BFCL：第一优先，判断多轮工具操作是否正确

选择 BFCL 官方多轮类别：基础、缺少参数、缺少工具、长上下文，覆盖不同工具环境。采用 BFCL V4 发布体系下的固定数据与评价器；本轮只测多轮部分，不宣称 BFCL V4 全榜总分。版本和样本清单在运行前固定，以该版本实际文件为准，不混用早期博客与新版本的样本数量。

例如，用户信息不够时应该追问，而不是猜一个参数；工具执行成功也不代表文件被放到了正确位置。利用官方的状态及响应检查结果，检验评委能否判断每个受支持的轮次是否达标。[BFCL 多轮设计](https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html)

优先检查官方榜单链接的公开模型结果能否提供完整输入、调用和返回；缺失必要上下文的输出不能冒充完整 trace。需要时重新收集轨迹。标准答案和评价器结果只用于计分，不提供给评委。[官方结果归档](https://github.com/HuanzhiMao/BFCL-Result)

BFCL 的轮次检查结果不等于任意 assistant 步骤的人工 +1/0/−1 标签。只在原评价器支持的粒度上报告成绩，不能把一个最终失败标签传播给每一步。

### WebArena：补充网页操作，区分原版与修订版

WebArena 覆盖购物、内容管理、论坛和协作开发等网页任务，适合检验长操作链和虚假成功声明。使用所有评委都能接收的同一份文本观察记录：页面内容、动作、工具返回和最终答复；不能只给 GPT 截图而不给其它评委。[原始任务与观察设计](https://webarena.dev/og/)

主线认可度来自原版 WebArena。对于评价器质量，再单列 ServiceNow 的 WebArena-Verified 修订版：作者报告对任务、答案与评价器作了人工检查，提供 812 个任务、确定性计分以及基于网络记录的离线评价。它更适合检验评委是否认出任务完成，但修订版自己的采用规模较小，不能借原版的名气声称同等普及，也不能直接合并两版成绩。[WebArena-Verified](https://github.com/ServiceNow/webarena-verified)

优先收集完整轨迹；只有任务题目或最终分数不够。若先用官方 258 题 Hard 子集降低收集成本，单列子集成绩，不代表全体任务。离线重评仍需要相应网络记录，并不意味着无需运行就有完整轨迹。

## 3. 这些原本是 Agent 能力评测，怎样用来测评委？

新实验明确叫作“基于官方 Agent 基准轨迹的评委评价”，不冒充官方原生 judge 排行榜。

1. 从固定任务集合收集多个 agent 的完整轨迹，同时包含成功和失败；不以 Jev 是否判对来筛样本。
2. 由对应版本的官方评价器给每条轨迹或受支持轮次计算结果，保留不同判定来源。
3. 把相同任务、规则、工具与轨迹给 Jev、Clef、GPT；隐藏标准答案、成功标记、评价器日志、模型身份及携带结果的文件名。
4. 主对照只要求所有评委输出标签。GPT 的短解释另做消融，避免重复上一轮输出任务不同的问题。接口包装允许不同，核心规则与证据保持一致。
5. 报告成功/失败宏 F1、失败召回、把失败误判为成功的比例、费用，并按任务与域拆分。多次轨迹来自同一任务时，统计区间按任务聚类。

若完整记录不足以让评委判定实际终局状态，应单独报告证据不足情况，不能把“猜不到隐藏状态”当作普通推理错误。公开结果归档是否具备足够证据，必须在选定轨迹之前确认。

这测的是评委识别完成情况的能力。若要声称“Jev 能提高 agent 成功率”，还需保持同一个执行 agent 和任务预算，比较接入评委前后的实际成功率；不能直接从离线判对率推出。

## 4. 每一步的人工标签怎么办？

上述公认基准主要验证任务完成或工具状态，**并不天然带有每一步的人工好坏标签**。为了追求知名度而把它们包装成逐步人工评分集，会改变研究问题。

所以把两类证据分开：官方基准轨迹承担终局与可验证轮次的主实验；已有 AgentProcessBench 只承担逐步错误识别的补充分析。

如果要新增“评委与人是否一致”的网页轨迹证据，可补充 AgentRewardBench：COLM 2025 论文报告 1,302 条轨迹、五类基准、四种执行模型，人工检查成功、副作用和重复等维度。它与 judge 研究直接匹配，但不能称为业内普遍采用的主标准；完整数据量也不能直接当作测试划分大小。[会议论文](https://proceedings.colm.cc/paper_files/paper/2025/hash/e61219bcb30e2a78f0647bfafe7855ca-Abstract-Conference.html)

上一轮的 500 条 APB 轨迹来自 BFCL/τ²，但属于 APB 的生成、筛选和标注设置，不等于已经完成 BFCL 或 τ² 官方全量实验。已有结果有效范围不变，不改名、不换标签。

## 5. 为什么不直接换成其它名气更大的基准？

| 候选 | 本轮决定 | 原因 |
|---|---|---|
| Terminal-Bench | 后续终端场景扩展 | 有广泛模型评测采用基础，但偏终端执行；收集完整轨迹和处理评分漏洞是另一组实验 |
| SWE-bench Verified | 不作为当前新主实验 | 专门测软件修复；OpenAI 已公开指出其测试设计与污染问题，不能只凭历史知名度认定它更可靠 |
| OSWorld | 留作视觉扩展 | 当前项目采用文本评委对比；先解决各模型获得相同视觉证据的问题 |
| AgentRewardBench | 人工终局判断补充 | 直接匹配 judge，但采用规模不足以替代上述主基准 |
| AgentProcessBench | 保留历史逐步诊断 | 有逐步标签，但不单独支撑普遍性的模型排名 |

Terminal-Bench 的外部采用可见上述 Anthropic 系统卡；其官方也明确处理过投机得分问题。[Terminal-Bench 官方说明](https://www.tbench.ai/news/leaderboard-integrity-update)。SWE-bench 的问题见[OpenAI 的说明](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)。这些限制不等于基准无价值，而是说明“更知名”也需要选对任务与版本。

回答质量部分保留 **RewardBench 2**，可用 **RewardBench v1** 增加历史对照；JudgeBench 留作正确性诊断。Ai2 的官方发布与维护证明 RewardBench 不是一个仅凭论文名字拼出来的小众集。现有 1,763 题四选一继续明确标为非 Ties 子集，不改称官方完整总分。[Ai2 发布说明](https://allenai.org/blog/rewardbench-the-first-benchmark-leaderboard-for-reward-models-used-in-rlhf-1d4d7d04a90b)、[官方 v1/v2 代码与榜单入口](https://github.com/allenai/reward-bench)

## 6. Star 数量也列出来，但不冒用

以下为 2026-11-19 查询 GitHub API 得到的仓库计数，之后会变化。仓库不等于数据集，合并仓库的 star 不能全部归给其中一个基准。

| 仓库 | Star | 解释 |
|---|---:|---|
| [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) | 2,482 | τ-bench 官方仓库 |
| [ShishirPatil/gorilla](https://github.com/ShishirPatil/gorilla) | 13,079 | BFCL 所在的整个 Gorilla 项目，不是 BFCL 单独计数 |
| [web-arena-x/webarena](https://github.com/web-arena-x/webarena) | 1,645 | 原版 WebArena 仓库 |
| [ServiceNow/BrowserGym](https://github.com/ServiceNow/BrowserGym) | 1,444 | 集成多种网页基准的框架，不是 WebArena 自身 |
| [McGill-NLP/agent-reward-bench](https://github.com/McGill-NLP/agent-reward-bench) | 52 | 专门的评委数据集；不包装成高普及度基准 |
| [allenai/reward-bench](https://github.com/allenai/reward-bench) | 749 | Ai2 的 RewardBench 系列仓库 |

**执行顺序：τ-bench 文本 + BFCL 多轮 → WebArena → 人工判断补充。** 本次完成的是数据集选择与实验设计，没有启动新的付费模型评测。
