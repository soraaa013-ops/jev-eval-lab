# Jev Eval Lab 完整教程：研究问题、实现方法与设计取舍

这篇教程讲解项目如何搭建、实验如何推进、代码如何实现，以及每个重要选择背后的依据。适合希望读懂整个项目，或者沿着现有代码继续做实验的读者。

教程围绕“要解决什么问题、为什么这样设计、代码怎样实现、实验说明了什么”展开，重点解释各阶段的设计依据与取舍。

## 1. 项目究竟要回答什么问题？

Jev Eval Lab 研究的是**评委是否可靠**。输入可以是一道题的两个回答，也可以是 agent 完整的工具执行记录；输出是评委的选择或评分，再与已有标签比较。

这里至少有三个不同角色：

- 被评对象：候选回答或 agent 的执行步骤。
- 评委：Jev、Clef、生成式 LLM 或本地 reward model。
- 参照标签：benchmark 提供的正确候选或人工过程标注。

项目不训练 Jev，也没有实现它的内部神经网络。它实现的是数据准备、模型适配、请求执行、结果保存、统计分析和报告生成。对于托管模型，能观察的是请求、响应、版本与行为，不能由这些材料反推出完整内部架构。

研究问题逐渐分成两条线：

1. **回答质量**：评委能选出更好的回答吗？交换位置后稳定吗？概率是否可信？
2. **Agent 过程**：评委能判断工具使用是否推进任务、定位错误和识别最终失败吗？

两者不能互相替代。能挑对答案的模型，不一定能发现“工具执行成功，但修改了错误的目录”。

### 为什么同时比较质量、稳定性、费用和延迟？

如果只测准确率，就无法判断一个便宜但漏报很多错误的评委是否适合部署；如果只看费用，就不知道节省的成本换来了多少错误。项目因此保留多个维度，而没有将它们压缩成一个未经论证的总分。

类型化输出也不能保证语义正确。Choice 可以保证答案属于预设类别，但仍可能选错；生成式模型可以输出合法 JSON，也仍可能误解证据。

## 2. 项目是怎样逐步发展起来的？

项目从回答质量比较逐步扩展到真实 agent 的过程判断：

| 阶段 | 做了什么 | 解决的问题 |
|---|---|---|
| 建立核心框架 | 统一数据、模型接口和指标计算 | 用相同任务比较不同评委 |
| 扩展回答协议 | 增加 RewardBench 2 的 ranking 与 rating | 从二选一扩展到多候选评分与选择 |
| 增加本地模型 | 接入开放权重 reward model | 比较独立打分与直接选择的差异 |
| 探索 agent 评估 | 使用合成案例研究决策模型行为 | 理解缺失证据、选项变化等因素的影响 |
| 评价真实轨迹 | 在 AgentProcessBench 上比较三个评委 | 直接检验过程判断能力 |

这里最重要的研究推进方式是：**先明确已有证据能回答什么，再为尚未回答的问题增加实验。** 回答质量分数不能证明 agent 评估有效；合成探针也不能代替真实轨迹，因此后来增加 AgentProcessBench。

## 3. 用一条样本理解核心架构

核心代码只有四个模块，可以按以下顺序阅读：

| 文件 | 负责什么 | 优先看哪些函数或类型 |
|---|---|---|
| [core.py](../src/jev_eval/core.py) | 数据类型与 JSONL 读取 | `PairwiseItem`、`Judgment` |
| [adapters.py](../src/jev_eval/adapters.py) | 不同模型接口 | `JudgeAdapter`、三个具体 adapter |
| [cli.py](../src/jev_eval/cli.py) | 配置、调度、落盘、命令入口 | `validate`、`command_run`、`command_analyze` |
| [metrics.py](../src/jev_eval/metrics.py) | 从判断记录计算指标 | `compute_metrics` |

假设一条教学样本是：

```json
{"id":"sum-1","context":"2+2 等于多少？","response_a":"4","response_b":"5","label":"A","category":"math"}
```

`PairwiseItem.from_dict()` 检查必填字段，并把标签限制在 A/B。`load_jsonl()` 检查 ID 唯一性，错误时给出文件和行号。这样可以在付费请求之前发现基础数据问题。

`swapped()` 会同时交换候选文本和 gold 标签：原来的 A 正确，交换后就应是 B 正确；仅交换文本会污染答案。

```text
JSONL 样本
  → PairwiseItem
  → original / swapped 两个任务
  → JudgeAdapter.judge(item)
  → Judgment
  → results.jsonl
  → metrics.json
  → report.md
```

`Judgment` 把接口结果统一为 choice、A/B 概率、实际返回模型、延迟、usage、费用与 raw 数据。因此统计模块不需要知道某个模型走哪个 HTTP endpoint。

### 两类托管接口为什么分开？

Jev 的 Decisions adapter 发送 `state` 和预定义 `questions`。state 放 context 与两个候选；winner 是一个 Choice 问题，选项为 A/B。

Chat adapter 则把同样的题目和候选序列化成 user message，要求生成 `choice`、`probability_a`、`probability_b`，并提供严格 JSON Schema。这两个接口的请求结构和解析方式不同，复用同一个 HTTP 形状会掩盖真实差异。

[实验详解第 9 节](../report/experiment-report.md)记录过一个实际问题：原题本身有 A—J 选项，Qwen 曾输出题目的答案 D，而不是候选标签 A/B。修正后的提示明确要求选择 CANDIDATE A 或 CANDIDATE B，并使用 `pairwise-v2-candidate-label` 版本标记。非法输出被拒绝，失败 run 不进入正式统计。

设计上的教训是：**先把评估任务的输出语义定义清楚，再讨论模型分数。** 同一个字母在原题与评委协议中可能指不同对象。

## 4. 第一条实验线：JudgeBench 回答对比较

### 4.1 数据怎么来？

[prepare_judgebench.py](../scripts/prepare_judgebench.py)将 question、response_A、response_B 转为统一 schema，把 `A>B` / `B>A` 转为 A/B 标签。

本次选 GPT-4o response split，共 350 对。这里的 GPT-4o 指候选回答来源，不是本项目评委只有 GPT-4o。

三种托管评委各做 700 次判断；本地 Skywork 也保存 700 个方向记录，但交换方向来自同一对分数，不是又运行了一遍同样的模型推理。

### 4.2 为什么交换顺序？

设正确回答是“4”：

```text
original: A=4，B=5，gold=A
swapped:  A=5，B=4，gold=B
```

真正选择相同内容时，输出字母应该相反。因此：

```text
逐次 accuracy = 正确方向数 / 全部方向数
swap consistency = 两次 choice 不同的完整回答对数 / 完整回答对数
strict swap accuracy = 两个方向都正确的回答对数 / 完整回答对数
```

一个始终选 A 的模型，在每题双方向下会有 50% accuracy，但严格准确率为 0。一个始终选错内容的模型也能有 100% consistency，所以一致性必须配合正确率读。

### 4.3 概率指标怎样算？

令 `y=1` 表示 gold=A，否则 `y=0`，`p=P(A)`：

```text
Brier = mean((p-y)^2)
log loss = mean(-y·log(p) - (1-y)·log(1-p))
```

代码在计算 log loss 时裁剪概率，避免 log(0)。Brier 越低通常越好；例如 gold=A，p=0.9 的误差是 0.01，p=0.1 的误差是 0.81。

ECE 按“所选答案的概率”分箱，比较每箱平均概率与实际准确率，再按样本数加权。三个托管 JudgeBench 配置使用 15 箱，smoke 和已提交的本地 baseline 配置为 10 箱；统计绘图脚本的默认可靠性分箱也是 10。跨表比较时应说明这一差异，不能认为所有 ECE 都用了同一口径。

Jev 原生分布、LLM 自报概率与 reward score 经 sigmoid 转换的概率不是同一种生成机制。低 ECE 仅描述这份数据上的经验匹配程度。

### 4.4 本地 reward model 有什么不同？

[run_open_reward_model.py](../scripts/run_open_reward_model.py)分别对 prompt+A 和 prompt+B 打分，再用分数差选择候选，并计算 `sigmoid(score_A-score_B)`。交换候选只交换分数，因此 100% 一致性来自机制，不代表模型更理解问题。

已提交 Skywork baseline 使用 CPU float32、256-token 上限与左侧截断。短上下文可能删掉关键证据，因此这个结果不是该模型完整上下文能力的上限。

### 4.5 如何读已有结果？

| 模型 | 逐次准确率 | 严格双顺序准确率 | 顺序一致率 |
|---|---:|---:|---:|
| GPT-5 mini | 85.71% | 80.57% | 89.71% |
| Jev 1.14 | 78.14% | 70.57% | 84.86% |
| Qwen3-30B-A3B | 64.29% | 40.00% | 51.43% |
| Skywork 0.6B，256 tokens | 60.29% | 60.29% | 100.00% |

数据入口是 [结果台账](../artifacts/README.md)。Jev 本轮较 GPT-5 mini 便宜、快，但准确率低；Qwen 的双顺序结果暴露位置敏感性；Skywork 的一致性不能脱离其计算机制解释。

## 5. 第二种回答协议：RewardBench 2

RewardBench 2 原生包含多个候选及 Ties，不能无损地塞进“唯一正确 A/B”的 schema。所以项目使用专用 runner，而不是为了复用框架改变任务含义。

### Rating：给每个候选打分

[run_rewardbench2_jev_rating.py](../scripts/run_rewardbench2_jev_rating.py)在同一个 state 中放候选，为每个候选提出一个五档 Score 问题。一次请求返回多个评分。

分数是 0—4 rubric 索引的概率期望；文案虽使用人类可读的 1—5 档，也不应该把 score 再当成另一种 1—5 原始量。输出 scores 按“所有 chosen，然后所有 rejected”排列，`num_correct` 是分界。

[分析脚本](../scripts/analyze_rewardbench2_rating.py)计算：

- top-1：最高分候选中至少有一个 chosen；与 rejected 并列最高也可能计对。
- strict ranking：所有 chosen 都严格高于所有 rejected。
- derived pairwise：枚举 chosen–rejected 对，统计严格大于的比例。

例如 chosen=0.8，rejected=[0.8,0.2,0.1]，top-1 算对，strict 算错，pairwise 为 2/3。这三个数字回答不同问题。

### Ranking：直接选择最好候选

[run_rewardbench2_jev_ranking.py](../scripts/run_rewardbench2_jev_ranking.py)处理 1,763 条非 Ties 样本，每条一个 chosen、三个 rejected。根据 `SHA256(id) mod 4` 对候选做确定性轮转，避免正确候选总在 A。

这种轮转没有覆盖所有 24 种排列，因此并不是全面的位置测试。Ties 的 102 条进入 rating，不进入唯一赢家选择。

### Ties 为什么需要单独公式？

102 条构成 51 组 ref/tied prompt。分析比较正确候选内部间隔，以及正确候选与错误候选之间的间隔，再结合准确率与 margin bonus。完整实现见 rating analyzer；公式与解释见 [实验详解第 13 节](../report/experiment-report.md)。

项目沿用该聚合公式，但 Jev 使用的是自定义五档 Score rubric。这些分数不属于官方 leaderboard 成绩；报告中的 80.49% 研究性宏平均也不能与其它协议直接排名。

这一部分的价值是发现**提问方式本身会改变结果**：例如已有报告中 Safety 的 ranking 为 87.78%，rating top-1 为 66.44%。这不能解释为模型突然变强或变弱，而是需要进一步研究整体比较与独立打分的差异。当前 RewardBench 2 只有 Jev，不能从这里得出跨模型胜负。

## 6. 为什么从回答评估走向真实 agent 轨迹？

回答 benchmark 检查的是“哪个答案更好”，agent 过程判断还要处理时间顺序、工具结果、任务约束和错误传播。例如一句“文件已创建”本身很流畅，但是否正确取决于工具实际在哪个路径创建了文件。

项目曾用合成案例研究选项反转、缺失证据等行为。这类小实验有助于理解模型对输入变化的反应，但缺少真实任务中的长程依赖和复杂工具交互。因此，后续实验转向 AgentProcessBench，用真实轨迹及人工过程标签直接比较评委。

## 7. 最新主线：如何让三个评委评价同一条 agent 轨迹？

### 7.1 先固定研究范围

[prepare_agentprocessbench.py](../scripts/prepare_agentprocessbench.py)准备 APB 的 BFCL、tau2 两个子集。每个子集各 250 条轨迹，共 500 条、6,147 个 assistant 步骤；每个底层问题有 5 条轨迹，共 100 个问题。

这是两个完整子集，不是完整 APB 排行榜，也没有重新运行产生这些轨迹的 agent。研究对象是“对既有执行记录的评判”。

### 7.2 构造盲评证据，而不是把整行直接发给模型

[run_agentprocessbench.py](../scripts/run_agentprocessbench.py)的 `evidence()` 采用白名单：

```text
question + task_description + tools
+ 带原消息编号的 messages
+ assistant_message_indices
```

它不传独立字段中的人工标签、参考答案、`tool_metrics`、`answer_text`。但轨迹本身的 assistant 回答仍属于证据，不会因为里面有答案文字而删除。

保留原消息编号非常重要：工具消息与用户消息参与理解，但只给 assistant 消息评分。输出 `step_5` 指原 messages 中的第 5 号消息，不是第五个 assistant 步骤。

### 7.3 统一评分语义，保留输出机制差异

三种标签为：

- +1：根据当时证据正确，并有效推进任务。
- 0：合理探索、中性或部分规划；合理工具尝试遭遇外部失败也可能属于此类。
- −1：事实错误、伪造证据、误读工具结果、违反约束、没有有效变化的重复失败。

Rubric 还规定错误传播：依赖未纠正错误的后续步骤受罚，明确纠正或独立恢复后可解除。工具失败不能机械地等于 agent 错误，工具成功也不能机械地等于任务成功。

Jev 与 Clef 为每个 assistant index 建立 Choice 问题，再增加 final 二分类问题。GPT-5 mini 生成 JSON 的 `step_labels`、`final_label` 和简短解释，使用 low reasoning。这里的 GPT 请求是 `json_object`，不是通用 pairwise adapter 的严格 JSON Schema。

`parse()` 检查消息编号集合精确匹配，标签是合法整数，再统一为数值标签。解释字段不是主评分输入，当前 parser 也没有严格核验每步解释是否齐全。

### 7.4 长轨迹如何处理？

预检中 Clef 拒绝了一次 96 个问题的请求，接口上限为 64。正式 runner 将决策问题按最多 64 个分批，**每批保留完整相同轨迹证据**，最后合并 answers。

分批减少单次问题数，没有截断轨迹，也没有消除总 token 上限风险。多个批次会重复输入证据，影响成本和延迟。

### 7.5 失败如何处理？

每条轨迹最多尝试 3 次，失败后退避等待。达到上限后将该轨迹记为终止失败，不无限重试；其缺失预测在主指标中按错处理。

正式执行使用 12 个线程。某个后续批次失败时，下一次 attempt 会重新执行整条轨迹的批次，费用分析需要保留先前已完成的部分。不能仅按“成功轨迹数量 × 单价”估算花费。

这也说明为何当前主实验用专用脚本：它需要逐步多标签、批次合并、有限重试与失败留痕，已超出最初 A/B runner 的接口。

## 8. Agent 指标为什么这样设计？

### 8.1 准确率很容易被多数类抬高

gold 中有 4,236 个 +1、231 个 0、1,680 个 −1。始终猜 +1 就有 68.91% accuracy，但完全发现不了错误。

因此主指标选宏 F1：对三类分别计算 `F1=2TP/(2TP+FP+FN)`，再等权平均。它不会让 +1 类仅因为数量多就完全主导结果；同时仍需看每类指标，因为中性类很少。

```text
错误召回 = 正确识别为 −1 的错误步骤 / 所有 gold=−1 步骤
错误误报率 = 被预测为 −1 的 gold∈{0,+1} 步骤 / 所有 gold∈{0,+1} 步骤
```

### 8.2 缺失输出不能从分母消失

[analyze_agentprocessbench.py](../scripts/analyze_agentprocessbench.py)建立 3×4 混淆矩阵：gold 行是 −1/0/+1，预测列是 −1/0/+1/missing。missing 保留在 gold 分母中，不能贡献正确数。

1,500 份模型×轨迹任务最终有 1,497 份完整输出。Clef 三条终止失败导致 264 个步骤标签缺失；主指标将它们按错计。额外比较三模型均完成的 497 条轨迹是事后敏感性分析，不替代主指标。

### 8.3 为什么按问题做 bootstrap？

同一轨迹的步骤有关联，同一问题的五条轨迹也有关联。把 6,147 个步骤当作独立样本，可能夸大有效样本量。

代码以 `(dataset, query_index)` 为 cluster，抽取 100 个问题组，保留组内所有轨迹与步骤；固定种子 20261116，重复 2,000 次。每次先合并混淆矩阵再计算指标。三个评委使用同一组抽样索引，因此差值区间是配对比较。

JudgeBench 则以 item 为 cluster，保持 original/swapped 一起抽样，默认 10,000 次。两条实验线的独立单位不同，不能共享一个“样本量”解释。

### 8.4 终局标签暴露了什么问题？

分析时发现 20 条 gold 的 `final_label=0`，但沿用的终局提示只允许 ±1。主逐步任务仍使用全部 500 条；辅助终局二分类只在其余 480 条上计算。同时保留全 500 条精确匹配率，并披露这是事后口径修正。

从这个事件得到的可执行经验是：未来冻结协议前应检查**全部标签取值及数量**，不要只通过几条 smoke 来判断标签空间完整。

### 8.5 如何解读已有结果？

| 评委 | 宏 F1 | 逐步准确率 | 错误召回 | 错误误报率 |
|---|---:|---:|---:|---:|
| Jev 1.14 | 50.45% | 77.13% | 34.35% | 2.22% |
| Clef-flash | 42.45% | 66.15% | 16.79% | 2.08% |
| GPT-5 mini | 37.57% | 71.22% | 13.45% | 1.32% |
| 始终 +1 | 27.20% | 68.91% | 0% | 0% |

来源：[已提交指标](../artifacts/agentprocessbench/metrics.json)及 [结果报告](../report/agent-judge-benchmark.md)。Jev 相对 GPT 的宏 F1 高 12.88 个百分点，配对区间为 [9.10,16.41] 个百分点。但 Jev 仍漏掉约三分之二错误，不能因为排名第一就成为唯一拦截器。

这与 JudgeBench 的 GPT 准确率领先并不矛盾：任务、标签、提示和预算不同。这里证明的是特定协议下的结果，不是某种架构在所有评估任务上普遍优胜。

### 8.6 用一个案例把机制串起来

`bfcl:0:0` 要求在 workspace 内创建 Projects。工具表明当前目录是 `/alex`，agent 却直接创建 Projects，之后列表显示 workspace 与 Projects 并列。

工具成功只能证明创建操作完成，不能证明路径符合用户要求。人工把创建步骤与后续错误成功声明标为 −1；Jev 识别了创建步骤的错误，但三个评委都未识别后续成功声明。原始证据见 [cases.json](../artifacts/agentprocessbench/cases.json)。

案例能解释“判断必须绑定目标与证据”，不能独自证明模型排名；排名来自完整数据。它还是事后选择的示例，应与预先固定的主指标分开。

## 9. 如何继续扩展这个项目？

### 增加一个 A/B 评委

遵循 [adding-models.md](adding-models.md)：实现 `JudgeAdapter.judge()`，返回统一 Judgment，在 `make_adapter()` 注册，用新 TOML 与新输出目录运行。先用少量已知样本确认标签含义、概率字段和异常行为，再跑冻结集合。

配置替换仅适用于同一种协议。若新模型返回的是多候选 score 或轨迹标签，就需要相应的数据契约和分析器，不能强行映射为 A/B 后假装任务没有变化。

### 增加一套真实 agent 评估

先定义可观察证据与标签，再决定评委形式：

1. 明确任务完成的外部标准，例如文件路径、订单字段或测试结果。
2. 明确步骤粒度与中性探索含义，明确全部标签取值。
3. 白名单构造模型输入，把 gold 留在离线分析侧。
4. 确定 rubric、失败处理和统计单位。
5. 在独立校准集选阈值或人工复审策略，再评估冻结测试集。
6. 若目标是改善 agent，另做相同任务与预算下的在线对照，衡量最终成功、副作用、恢复率和总成本。

这些是后续实验方法，不是本仓库已经完成的功能。当前没有训练评委、验证线上转交策略，也没有证明过程评分能提高 agent 成功率。

## 10. 延伸阅读

| 你想弄清楚什么 | 去哪里 |
|---|---|
| 核心框架怎样实现 | [src/jev_eval](../src/jev_eval/) |
| 回答实验每个协议的完整解释 | [experiment-report.md](../report/experiment-report.md) |
| JudgeBench/RB2 逐条结果与规模 | [artifacts/README.md](../artifacts/README.md) |
| 统计区间、可靠性图和错误清单 | [artifacts/analysis](../artifacts/analysis/) |
| 真实 agent 实验的评分规则及补充说明 | [PROTOCOL.md](../artifacts/agentprocessbench/PROTOCOL.md) |
| Agent 结果与限制的易读解释 | [agent-judge-benchmark.md](../report/agent-judge-benchmark.md) |
