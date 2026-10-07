# thinking-toolbox · 思维工具箱

个人使用的多思维模型协同分析技能。围绕一个值得深思的问题，自动匹配并调度多个思维模型（subskill）分别作答，再由主 skill 聚合整理，输出「两层回答」，并把每次问答自动归档到 `history/`。

## 架构

```
thinking-toolbox-skills/           # 项目根即技能根 BASE
├── SKILL.md                       # 主 skill：澄清 → 匹配 → 调度 → 聚合 → 记录
├── references/
│   ├── subskill-template.md       # subskill 统一模板 + 内容种子表 + 验收命令
│   └── history-format.md          # history 文件规范 + 索引格式
├── subskills/<name>/SKILL.md      # 27 个思维模型（被主 skill 读取，不注册为独立技能）
├── history/                       # 运行时产出：YYYY-MM-DD/*.md + INDEX.md
└── .workbuddy/memory/             # 工作区记忆（宿主维护，可删除）
```

## 两层回答

1. **第一层**：每个被启用的思维模型以自己的视角作答（核心判断 / 分析 / 行动含义）。
2. **第二层**：主 skill 聚合——共识点、分歧点（含根因）、盲区、主判断（带置信度）、下一步行动建议。

## 27 个思维模型

第一性原理、系统思维、深度思维、逆向思维、批判思维、战略思维、产品思维、预测思维、长期主义、价值主义、孙子兵法与三十六计、毛选、芒格、纳瓦尔、概率（贝叶斯）、二阶、经济学、辩证、复利、利他、时光机、终局、周期、环境、人脉、奥卡姆剃刀、宏观。

## 用法示例

- `用思维工具箱分析：要不要 all in AI 创业` —— 自动匹配 3~7 个模型
- `用芒格和第一性原理分析 X，不要产品思维` —— 指定 + 排除
- `除了产品思维，全部模型都上` —— 全部−排除（27 减 1）
- `全部模型看 X` —— 27 个全开（按相关度排序，每模型 ≤150 字，聚合优先）
- `帮我想想我的事业` —— 信息不足，先反问 1 个最高信息增益问题再匹配

## 分发（软链到宿主）

技能源码在本仓库，通过软链分发到各 AI Agent 宿主（与 deep-thinking 相同惯例）：

```bash
ln -s /Users/zyb/Documents/git/yunsiweilai.com/agent-skills/thinking-toolbox-skills ~/.workbuddy/skills/thinking-toolbox
# 如需分发到其他宿主：
# ln -s <本目录> ~/.claude/skills/thinking-toolbox
# ln -s <本目录> ~/.agents/skills/thinking-toolbox
```

**只软链主目录，切勿单独软链 `subskills/` 内任何目录**——subskill 是被主 skill 读取的资料，嵌套目录不会被宿主注册；若被单独软链会污染全局技能列表。

### 与独立技能 deep-thinking 的关系

本技能是**多模型并行拼盘**形态（"多角度看看""几个模型一起想"）；
独立技能 `deep-thinking` 是**单主因果链深挖**形态（"帮我想透""深挖一层"）。
两者形态互斥，按用户措辞选择，不叠加。`subskills/deep-thinking/` 只是工具箱内部的
"纵向深挖一层"视角，不等于也不触发那个独立技能。

## history 说明

- 每个问题一个文件：`history/YYYY-MM-DD/HHMM-<问题slug>.md`；同一问题的追问追加为「追问 N」小节。
- `history/INDEX.md` 是检索入口：用户说"上次聊过什么"时先读它，不要凭空回忆。
- 默认 `history/*` 被 .gitignore 忽略（个人问答记录不入库）。如需跨机同步，删除 .gitignore 中对应行即可。
- 归档含人名/公司/薪酬/健康等敏感信息时，写入前会先征得同意。
