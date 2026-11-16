# System One 验证证据（2026-11-16）

本目录包含本轮核查与诊断，不混入原有 6,428 条 benchmark 判断。
结论与边界见 [补充报告](../../../report/system-one-agent-evaluation.md)。

## 证据清单

| 目录 / 文件 | 来源与范围 | 可复现内容 |
|---|---|---|
| [catalog.json](catalog.json) | Laya、d3-edge、Clef-flash 固定模型 revision；Kev 固定源码 commit | 公开配置字段、源码地址与文件 SHA-256；不是性能测试 |
| [external-reanalysis/](external-reanalysis/) | 外部 sys1-eval 保存的 Jev/Laya 推理；六轨道 2,100 个配对案例 | 逐案例预测/对错、聚合正确率、输入哈希；没有重新调用外部模型 |
| [laya-probes/](laya-probes/) | 本机 Laya 英文根 checkpoint；12 个合成基础案例 × 5 变体＝60 次 | 实际返回、延迟、token 序列哈希、代码/权重哈希与环境 |
| [d3-edge-probes/](d3-edge-probes/) | 本机 d3-edge；同 12 个基础案例 × 3 个短输入变体＝36 次 | 实际返回、延迟、代码/权重哈希与环境；没有视觉实验 |
| [d3-edge-exploratory/](d3-edge-exploratory/) | 初次 60-case 探索计划完成 5 条后因 CPU 长输入耗时中断 | 所有已完成结果（包括失败）保留；`status.json` 解释中断；不计入正式诊断比较 |

正式诊断保留 `cases.jsonl`、`results.jsonl`、`metrics.json`、`manifest.json`。
病例为本次人工构造的机制检查，**不是代表性样本、不是公开 agent benchmark、没有真实 agent 执行**。
不同变体有相关性；缺失证据组只有 4 个独特输入，每个重复 3 次。
本轮没有重新跑 Jev 在该诊断集上的结果，不能将其与原 JudgeBench 成绩合并排名。

## 复算外部结果与核查公开工件

以下仅需 Python 标准库与网络，无模型 key：

```bash
python scripts/verify_system_one_catalog.py
python scripts/audit_system_one_evidence.py --cache /tmp/jev-external-audit
```

外部源固定为 `David-DL-Space/sys1-eval@e74dfb6d99ed041f5f5240af386ba5272de84cdd`。
脚本按案例 ID 配对，保留 2,100-case 规模集，使用作者修正后的 `*-c-fixed.jsonl` 覆盖 C 轨道。
选择题按 label 相等计算；二元题用 `noul >= 0.5`；失败响应计错。
原始上游 prompt/响应留在下载缓存，只提交我们的衍生逐题结果与出处哈希。
若需要检查标签语义，应回查固定上游数据；本次复算并未重新人工标注这些案例。

## 重新运行本地诊断

请先审阅固定版本代码，再下载模型；不要直接把生产项目的 Transformers 版本升级以兼容实验。
Laya 与 d3 在两个隔离的依赖集合运行，实际包版本记录在各自 manifest。
本机采用 PyTorch 2.7.1+cpu、2 线程；Laya 使用 Transformers 4.57.6，d3 使用 5.17.0。
d3 发布 requirements 声明更高的 PyTorch 下限，本轮 2.7.1 CPU 参考路径能运行这些文本请求；
这不是对该依赖组合完整支持、GPU 行为或多模态兼容性的保证。

使用 `huggingface_hub.snapshot_download` 固定以下 revision，下载所需代码、配置、tokenizer 和 safetensors：

| repo | revision |
|---|---|
| `convaiinnovations/laya` | `e333cb7c823cd1787276228260f56d02fbf5180b` |
| `vllm-sr/d3-edge` | `bee5e872f75b9c5d1405767bf244a6948b95c0af` |

Laya 只需要根 checkpoint：`rl_agent_api.py`、`rl_common.py`、`rl_agent_config.json`、
`encoder/config.json`、`tokenizer/*`、`model.safetensors`，不要下载多语和 typed-decisions 子目录代替它。
d3 需要仓库根目录的 Python、JSON、tokenizer 文本、Jinja 和 safetensors 文件。
模型权重不提交到 Git。

```bash
# 在各自依赖环境中运行，路径替换为已下载并核查的快照目录
OMP_NUM_THREADS=2 python scripts/probe_system_one.py \
  --model laya --model-dir /path/to/laya

OMP_NUM_THREADS=2 python scripts/probe_system_one.py \
  --model d3-edge --model-dir /path/to/d3-edge \
  --variants original reverse_options no_evidence
```

脚本每次重新写入对应输出目录，不混合不同协议；加载后的 1 次 warmup 不计入结果。
输入、输出、精度、线程数、环境版本和哈希均记录。参数中的固定 revision 是预期来源，
实际权重 SHA-256 另行保存，复现时应核对。不要仅凭本机的 CPU 延迟判断模型的线上速度。

已有诊断结果可以完全离线重算，无需安装模型依赖：

```bash
python scripts/probe_system_one.py --model laya --analyze-only
python scripts/probe_system_one.py --model d3-edge --analyze-only
```

## 本轮未完成也未宣称完成的内容

- Kev/Clef 的权重推理、跨模型正式 agent benchmark；
- d3 的完整长输入实验与视觉/视频评估；
- AgentRewardBench、AgentProcessBench 上的新 run；
- agent 在线干预实验、真实业务标签、领域微调或上线收益验证。

这些是研究路线中的下一步，不是可以由当前诊断结果推出的结论。
