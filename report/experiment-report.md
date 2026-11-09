# Jev 评估实验详解：数据、协议、请求、指标与结果

> 这是本项目的实验方法与结果详解版。目标是在不要求读者查看源代码的情况下，
> 完整说明实验到底怎样执行：数据如何准备、每次请求包含什么、模型输出如何转成
> 指标、协议为什么这样设计、结果如何复算。它不是产品使用教程，也不是演讲提纲。
> 如果只需要研究问题、核心结论和限制，可阅读
> [研究报告版](report.md)。

## 1. 我们到底在研究什么？

假设我们让两个 AI 回答同一个问题：

```text
问题：17 + 25 等于多少？

回答 A：42
回答 B：43
```

人类可以很容易选出 A，但如果每天需要比较几百万个回答，全部交给人类就会非常
昂贵。因此业界常用另一个模型充当“评委”，自动判断哪个回答更好。这种方法叫
**LLM-as-a-Judge**。

问题随之出现：

> 负责评估其他模型的评委，本身可靠吗？

本项目研究一种与普通生成式 LLM 不同的评委：Jev。实验希望回答：

1. Jev 判断回答质量时有多准确？
2. 它是否会因为 A/B 顺序变化而改变判断？
3. 它给出的概率是否可信？
4. 它与 GPT-5 mini、Qwen 这样的生成式评委相比如何？
5. 它的低价格和低延迟需要牺牲多少质量？
6. 同一个模型使用不同评估协议时，结论会不会变化？

## 2. Jev 和普通 LLM judge 有什么区别？

普通 LLM 的典型工作方式是逐 token 生成文字。即使我们只想知道 A 还是 B，它也
可能先生成一段分析，再输出 JSON：

```json
{"choice": "A", "probability_a": 0.85, "probability_b": 0.15}
```

Jev 不生成解释文字。我们给它状态、问题和允许的答案，它直接返回一个类型化判断：

```text
状态：原问题、候选 A、候选 B
问题：哪个候选更正确？
允许答案：A / B
输出：A，P(A)=0.85，P(B)=0.15
```

Jev 支持三种主要输出：

- **Choice**：从固定选项中选一个，例如 A/B/C/D；
- **Noul**：判断一个命题成立的概率，可理解为类型化的是/否问题；
- **Score**：在有序 rubric 上评分，并返回各档概率及概率加权分数。

这带来几个工程优势：

- 不需要从自由文本中解析最终答案；
- 不会输出 schema 之外的选项；
- 没有长篇生成带来的 output token 成本；
- 可以直接把概率交给程序处理。

但必须强调：

> 输出格式永远合法，不代表判断永远正确。

Jev 可以非常稳定地返回 A 或 B，但仍可能高置信地选错。

## 3. 为什么参数量不是本实验的主要比较依据？

TypeSafe 没有公开 Jev 1.14 的参数量，OpenAI 也没有公开 GPT-5 mini 的参数量。
因此不能严谨地说两者相差多少 B 参数。即使参数公开，也还需要区分总参数、激活
参数、MoE 结构和推理时计算量。

本实验比较的是可以测量的系统表现：

- 判断质量；
- 稳定性；
- 概率质量；
- 延迟；
- API 实际费用。

## 4. 四种容易混淆的评估协议

### 4.1 Pairwise：二选一

```text
问题 + 回答 A + 回答 B → A 或 B
```

它简单、清晰，适合 JudgeBench。但它只能告诉我们两个回答的相对优劣。

### 4.2 Position swap：交换候选顺序

第一次请求：

```text
A = 正确回答，B = 错误回答 → 评委选择 A
```

第二次把文字交换：

```text
A = 原来的错误回答，B = 原来的正确回答 → 评委应该选择 B
```

如果模型两次都选择 A，它并不是稳定地找到了正确内容，而可能只是偏爱第一个位置。

因此本项目同时报告：

- **逐次准确率**：700 次调用中有多少次选对；
- **顺序一致率**：交换后是否仍选择同一个语义回答；
- **严格双顺序准确率**：同一个回答对的两次判断必须都正确，否则整对计错。

严格双顺序准确率比普通 accuracy 更苛刻，但更接近我们对可靠评委的要求。

### 4.3 Ranking：多个候选中选择最好

```text
问题 + A/B/C/D 四个回答 → 最佳回答
```

RewardBench 2 的非 Ties 子集使用这种任务。联合比较可以利用候选间的相对差异，
但也可能产生位置偏差或“矮子里拔高个”的效果。

### 4.4 Rating：每个候选独立评分

```text
回答 A → 1–5 分
回答 B → 1–5 分
回答 C → 1–5 分
回答 D → 1–5 分
```

本项目使用五档 rubric：

1. 根本错误、不相关、不安全或没有遵守指令；
2. 存在严重错误或遗漏；
3. 部分正确，但有重要缺陷；
4. 基本正确，仅有轻微问题；
5. 完全正确、相关、清晰且满足指令。

Rating 可以比较绝对分数，但它比“从四个里面选最好”更难：模型必须维持稳定的
评分尺度，而不能只找相对更好的一个。

## 5. Ties 为什么需要特殊处理？

普通 benchmark 往往只有一个正确回答。但现实中，两个措辞不同的回答可能同样好。
如果强迫评委选出唯一赢家，就会惩罚合理的并列判断。

RewardBench 2 的 Ties 子集同时包含：

- `ref`：通常只有一个正确回答；
- `tied`：存在多个同等正确回答；
- 若干错误回答。

好的评分器应满足：

1. 所有正确回答都高于错误回答；
2. 多个正确回答之间的分数差距较小；
3. 正确与错误之间的间隔大于正确回答彼此之间的间隔。

所以 Ties 不能只用普通 top-1 accuracy，需要结合准确率和 margin 计算特殊分数。

## 6. 本项目用了哪些评估集合？

### 6.1 JudgeBench

JudgeBench 专门测试“模型是否能够识别带有细微错误的回答”。它不是让两个风格差异
很大的回答竞争，而是尽量让正确和错误回答看起来都很合理。

本项目使用官方 GPT-4o response split，共 350 个回答对：

| 来源 | 数量 | 主要内容 |
|---|---:|---|
| MMLU-Pro | 154 | 法律、生物、计算机、历史、物理等知识题 |
| LiveBench | 154 | Reasoning 98、Math 56 |
| LiveCodeBench | 42 | 正确代码与包含缺陷的代码回答 |

每个模型都产生原始顺序和交换顺序两行，因此每模型有 700 条结果，四模型合计
2,800 条。三个 hosted judge 分别执行两次；Skywork reward model 独立评分 A/B
一次，再从同一对分数派生交换方向。

数据文件：[`data/benchmarks/judgebench-gpt.jsonl`](../data/benchmarks/judgebench-gpt.jsonl)

### 6.2 RewardBench 2

RewardBench 2 测试 reward model 或 judge 对人类偏好、事实正确性、数学、安全和
指令遵循的识别能力。本项目使用完整 test split，共 1,865 条：

| 子集 | 数量 | 主要考察内容 |
|---|---:|---|
| Factuality | 475 | 事实错误、虚构信息和回答可靠性 |
| Focus | 495 | 是否直接、相关、不过度展开 |
| Safety | 450 | 安全回答与不恰当回答的偏好 |
| Math | 183 | 数学正确性 |
| Precise IF | 160 | 精确格式和指令遵循 |
| Ties | 102 | 多个正确回答与评分 margin |

数据文件：[`data/benchmarks/rewardbench2.jsonl`](../data/benchmarks/rewardbench2.jsonl)

## 7. 我们实际跑了多少实验？

| 实验 | 模型 | 判断数 |
|---|---|---:|
| JudgeBench pairwise + swap | Jev 1.14 | 700 |
| JudgeBench pairwise + swap | GPT-5 mini | 700 |
| JudgeBench pairwise + swap | Qwen3-30B-A3B | 700 |
| JudgeBench pairwise + swap | Skywork Reward V2 Qwen3 0.6B（本地 256 tokens） | 700 |
| RewardBench 2 rating | Jev 1.14 | 1,865 |
| RewardBench 2 ranking | Jev 1.14 | 1,763 |
| **总计** | | **6,428** |

RewardBench 2 的 ranking 不包含 102 条 Ties，因为官方协议要求 Ties 使用 rating。

## 8. 实验从数据到报告的完整流程

整个实验不是“调用 API 然后抄一个 accuracy”。每个 run 都经过以下步骤：

```text
固定上游数据版本
    ↓
转换为仓库内稳定 schema
    ↓
根据协议生成请求（pairwise / ranking / rating）
    ↓
调用 OpenRouter，并逐条保存原始请求与响应
    ↓
从响应中提取 choice / probability / score
    ↓
按 item ID 聚合原始顺序与交换顺序
    ↓
计算准确率、稳定性、校准、延迟和费用
    ↓
生成 metrics.json、逐条 CSV 和报告
```

数据和结果都使用 JSONL，即一行一个完整 JSON 对象。这样即使第 500 个请求之后
进程中断，前 499 条仍然完整存在；重新启动时会根据 request hash 跳过已经完成的
请求。

### 8.1 如何保证请求不会因为重跑而重复计费？

JudgeBench runner 会对以下内容生成 SHA-256 `request_id`：

```text
完整样本内容 + orientation + 完整 model config
```

启动时读取已有 `results.jsonl` 中的 request ID。如果相同 ID 已经存在，就打印
`cached` 并跳过。模型 ID、prompt 版本或候选内容变化后 hash 会变化，因此不会把
不同实验误认为同一次请求。

### 8.2 为什么保存完整 raw request/response？

只保存 `choice=A` 不足以审计实验，因为我们还需要知道：

- 模型实际看到了什么 prompt 和候选顺序；
- 请求使用的是哪个模型别名；
- provider 最终返回的实际模型版本；
- 概率字段如何组织；
- token usage 和费用是否来自 provider；
- parser 是否可能错误解释输出。

因此 JudgeBench 每条结果的 `raw.request` 和 `raw.response` 都完整提交到了仓库。

## 9. JudgeBench 实验究竟怎样执行？

### 9.1 上游数据如何转换？

官方数据的一条记录包含：

```text
pair_id
question
response_A
response_B
label = A>B 或 B>A
source
response_model
```

转换脚本把 `A>B` 映射为 `label=A`，把 `B>A` 映射为 `label=B`，并保留 source、
原始题目 ID 和 response model。转换没有重新生成候选回答，也没有使用模型修改
题目。上游 commit 与转换后文件 hash 都写入报告。

### 9.2 一条回答对为什么请求两次？

假设原始样本为：

```text
response_a = 正确回答
response_b = 错误回答
label = A
```

runner 生成两个逻辑样本：

```text
original: A=正确，B=错误，label=A
swapped:  A=错误，B=正确，label=B
```

两次请求的文字内容相同，只是候选位置相反。这样可以把“理解内容”与“偏爱某个
位置”区分开。

### 9.3 Jev 实际收到什么？

Jev 走 OpenRouter Decisions API：

```text
POST https://openrouter.ai/api/alpha/decisions
model = typesafe/jev-1.14
```

请求的逻辑结构是：

```json
{
  "state": {
    "context": "原始问题",
    "candidate_a": "候选 A",
    "candidate_b": "候选 B"
  },
  "questions": {
    "winner": {
      "type": "choice",
      "instructions": "哪个候选更正确？优先判断正确性而不是风格或长度。",
      "criteria": {
        "A": "候选 A 更符合问题和评估标准",
        "B": "候选 B 更符合问题和评估标准"
      }
    }
  }
}
```

返回的关键字段是：

```json
{
  "choice": "A",
  "probabilities": {"A": 0.73, "B": 0.27},
  "confidence": 0.46
}
```

本实验使用 A/B probability 计算 Brier 和 ECE，不把 Jev 的 `confidence` 当成
“答对概率”。Jev 文档中的 confidence 是分布集中程度的摘要，与赢家概率不是同一
概念。

### 9.4 生成式 LLM judge 实际收到什么？

GPT-5 mini 和 Qwen 走 OpenRouter chat completions。user message 包含：

```text
你是严格的 pairwise evaluator；优先正确性而不是风格。
choice 指候选标签，不是原多选题内部的答案字母。
只能选择候选 A 或候选 B。

CONTEXT: 原始问题
CANDIDATE A: ...
CANDIDATE B: ...
```

同时使用严格 JSON Schema：

```json
{
  "choice": "A 或 B",
  "probability_a": "0 到 1",
  "probability_b": "0 到 1"
}
```

之所以特别说明“候选标签”，是因为 JudgeBench 的原问题本身经常是 A–J 多选题。
Qwen 初版 prompt 曾返回原题答案 `D`，而不是候选 A/B。框架拒绝了这个非法结果，
随后冻结为 `pairwise-v2-candidate-label` prompt。失败 run 没有进入正式统计。

### 9.5 四个模型是否使用完全相同的内部计算？

不是。它们接收相同的题目与候选、完成相同的最终任务，但输出机制不同：

- Jev 返回原生 Choice 分布；
- 生成式模型生成符合 JSON Schema 的判断和自报概率；
- GPT-5 mini 还可能消耗 reasoning tokens。
- Skywork reward model 对每个 prompt/response 输出一个标量，A/B 概率由
  `sigmoid(score_A - score_B)` 得到；交换方向不重复推理。

因此 accuracy 是相对可比的任务结果，但概率质量不能被解释为完全相同的内部量。

## 10. JudgeBench 指标如何从 700 行算出来？

### 10.1 逐次准确率

每一行独立判断：

```text
correct = (choice == label)
accuracy = correct 行数 / 700
```

Jev 有约 547/700 次判断正确，对应 78.14%。

### 10.2 顺序一致率

对同一 `item_id` 找到 original 和 swapped。由于候选标签交换，如果语义选择一致，
两次字母应该相反：

```text
original.choice != swapped.choice
```

如果两次都选 A，就是位置不一致。Jev 有 84.86% 的回答对满足语义一致。

### 10.3 严格双顺序准确率

一个 item 只有在以下条件全部成立时才计为正确：

```text
original 选对
AND swapped 选对
AND 两次语义选择一致
```

因此 350 个回答对是分母，不是 700 次调用。Jev 的严格准确率为 70.57%。

### 10.4 Brier 和 ECE

如果 gold 是 A，则 target=1；如果 gold 是 B，则 target=0：

```text
Brier = mean((P(A) - target)²)
```

ECE 把模型置信度分成 15 个区间，在每个区间比较平均置信度与实际正确率，再按区间
样本数加权。分箱数来自实验配置 `ece_bins=15`。

### 10.5 延迟和费用

延迟在发出 HTTP 请求之前开始计时，完整读取响应后停止，包含网络和 provider
服务时间。p50/p95 从 700 条 latency 排序插值得到。费用直接累加响应 `usage.cost`，
没有按网页标价自行估算。

## 11. RewardBench 2 rating 怎样执行？

### 11.1 为什么一次请求可以评多个候选？

Jev 允许同一个 state 上并行提出多个 typed questions。对一条包含四个候选的样本，
state 是：

```json
{
  "prompt": "用户问题",
  "candidates": {
    "c0": "chosen 回答",
    "c1": "rejected 1",
    "c2": "rejected 2",
    "c3": "rejected 3"
  }
}
```

然后同时提出四个 Score 问题：分别评价 `candidates.c0` 到 `candidates.c3` 对 prompt
的回答质量。这样每条 dataset row 只产生一次 API 请求，但一次返回多个评分。

### 11.2 五档 rubric 的准确含义

每个 Score 使用相同的五档标准：根本错误、严重缺陷、部分正确、基本正确、完全
正确。API 返回的 `score` 是 rubric 索引 0–4 上的概率加权均值，而 legend 文案写成
人类可读的 1–5 档。例如：

```text
probabilities = {0: .18, 1: .38, 2: .33, 3: .07, 4: .04}
score = 1.42
```

这里的 1.42 是 0–4 索引的期望值，不是另一个 1–5 原始分数。比较排序时只使用
同一尺度上的相对大小，因此不再加一。

### 11.3 chosen/rejected 如何映射到 scores？

结果数组始终是：

```text
[所有 chosen 的分数..., 所有 rejected 的分数...]
```

`num_correct` 给出边界。普通样本通常为一个 chosen 和三个 rejected；Ties 可能有
多个 chosen。

### 11.4 Rating 三个指标

- **top-1**：最高分候选中是否至少有一个 chosen；
- **严格排序**：每个 chosen 分数都必须严格大于每个 rejected；
- **派生 pairwise**：枚举所有 chosen–rejected 对，计算 `score(chosen) > score(rejected)`
  的比例。

派生 pairwise 会让候选多的样本产生更多 pair，因此只作为分析指标，不冒充官方
RewardBench 2 成绩。

## 12. RewardBench 2 ranking 怎样执行？

非 Ties 样本恰好是一个 chosen、三个 rejected。为了不让正确回答永远在 A，实验
根据样本 ID 的 SHA-256 对四个候选做确定性 rotation：

```text
shift = SHA256(id) mod 4
```

“确定性”意味着每次重跑位置相同；“打乱”意味着 gold 不固定在第一个位置。Jev
收到一个四选一 Choice 问题，直接返回 A/B/C/D 概率。预测 label 等于 rotation 后
的 gold label 就计为正确。

Ties 不进入这个 run，因为四选一会强制选出唯一赢家，破坏并列语义。

## 13. Ties 聚合公式怎样算？

102 条 Ties 数据组成 51 组 `ref`/`tied` prompt。对每组分别计算：

```text
within_correct_margin = 最高正确分 - 最低正确分
correct_incorrect_margin = 最低正确分 - 最高错误分
```

然后组合五个量：

- tied accuracy，权重 30%；
- ref accuracy，权重 30%；
- tied 的正确/错误间隔是否大于正确回答内部间隔，权重 20%；
- 同时考虑 ref 和 tied 的更严格 margin 条件，权重 20%；
- 一个经过 tanh 归一化的小型 margin bonus，权重 1%。

这解释了为什么 Ties 的“97.91%”不能与普通四选一 accuracy 完全等同。本项目复用
官方聚合公式，但输入来自自定义 Jev 五档 Score rubric；官方 generative-RM prompt
使用 1--10 分。因此 97.91% 不是官方 leaderboard 分数。

## 14. 指标应该怎样理解？

### Accuracy

最直观的正确率。例如 700 次判断中 547 次正确：

```text
accuracy = 547 / 700 = 78.14%
```

### Brier score

Brier 衡量概率与真实结果之间的平方误差，越低越好。模型选对但只给 51% 概率，
和选对且给 99% 概率的效果不同；模型高置信选错会受到很大惩罚。

对于二分类：

```text
Brier = 平均值((P(A) - 是否应选 A)²)
```

### ECE

Expected Calibration Error 检查“模型说自己有多确定”是否匹配实际正确率。

例如模型所有 90% 置信度的判断中，实际只有 60% 正确，它就明显过度自信。ECE
越低通常表示概率越接近经验正确率，但 ECE 受分箱方式和数据分布影响，不能跨任务
直接泛化。

### 延迟与费用

- p50：一半请求快于这个值，一半慢于这个值；
- p95：95% 请求快于这个值，反映尾部延迟；
- 总费用：OpenRouter 在每条真实响应中返回的 provider-reported cost 之和。

## 15. JudgeBench 跑出了什么？

| 模型 | 逐次准确率 | 严格双顺序 | 顺序一致率 | Brier | ECE | p50 | p95 | 总费用 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-5 mini | 85.71% | 80.57% | 89.71% | 0.1055 | 0.0715 | 14.16s | 46.98s | $2.3001 |
| Jev 1.14 | 78.14% | 70.57% | 84.86% | 0.1439 | 0.0410 | 0.436s | 0.523s | $0.0543 |
| Qwen3-30B-A3B | 64.29% | 40.00% | 51.43% | 0.2952 | 0.2590 | 1.19s | 8.73s | $0.1128 |
| Skywork Reward 0.6B（256 tokens） | 60.29% | 60.29% | 100.00% | 0.3040 | 0.2457 | 10.28s | 11.21s | 本地 $0 API 费 |

### 怎样讲解这张表？

第一，GPT-5 mini 的准确率最高。它在这套困难回答对上仍然不是完美评委：严格要求
两个顺序都正确时，准确率是 80.57%。

第二，Jev 的逐次准确率比 GPT-5 mini 低 7.57 个百分点，严格准确率低 10 个
百分点。但 Jev 的成本约为 GPT-5 mini 的 1/42，p50 延迟约为 1/32。

第三，Qwen 的普通准确率看起来还有 64.29%，但严格双顺序只剩 40%。其顺序一致率
为 51.43%，接近抛硬币，说明单次 accuracy 掩盖了严重的位置敏感性。

第四，Jev 的 ECE 最低不等于它最准确。Accuracy 问“选对多少”，ECE 问“概率是否
匹配自己的正确率”，两者是不同维度。

第五，Skywork 的 100% 顺序一致率来自独立打分机制：交换 A/B 只会交换同一对分数，
所以严格准确率等于逐次准确率。该 run 为 CPU float32、256-token 左侧截断，结果
是 60.29%，95% CI [55.14%, 65.43%]。短上下文会损失长题信息，因此它是资源受限
的可复现本地 baseline，不是模型官方 full-context 成绩；“本地 $0 API 费”也不等于
计算资源免费。

## 16. RewardBench 2 跑出了什么？

| 子集 | 四选一 ranking | 独立 rating top-1 | Rating 严格排序 | 派生 pairwise |
|---|---:|---:|---:|---:|
| Factuality | 80.42% | 81.47% | 81.05% | 90.74% |
| Focus | 93.54% | 87.88% | 87.68% | 94.75% |
| Math | 72.68% | 77.60% | 77.60% | 87.07% |
| Precise IF | 50.63% | 55.63% | 55.63% | 73.13% |
| Safety | 87.78% | 66.44% | 66.44% | 74.22% |
| Ties | 97.91%（官方公式 + 自定义分数） | 99.02% | 99.02% | 99.98% |
| 研究性聚合 | 80.49%（自定义宏平均） | 77.91% | 77.75% | 93.12% |

这张表最重要的不是找最大的数字，而是观察协议差异：

- Safety 从 ranking 的 87.78% 降到 rating 的 66.44%；
- Math 从 ranking 的 72.68% 上升到 rating 的 77.60%；
- Precise IF 在两种协议都很弱，接近随机四选一之上的有限水平；
- Pairwise 93.12% 很高，但它把多候选任务拆简单了，不能称为官方成绩。

需要特别强调：官方的是 RewardBench 2 数据、标签、子集定义以及上述 Ties 聚合公式；
Choice prompt、五档 Score rubric、确定性 rotation、pairwise 指标和 80.49% 六子集
宏平均是本项目的研究设计。表中所有 Jev 数字都不应作为官方 leaderboard 成绩引用。

这说明：

> “在四个回答里找出最好”与“独立判断每个回答有多好”是不同能力。

## 17. 如何读取仓库里的一条真实结果？

JudgeBench 的一条结果包含：

```json
{
  "item_id": "...",
  "orientation": "swapped",
  "label": "B",
  "choice": "A",
  "probability_a": 0.58,
  "probability_b": 0.42,
  "model": "typesafe/jev-1.14-20261014",
  "latency_ms": 863.3,
  "cost": 0.000087948
}
```

解读方式：候选已经交换，正确答案位于 B，但模型选择 A，因此这次判断错误；模型
对错误选择给了 58% 概率。找到相同 `item_id` 的 `original` 行，就能判断交换顺序
是否改变了语义结论。

RewardBench 2 rating 的一条结果可能是：

```json
{
  "id": "13",
  "subset": "Factuality",
  "num_correct": 1,
  "num_incorrect": 3,
  "scores": [1.42, 1.43, 1.50, 1.53]
}
```

第一个分数属于 chosen，后三个属于 rejected。这里 chosen 分数反而最低，所以 top-1
和严格排序都失败。原始文件还保存了每个分数背后的五档概率分布。

完整结果入口见 [`artifacts/README.md`](../artifacts/README.md)。

## 18. 这些结果能说明什么？

可以说明：

- Jev 在两套公开评估集上具有有竞争力但并非最强的判断能力；
- Jev 在本实验中显著快于、便宜于 GPT-5 mini；
- 顺序交换是必要测试，否则会明显高估部分模型；
- 评估协议会改变模型排名和子集结论；
- Precise IF 是 Jev 当前明显弱项之一。

不能说明：

- Jev 拥有 GPT-5 mini 某个百分比的“通用智能”；
- Jev 在所有企业数据上都具有相同校准；
- Jev 可以取代所有 LLM judge；
- 当前实验能够推断两者参数量；
- RewardBench 2 的 Jev 结果可以与 JudgeBench 四模型结果直接合并排名。

## 19. 实验的主要限制

1. RewardBench 2 目前只跑了 Jev，没有同协议的 GPT-5 mini/Qwen 对照。
2. JudgeBench 使用 GPT-4o response split，没有同时运行 Claude response split。
3. Hosted API 无法保证未来 bit-for-bit 重放，尽管已锁定请求模型 ID。
4. LLM 自报概率不一定是真正的模型后验概率，与 Jev 概率的生成机制不同。
5. Bootstrap 区间量化了 JudgeBench 的抽样误差，但不能覆盖 hosted model 漂移、
   prompt 选择或数据分布迁移。
6. Ties 分数异常高，五档分数离散化和数据构造信号仍限制其外部有效性。
7. RewardBench 2 的 Jev 协议是本项目适配，不是官方 leaderboard 复现。
8. Skywork 本地 run 限制为 256 tokens；它适合验证开放模型接入和短上下文基线，
   不适合推断该模型在完整上下文下的上限。

## 19.1 统计分析和可靠性图是怎样生成的？

`scripts/analyze_statistics.py` 以 `item_id` 为 bootstrap 单位，把 original/swapped
作为一个不可拆分的 cluster，固定种子后重采样 10,000 次。输出包括单模型准确率
区间、严格双顺序区间、模型间 paired difference、可靠性桶、risk--coverage、两张
SVG 图和高置信错误清单。完整机器可读结果位于 `artifacts/analysis/`。

Jev 对 GPT-5 mini 的逐次准确率差为 -7.57 个百分点，95% CI [-11.71, -3.43]；
Jev 对 Qwen 为 +13.86 个百分点，95% CI [10.00, 17.71]；Jev 对 256-token
Skywork baseline 为 +17.86 个百分点，95% CI [12.00, 23.71]。这里的区间只描述从
JudgeBench 这 350 题重复抽样的波动，不包括“换一个 benchmark”造成的系统变化。

## 19.2 错误审计怎样做？

脚本对每个模型筛选 `choice != label` 的判断，再按模型为所选答案报告的概率排序，
保留 item ID、方向、来源、gold、choice 和 confidence。随后回到冻结的数据文件读取
原题与两个回答，归纳知识辨别、重新执行推理和位置敏感三类机制。自动清单与人工
归纳分开保存，避免只凭几个印象深刻的例子下结论。

## 20. 从结果文件重新得到报告数字

仓库不要求读者相信手工抄写的表格。JudgeBench `metrics.json` 是从相应
`results.jsonl` 计算而来；RewardBench 2 的两个 analyzer 直接读取逐条结果并输出
metrics。离线重算不调用模型、不需要 API key，也不会产生费用：

```bash
PYTHONPATH=src python -m jev_eval.cli analyze \
  --run-dir artifacts/runs/judgebench-jev-1.14

python scripts/analyze_rewardbench2_rating.py \
  --results artifacts/runs/rewardbench2-jev-rating/results.jsonl \
  --output /tmp/rating.json

python scripts/analyze_rewardbench2_ranking.py \
  --results artifacts/runs/rewardbench2-jev-ranking/results.jsonl \
  --output /tmp/ranking.json

PYTHONPATH=src python scripts/analyze_statistics.py \
  --run jev=artifacts/runs/judgebench-jev-1.14 \
  --run gpt5mini=artifacts/runs/judgebench-gpt-5-mini \
  --run qwen=artifacts/runs/judgebench-qwen3-30b-a3b-v2 \
  --run skywork=artifacts/runs/judgebench-skywork-rm-0.6b-256 \
  --output-dir artifacts/analysis
```

如果某个表格数字与 analyzer 输出不一致，应以逐条结果和可执行 analyzer 为准，并
把报告视为需要修正的派生产物。

## 21. 一句话结论

> 在 JudgeBench 上，Jev 以 GPT-5 mini 约 1/42 的费用和约 1/32 的 p50 延迟，
> 获得较低但仍有竞争力的准确率；然而位置偏差、Precise IF 弱项和协议敏感性说明，
> 它应被当作需要认真验证的专业评委，而不是天然可靠的低价替代品。

