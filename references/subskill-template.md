# subskill 统一模板与写作要求

本文件是 `subskills/<name>/SKILL.md` 的写作规范。新增或修改 subskill 时严格遵循。

## 六段式模板

每个 subskill 文件 45~120 行，中文，结构固定为：

```markdown
---
name: <kebab-name，与目录名一致>
description: >
  思维工具箱子模型：<中文名>。<一句话核心定位>。被调度时以该视角分析用户问题；
  不适用于<排除边界>。
---

# <中文名>

## 核心思想
<3~6 条，每条一句话概念 + 一句解释。必须是该模型独有的概念，禁止放之四海皆准的套话。>

## 分析步骤
<3~6 步提问/推理框架，祈使句，面向执行者，可直接照做。>

## 关键问题清单
<5~8 个该模型标志性的提问，调度时直接拿来追问用户或自问。>

## 输出要求
限长：默认模式 ≤300 字，全部模式 ≤150 字。
<核心判断 → 分析 → 行动含义 的结构约束；该模型特有的表达要求。>

## 何时不适用
<2~4 条，帮助主 skill 在追问时判断是否换将；与其他易混模型的分工说明。>
```

## 防空壳验收标准

任意删掉模型名后，仅凭内容仍能猜出是哪个模型——否则视为空壳返工。
每个 subskill 必须包含下表列出的**内容种子**（实质概念，不是修辞）：

| 目录名 | 必须出现的内容种子 |
| --- | --- |
| first-principles | 拆解到不可再分的事实、类比思维批判、从零重构路径 |
| systems-thinking | 存量/流量、增强回路 vs 调节回路、延迟、杠杆点 |
| deep-thinking | 五层追问、现象→机制→结构→约束→演化 |
| inversion | 事前验尸、避免愚蠢清单、反向目标 |
| critical-thinking | 证据分级、常见谬误清单、钢铁人（steelman） |
| strategic-thinking | 定位/取舍/配称、五力、护城河 |
| product-thinking | 用户-场景-需求-价值闭环、PMF、MVP |
| forecasting | 基准率→驱动力→反作用力→拐点→证伪条件 |
| long-termism | 时间偏好、延迟满足、长期复利资产 |
| value-thinking | 内在价值 vs 价格、安全边际、价值锚 |
| sun-tzu | 道天地将法、虚实、形势；36 计按胜战/敌战/攻战/混战/并战/败战六套选用 |
| mao-xuan | 主要矛盾与矛盾的主要方面、调查研究、实践论、持久战三阶段 |
| munger | 多元模型格栅、25 种误判心理、能力圈、lollapalooza 效应 |
| naval | 专长×责任×杠杆（代码/媒体/资本/人力）、判断力、运气的四种分类 |
| bayesian-thinking | 先验/似然/后验、基准率谬误、证据更新幅度 |
| second-order-thinking | "然后呢"链条、激励的二阶扭曲、副作用映射 |
| economic-thinking | 机会成本、边际分析、激励反应、比较优势 |
| dialectical-thinking | 对立统一、质量互变、否定之否定、度的把握 |
| compounding | 复利三要素（本金/利率/时间）、临界点、可积累资产识别 |
| altruism | 价值交换前置、利他的长期回报机制、共赢结构设计 |
| time-machine | 孙正义时光机理论、跨市场阶段映射、适用前提（基础设施/人口结构相似性） |
| endgame | 终局形态想象、倒推里程碑、不变量识别 |
| cycles | 信贷/经济/行业/情绪周期、周期定位指标、均值回归 |
| environment | 孟母三迁、近朱者赤、"你是身边五个人的平均值"、环境设计 > 意志力（默认选项与摩擦）、信息食谱 |
| relationships | 人情账户（先存后取）、互惠与回请、面子与台阶、平时烧香 vs 临时抱佛脚、触点设计 |
| occams-razor | 如无必要勿增实体、最简解释优先、汉隆剃刀（能归因愚蠢勿归因恶意）、复杂性的维护成本、删减作为设计原则 |
| macro-thinking | 自上而下 vs 自下而上、PEST 扫描、"不谋全局者不足谋一域"、宏观叙事 vs 微观体感、局部最优之和 ≠ 全局最优 |

## 一致性要求

- frontmatter 的 `name` 必须与目录名完全一致。
- description 不重复主 SKILL.md 路由表中的匹配条件（匹配规则单一事实源在主 SKILL.md），只写模型自身定位与排除边界。
- 「何时不适用」写具体场景，不写"问题太简单时"这类空话。
- 与其他易混模型存在职责重叠时，在 description 里写明分工句（照 `macro-thinking` 的写法）。

## 验收命令

新增或修改 subskill 后，在技能根目录执行，全部无输出即通过：

```bash
# 1) 目录数与主 SKILL.md 路由表行数一致
ls -d subskills/*/ | wc -l
grep -cE '^\| [a-z-]+ \| ' SKILL.md

# 2) frontmatter name 与目录名一致
for d in subskills/*/; do dir=$(basename "$d"); name=$(grep -m1 '^name: ' "$d/SKILL.md" | sed 's/name: //'); [ "$dir" != "$name" ] && echo "MISMATCH: $dir vs $name"; done

# 3) 路由表与目录名完全一致
diff <(ls -d subskills/*/ | sed 's|subskills/||;s|/||' | sort) \
     <(grep -oE '^\| [a-z-]+ \| ' SKILL.md | sed 's/| //g' | awk '{print $1}' | sort)

# 4) 五段式齐备（每份应输出 5）
for d in subskills/*/; do grep -c '^## ' "$d/SKILL.md"; done | sort -u

# 5) 限长字段覆盖率应为 100%
grep -L "限长" subskills/*/SKILL.md

# 6) 防空壳：抽查内容种子
grep -l "孟母三迁" subskills/environment/SKILL.md
```

注意：macOS 自带 grep 不支持 `\|` 交替语法，务必用 `grep -E`。

