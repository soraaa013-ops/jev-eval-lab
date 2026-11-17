# Jev Eval Lab 完整教程：从研究问题到可复核的评估实验

这篇教程讲解项目如何搭建、实验如何推进、代码如何实现，以及每个重要选择背后的依据。适合希望读懂整个项目、复核结果，或者沿着现有代码继续做实验的读者。

本文依据截至 `ca68bd8` 的代码、Git 历史、协议和实验工件编写。文中的“为什么这样做”是可检查的设计理由；有记录的开发事件会注明出处。没有记录的部分只解释实现的作用，不把事后解释写成作者当时的心理活动或逐步内部思维记录。本文没有重新训练或调用付费模型。

建议按顺序阅读。只想动手，可以先看第 3、12 节；关心最新 agent 实验，可以先看第 8—10 节。

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

下面是 Git 历史可支持的阶段，不是每一次编辑的完整时间线。可在仓库运行 `git log --reverse --oneline` 自行核对。

| 阶段与提交 | 做了什么 | 解决的问题 |
|---|---|---|
| `81d5b42` | 建立可复现评估研究的初始版本 | 用统一数据与结果格式跑通评委实验 |
| `bbe3dab` | 补充 RewardBench 2 的完整协议和结果 | 从二选一扩展到多候选评分与选择 |
| `53db98d`—`a87248f` | 扩充数据审计、实验详解、协议出处 | 区分上游标准与本项目自定义适配 |
| `7f78647` | 完成研究并增加开放权重 reward baseline | 加入本地独立打分机制和统计比较 |
| `ba80739`、`176f806` | 制作一页汇报，补充 System One 与 agent 路线 | 将回答评估放到更大的应用问题中解释 |
| `a1c37d3` | 核查实现、复算外部证据、运行本地探针 | 区分模型宣传、外部结果和本机实测 |
| `ca68bd8` | 运行真实 agent 轨迹的三评委比较 | 直接检验过程判断能力 |

这里最重要的研究推进方式是：**先明确已有证据能回答什么，再为尚未回答的问题增加实验。** 回答质量分数不能证明 agent 评估有效；合成探针也不能代替真实轨迹，因此后来增加 AgentProcessBench。

旧文档需要结合阶段读。例如 [System One 验证记录](../artifacts/validation/system-one/README.md)末尾“未完成”的 APB 实验描述属于那个阶段；后续完成状态以 [agent 实验记录](../artifacts/agentprocessbench/README.md)为准。

## 3. 先跑一次最小实验

以下命令都在仓库根目录执行。要求 Python 3.11 及以上；核心框架只有标准库依赖。可以使用已有虚拟环境；新环境的安装方式是：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

然后执行不需要密钥的完整链路：

```bash
jev-eval validate --config configs/experiments/smoke.toml
jev-eval run --config configs/experiments/smoke.toml
jev-eval analyze --run-dir artifacts/runs/smoke
jev-eval report --run-dir artifacts/runs/smoke
```

四步分别负责：

1. 检查配置、读取数据、拒绝重复 ID，并输出数据哈希。
2. 生成原顺序与交换顺序任务，调用 mock，逐行保存结果。
3. 从已有结果计算指标，写入 `metrics.json`。
4. 把指标变成 `report.md`。

输出目录还包含 `manifest.json` 与 `config.resolved.json`。再次执行 `run`，相同请求会显示 `cached`。一键入口 `make smoke` 还会先运行测试。

**Mock 的满分只说明管道工作。** [MockAdapter](../src/jev_eval/adapters.py)直接读取样本标签，构造 0.9/0.1 概率；它不能用来证明模型能力，也不能作为真实 benchmark 的竞争 baseline。

### 一个配置控制哪些内容？

[smoke.toml](../configs/experiments/smoke.toml)的结构是：

```toml
[experiment]
name = "smoke"
dataset = "data/samples/pairwise.jsonl"
output_dir = "artifacts/runs/smoke"
swap_positions = true
limit = 0

[model]
adapter = "mock"
id = "deterministic/mock-v1"

[metrics]
ece_bins = 10
```

`limit=0` 表示不截取样本；`swap_positions=true` 表示每题有两个方向。相对路径以找到的 `pyproject.toml` 所在目录为基准，而不是随意依赖启动目录。

新实验应使用新的名称和输出目录。改模型后继续往旧结果目录写，会让不同协议混在同一份结果中；哈希去重不等于实验隔离。

## 4. 用一条样本理解核心架构

核心代码只有四个模块，可以按以下顺序阅读：

| 文件 | 负责什么 | 优先看哪些函数或类型 |
|---|---|---|
| [core.py](../src/jev_eval/core.py) | 数据类型、JSONL、哈希 | `PairwiseItem`、`Judgment`、`stable_hash` |
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

## 5. 为什么保存逐条结果，而不是只保存准确率？

总准确率无法回答“模型看到了什么”“解析有没有错”“是否混入了不同版本”。因此 JudgeBench 每一行保留 `raw.request` 与 `raw.response`，以及用于关联的 item ID、方向和请求 ID。

### 请求身份如何产生？

通用 runner 对以下对象进行排序键、紧凑 JSON 序列化，然后计算 SHA-256：

```text
{item: 完整 PairwiseItem, orientation: 当前方向, model: 完整模型配置}
```

同一内容生成同一个 ID，启动时据此跳过已保存任务。这里包含 gold 是本地缓存实现；真正发送给托管评委的 payload 不包含 gold。

每完成一个 future，主线程追加一行并 flush。完成顺序由并发决定，不能依赖 JSONL 的物理行号对齐模型；应该使用 `item_id + orientation`。

### 这个机制有哪些边界？

- JSONL 只保存已经落盘的请求。进程在服务端完成后、写盘前中断，重跑仍可能重复付费。
- 通用 runner 的哈希没有自动包含 adapter 源码。硬编码 prompt 改动时，需要更新版本标记并使用新目录。
- 通用 runner 每次启动会写 manifest；它没有全面拒绝旧目录中混入的新协议。
- 通用 runner 遇到异常会尝试取消其他任务并抛错，但已经开始的并发请求未必停止，也不一定都被保存。
- 当前概率验证并不全面：chat schema 要求范围，但本地没有统一强制检查概率和为 1；Decisions parser 的历史兼容分支还可能从 confidence 补概率。审计时要检查实际响应字段，不能把所有 confidence 都视为赢家概率。

这些是当前实现的实际边界，不应被“可复现”三个字遮住。已有实验可复算，不代表 runner 已是完整的生产任务系统。

### 不同实验的审计能力并不完全相同

| 路径 | 保存和续跑方式 |
|---|---|
| 通用 pairwise | 请求哈希缓存，保存完整 raw request/response |
| RewardBench 2 | 专用脚本按样本 ID 跳过；rating 保留 answers，ranking 保留 choice/概率等字段，没有统一 raw 封套 |
| 本地 reward model | manifest 校验模型、revision、数据和上下文配置，拒绝混用 |
| AgentProcessBench | manifest 固定逻辑请求哈希，保留 attempts、分批响应、失败记录；主实验终止失败也缓存 |

所以不要假设所有 `results.jsonl` 都能用同一个 analyzer，也不要把 pairwise 的缓存保证推广到 RewardBench 2。

## 6. 第一条实验线：JudgeBench 回答对比较

### 6.1 数据怎么来？

[prepare_judgebench.py](../scripts/prepare_judgebench.py)使用固定上游 revision，将 question、response_A、response_B 转为统一 schema，把 `A>B` / `B>A` 转为 A/B 标签，保留来源信息。数据版本与转换后 SHA-256 见 [数据出处](dataset-provenance.md)。

本次选 GPT-4o response split，共 350 对。这里的 GPT-4o 指候选回答来源，不是本项目评委只有 GPT-4o。

三种托管评委各做 700 次判断；本地 Skywork 也保存 700 个方向记录，但交换方向来自同一对分数，不是又运行了一遍同样的模型推理。

### 6.2 为什么交换顺序？

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

### 6.3 概率指标怎样算？

令 `y=1` 表示 gold=A，否则 `y=0`，`p=P(A)`：

```text
Brier = mean((p-y)^2)
log loss = mean(-y·log(p) - (1-y)·log(1-p))
```

代码在计算 log loss 时裁剪概率，避免 log(0)。Brier 越低通常越好；例如 gold=A，p=0.9 的误差是 0.01，p=0.1 的误差是 0.81。

ECE 按“所选答案的概率”分箱，比较每箱平均概率与实际准确率，再按样本数加权。三个托管 JudgeBench 配置使用 15 箱，smoke 和已提交的本地 baseline 配置为 10 箱；统计绘图脚本的默认可靠性分箱也是 10。跨表比较时应说明这一差异，不能认为所有 ECE 都用了同一口径。

Jev 原生分布、LLM 自报概率与 reward score 经 sigmoid 转换的概率不是同一种生成机制。低 ECE 仅描述这份数据上的经验匹配程度。

### 6.4 本地 reward model 有什么不同？

[run_open_reward_model.py](../scripts/run_open_reward_model.py)分别对 prompt+A 和 prompt+B 打分，再用分数差选择候选，并计算 `sigmoid(score_A-score_B)`。交换候选只交换分数，因此 100% 一致性来自机制，不代表模型更理解问题。

已提交 Skywork baseline 使用 CPU float32、256-token 上限与左侧截断。脚本默认上限是 2048；复现已提交条件必须显式传 `--max-length 256`。短上下文可能删掉关键证据，因此这个结果不是该模型完整上下文能力的上限。

### 6.5 如何读已有结果？

| 模型 | 逐次准确率 | 严格双顺序准确率 | 顺序一致率 |
|---|---:|---:|---:|
| GPT-5 mini | 85.71% | 80.57% | 89.71% |
| Jev 1.14 | 78.14% | 70.57% | 84.86% |
| Qwen3-30B-A3B | 64.29% | 40.00% | 51.43% |
| Skywork 0.6B，256 tokens | 60.29% | 60.29% | 100.00% |

数据入口是 [结果台账](../artifacts/README.md)。Jev 本轮较 GPT-5 mini 便宜、快，但准确率低；Qwen 的双顺序结果暴露位置敏感性；Skywork 的一致性不能脱离其计算机制解释。

## 7. 第二种回答协议：RewardBench 2

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

轮转可复现，但不是对所有 24 种排列做全面位置测试。Ties 的 102 条进入 rating，不进入唯一赢家选择。

### Ties 为什么需要单独公式？

102 条构成 51 组 ref/tied prompt。分析比较正确候选内部间隔，以及正确候选与错误候选之间的间隔，再结合准确率与 margin bonus。完整实现见 rating analyzer；公式与解释见 [实验详解第 13 节](../report/experiment-report.md)。

项目沿用该聚合公式，但 Jev 使用的是自定义五档 Score rubric。官方数据与公式，不等于官方 leaderboard 复现；报告中的 80.49% 研究性宏平均也不能与其它协议直接排名。

这一部分的价值是发现**提问方式本身会改变结果**：例如已有报告中 Safety 的 ranking 为 87.78%，rating top-1 为 66.44%。这不能解释为模型突然变强或变弱，而是需要进一步研究整体比较与独立打分的差异。当前 RewardBench 2 只有 Jev，不能从这里得出跨模型胜负。

## 8. 为什么还需要 System One 核查与真实 agent 数据？

回答 benchmark 之后，还有两个问题：其它决策模型究竟提供什么实现？这些判断能力能迁移到 agent 过程吗？项目把证据分为不同层次：

| 工作 | 能支持什么 | 不能替代什么 |
|---|---|---|
| 固定 revision、配置和代码哈希 | 确认核查了哪个工件 | 性能测试 |
| 复算外部 2,100 个配对案例 | 检查已有结果的聚合与标签处理 | 本项目重新推理、重新标注 |
| Laya 60 次、d3-edge 36 次正式合成探针 | 诊断选项反转、缺失证据等行为 | 真实 agent benchmark |
| APB 500 条真实轨迹 | 与人工过程标签比较 | 在线干预收益 |

具体脚本为 `verify_system_one_catalog.py`、`audit_system_one_evidence.py`、`probe_system_one.py`。本地模型依赖彼此不同，实际环境记录在各自 manifest，不应直接把所有依赖装进同一个研究环境。

d3 的初次长输入探索完成 5 条后因 CPU 耗时中断，记录保留在 exploratory 目录，没有把未完成计划包装成正式实验。这样的失败记录说明了资源限制，也避免只呈现顺利完成的部分。

## 9. 最新主线：如何让三个评委评价同一条 agent 轨迹？

### 9.1 先固定研究范围

[prepare_agentprocessbench.py](../scripts/prepare_agentprocessbench.py)固定 APB revision，并验证 BFCL、tau2 文件 SHA-256。各 250 条轨迹，共 500 条、6,147 个 assistant 步骤；每个底层问题有 5 条轨迹，共 100 个问题。

这是两个完整子集，不是完整 APB 排行榜，也没有重新运行产生这些轨迹的 agent。研究对象是“对既有执行记录的评判”。

### 9.2 构造盲评证据，而不是把整行直接发给模型

[run_agentprocessbench.py](../scripts/run_agentprocessbench.py)的 `evidence()` 采用白名单：

```text
question + task_description + tools
+ 带原消息编号的 messages
+ assistant_message_indices
```

它不传独立字段中的人工标签、参考答案、`tool_metrics`、`answer_text`。但轨迹本身的 assistant 回答仍属于证据，不会因为里面有答案文字而删除。

保留原消息编号非常重要：工具消息与用户消息参与理解，但只给 assistant 消息评分。输出 `step_5` 指原 messages 中的第 5 号消息，不是第五个 assistant 步骤。

测试通过放入 `SECRET_GOLD` 等哨兵字段，确认这些字段不会进入 payload。这检验的是字段隔离，不能证明公开 benchmark 不存在训练污染。

### 9.3 统一评分语义，保留输出机制差异

三种标签为：

- +1：根据当时证据正确，并有效推进任务。
- 0：合理探索、中性或部分规划；合理工具尝试遭遇外部失败也可能属于此类。
- −1：事实错误、伪造证据、误读工具结果、违反约束、没有有效变化的重复失败。

Rubric 还规定错误传播：依赖未纠正错误的后续步骤受罚，明确纠正或独立恢复后可解除。工具失败不能机械地等于 agent 错误，工具成功也不能机械地等于任务成功。

Jev 与 Clef 为每个 assistant index 建立 Choice 问题，再增加 final 二分类问题。GPT-5 mini 生成 JSON 的 `step_labels`、`final_label` 和简短解释，使用 low reasoning。这里的 GPT 请求是 `json_object`，不是通用 pairwise adapter 的严格 JSON Schema。

`parse()` 检查消息编号集合精确匹配，标签是合法整数，再统一为数值标签。解释字段不是主评分输入，当前 parser 也没有严格核验每步解释是否齐全。

### 9.4 长轨迹如何处理？

预检中 Clef 拒绝了一次 96 个问题的请求，接口上限为 64。正式 runner 将决策问题按最多 64 个分批，**每批保留完整相同轨迹证据**，最后合并 answers。

分批减少单次问题数，没有截断轨迹，也没有消除总 token 上限风险。多个批次会重复输入证据，影响成本和延迟。逻辑轨迹请求 hash 与每个 HTTP part 的 hash 都保留，便于检查实际拆分。

### 9.5 失败如何处理？

每条轨迹最多尝试 3 次，失败后退避等待；输出包含每次 attempt、HTTP part、错误和累计耗时。主实验缓存终止失败，避免 resume 无限制重试。预检保存在 `smoke.jsonl`，主实验保存在 `results.jsonl`，不混算。

正式执行使用 12 个线程。某个后续批次失败时，下一次 attempt 会重新执行整条轨迹的批次，费用分析需要保留先前已完成的部分。不能仅按“成功轨迹数量 × 单价”估算花费。

这也说明为何当前主实验用专用脚本：它需要逐步多标签、批次合并、有限重试与失败留痕，已超出最初 A/B runner 的接口。

## 10. Agent 指标为什么这样设计？

### 10.1 准确率很容易被多数类抬高

gold 中有 4,236 个 +1、231 个 0、1,680 个 −1。始终猜 +1 就有 68.91% accuracy，但完全发现不了错误。

因此主指标选宏 F1：对三类分别计算 `F1=2TP/(2TP+FP+FN)`，再等权平均。它不会让 +1 类仅因为数量多就完全主导结果；同时仍需看每类指标，因为中性类很少。

```text
错误召回 = 正确识别为 −1 的错误步骤 / 所有 gold=−1 步骤
错误误报率 = 被预测为 −1 的 gold∈{0,+1} 步骤 / 所有 gold∈{0,+1} 步骤
```

### 10.2 缺失输出不能从分母消失

[analyze_agentprocessbench.py](../scripts/analyze_agentprocessbench.py)建立 3×4 混淆矩阵：gold 行是 −1/0/+1，预测列是 −1/0/+1/missing。missing 保留在 gold 分母中，不能贡献正确数。

1,500 份模型×轨迹任务最终有 1,497 份完整输出。Clef 三条终止失败导致 264 个步骤标签缺失；主指标将它们按错计。额外比较三模型均完成的 497 条轨迹是事后敏感性分析，不替代主指标。

### 10.3 为什么按问题做 bootstrap？

同一轨迹的步骤有关联，同一问题的五条轨迹也有关联。把 6,147 个步骤当作独立样本，可能夸大有效样本量。

代码以 `(dataset, query_index)` 为 cluster，抽取 100 个问题组，保留组内所有轨迹与步骤；固定种子 20261116，重复 2,000 次。每次先合并混淆矩阵再计算指标。三个评委使用同一组抽样索引，因此差值区间是配对比较。

JudgeBench 则以 item 为 cluster，保持 original/swapped 一起抽样，默认 10,000 次。两条实验线的独立单位不同，不能共享一个“样本量”解释。

### 10.4 终局标签暴露了什么问题？

分析时发现 20 条 gold 的 `final_label=0`，但沿用的终局提示只允许 ±1。主逐步任务仍使用全部 500 条；辅助终局二分类只在其余 480 条上计算。同时保留全 500 条精确匹配率，并披露这是事后口径修正。

从这个事件得到的可执行经验是：未来冻结协议前应检查**全部标签取值及数量**，不要只通过几条 smoke 来判断标签空间完整。

### 10.5 如何解读已有结果？

| 评委 | 宏 F1 | 逐步准确率 | 错误召回 | 错误误报率 |
|---|---:|---:|---:|---:|
| Jev 1.14 | 50.45% | 77.13% | 34.35% | 2.22% |
| Clef-flash | 42.45% | 66.15% | 16.79% | 2.08% |
| GPT-5 mini | 37.57% | 71.22% | 13.45% | 1.32% |
| 始终 +1 | 27.20% | 68.91% | 0% | 0% |

来源：[已提交指标](../artifacts/agentprocessbench/metrics.json)及 [结果报告](../report/agent-judge-benchmark.md)。Jev 相对 GPT 的宏 F1 高 12.88 个百分点，配对区间为 [9.10,16.41] 个百分点。但 Jev 仍漏掉约三分之二错误，不能因为排名第一就成为唯一拦截器。

这与 JudgeBench 的 GPT 准确率领先并不矛盾：任务、标签、提示和预算不同。这里证明的是特定协议下的结果，不是某种架构在所有评估任务上普遍优胜。

### 10.6 用一个案例把机制串起来

`bfcl:0:0` 要求在 workspace 内创建 Projects。工具表明当前目录是 `/alex`，agent 却直接创建 Projects，之后列表显示 workspace 与 Projects 并列。

工具成功只能证明创建操作完成，不能证明路径符合用户要求。人工把创建步骤与后续错误成功声明标为 −1；Jev 识别了创建步骤的错误，但三个评委都未识别后续成功声明。原始证据见 [cases.json](../artifacts/agentprocessbench/cases.json)。

案例能解释“判断必须绑定目标与证据”，不能独自证明模型排名；排名来自完整数据。它还是事后选择的示例，应与预先固定的主指标分开。

## 11. 可复现到底意味着什么？

项目区分两层：

1. **分析复现**：用已提交的原始或逐条结果重新计算指标，不需要 API 密钥。
2. **推理重跑**：用冻结数据、提示和模型 ID 再次请求服务。托管后端可能变化，不能保证响应逐位相同。

数据 revision 固定来源版本，文件 SHA-256 固定字节；请求 hash 固定序列化内容；返回 model 字段记录服务实际声明的版本。它们分别提供不同证据，不能互相替代。

费用来自响应 usage，并不覆盖未知收费。Agent analyzer 按 attempts 中的 parts 累加报告费用，避免同时累加合并外层 usage 而重复记账。没有 usage 的失败是否收费未知。

延迟也要看定义：pairwise 是 HTTP 请求耗时；APB 是包含批次和重试的轨迹耗时，不含线程排队。不能把不同请求粒度的 p50 直接解释成模型纯推理速度。

最后，静态完整轨迹仍可能带来后见偏差：即使 rubric 要求只依据当时信息，模型实际看到了后续内容。若要证明在线拦截有效，需要仅提供轨迹前缀重新验证，并另跑闭环对照。

## 12. 动手复核：从记录重新得到数字

### 12.1 不修改已提交结果，重算 JudgeBench 与 RewardBench 2

先激活虚拟环境。在根目录执行：

```bash
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from jev_eval.core import read_jsonl
from jev_eval.metrics import compute_metrics
p = Path('artifacts/runs/judgebench-jev-1.14')
manifest = json.loads((p / 'manifest.json').read_text())
bins = manifest['config'].get('metrics', {}).get('ece_bins', 10)
print(json.dumps(compute_metrics(list(read_jsonl(p / 'results.jsonl')), bins), indent=2))
PY

python scripts/analyze_rewardbench2_rating.py \
  --results artifacts/runs/rewardbench2-jev-rating/results.jsonl \
  --output /tmp/jev-tutorial-rating.json

python scripts/analyze_rewardbench2_ranking.py \
  --results artifacts/runs/rewardbench2-jev-ranking/results.jsonl \
  --output /tmp/jev-tutorial-ranking.json
```

如果希望更新 run 内的派生指标，可使用 `jev-eval analyze --run-dir ...`；它会写入该目录的 metrics。`report` 命令随后读取 metrics，而不会自动重新执行分析。

统计区间和图可以写到临时目录：

```bash
PYTHONPATH=src python scripts/analyze_statistics.py \
  --run jev=artifacts/runs/judgebench-jev-1.14 \
  --run gpt5mini=artifacts/runs/judgebench-gpt-5-mini \
  --run qwen=artifacts/runs/judgebench-qwen3-30b-a3b-v2 \
  --run skywork=artifacts/runs/judgebench-skywork-rm-0.6b-256 \
  --output-dir /tmp/jev-tutorial-statistics
```

### 12.2 离线重算 APB

安装附加依赖后，官方脚本会重写已存在的 `metrics.json` 与 `per-step.csv`：

```bash
pip install -e '.[agent-eval]'
python scripts/analyze_agentprocessbench.py
```

若希望完全隔离派生产物，可以利用模块中的 `OUT` 将输出放入临时目录，并仅链接原始结果：

```bash
python - <<'PY'
import sys, tempfile
from pathlib import Path
sys.path.insert(0, 'scripts')
import analyze_agentprocessbench as analysis
out = Path(tempfile.mkdtemp(prefix='jev-apb-tutorial-'))
(out / 'results.jsonl').symlink_to(
    Path('artifacts/agentprocessbench/results.jsonl').resolve())
analysis.OUT = out
analysis.main()
print('Derived files:', out)
PY
```

analyzer 会检查逻辑请求 hash，拒绝协议漂移，并要求全部模型×轨迹记录存在；终止失败记录算已执行，不等于有有效预测。用较早版本代码分析较新请求时，也可能因 hash 不同而拒绝运行。

### 12.3 新发起一次模型实验

以下步骤会使用网络；推理需要密钥并产生费用。不是阅读教程或离线复核的前提。

通用 pairwise 使用环境变量 `OPENROUTER_API_KEY`，配置参考 [jev_sample.toml](../configs/experiments/jev_sample.toml)。复制一份配置，修改实验名称、输出目录和所需模型，再执行 validate/run/analyze/report。

APB 现有 CLI 使用固定数据与输出路径：

```bash
python scripts/prepare_agentprocessbench.py
python scripts/run_agentprocessbench.py --prepare
python scripts/run_agentprocessbench.py --smoke
python scripts/run_agentprocessbench.py --run
```

在当前完整仓库中，主实验相同 hash 的记录已经缓存，`--run` 应显示 `Pending 0`；它不是“强制重跑”。做新协议时应在独立仓库副本或明确的新输出实现中运行，保留已有结果。`--prepare` 会重写 manifest，也不应被用来掩盖旧结果与新提示的不一致。

密钥接入并不统一：pairwise 支持环境变量及配置引用的 secrets 文件，APB 优先环境变量再读本地 secrets；RewardBench 2 的专用 runner 当前直接读 `configs/secrets.toml`。不要把密钥写进提交的实验配置或文档。

## 13. 如何继续扩展这个项目？

### 增加一个 A/B 评委

遵循 [adding-models.md](adding-models.md)：实现 `JudgeAdapter.judge()`，返回统一 Judgment，在 `make_adapter()` 注册，用新 TOML 与新输出目录运行。先用少量已知样本确认标签含义、概率字段和异常行为，再跑冻结集合。

配置替换仅适用于同一种协议。若新模型返回的是多候选 score 或轨迹标签，就需要相应的数据契约和分析器，不能强行映射为 A/B 后假装任务没有变化。

### 增加一套真实 agent 评估

先定义可观察证据与标签，再决定评委形式：

1. 明确任务完成的外部标准，例如文件路径、订单字段或测试结果。
2. 明确步骤粒度与中性探索含义，审计全部标签取值。
3. 白名单构造模型输入，把 gold 留在离线分析侧。
4. 冻结模型版本、rubric、请求、失败处理和统计单位。
5. 在独立校准集选阈值或复核策略，再评估冻结测试集。
6. 若目标是改善 agent，另做相同任务与预算下的在线对照，衡量最终成功、副作用、恢复率和总成本。

这些是后续实验方法，不是本仓库已经完成的功能。当前没有训练评委、验证线上转交策略，也没有证明过程评分能提高 agent 成功率。

### 测试验证了什么？

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

现有测试覆盖核心数据/指标、出处、外部证据审计，以及 APB 标签隔离、编号校验、标签映射和缺失计分。APB 测试需要 requests 与 numpy；缺少时会跳过。因此看到测试命令成功时，也要检查是否出现 skip。

测试可以发现实现错误，但不能证明人工标签完美、提示最优或模型适合生产。统计区间量化抽样波动，也不覆盖模型漂移、训练污染或换领域后的表现。

## 14. 阅读与复核索引

| 你想弄清楚什么 | 去哪里 |
|---|---|
| 核心框架怎样实现 | [src/jev_eval](../src/jev_eval/) |
| 回答实验每个协议的完整解释 | [experiment-report.md](../report/experiment-report.md) |
| JudgeBench/RB2 逐条结果与规模 | [artifacts/README.md](../artifacts/README.md) |
| 数据版本与转换出处 | [dataset-provenance.md](dataset-provenance.md) |
| 统计区间、可靠性图和错误清单 | [artifacts/analysis](../artifacts/analysis/) |
| System One 外部核查与合成诊断 | [验证台账](../artifacts/validation/system-one/README.md) |
| 真实 agent 实验的冻结规则及补充说明 | [PROTOCOL.md](../artifacts/agentprocessbench/PROTOCOL.md) |
| Agent 原始响应、重试与失败 | [results.jsonl](../artifacts/agentprocessbench/results.jsonl) |
| Agent 每一步 gold 与预测 | [per-step.csv](../artifacts/agentprocessbench/per-step.csv) |
| Agent 结果与限制的易读解释 | [agent-judge-benchmark.md](../report/agent-judge-benchmark.md) |

建议最后亲自选一条错误记录，沿着“数据 → payload → 原始响应 → 解析标签 → 指标”走一遍。能把一条结果解释清楚，再检查同一规则是否作用于全部样本，才能理解报告中的数字从哪里来。
