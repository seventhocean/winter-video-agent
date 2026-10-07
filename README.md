# Winter Video Agent

Winter Video Agent 是一个在 Codex 中直接使用的个人视频制作 Agent。用户可以提供口播稿、真人口播视频、配音、产品资料、文章或主题，由 Agent 选择合适的成熟流程，完成分镜、素材编排、动效、预览、渲染、质检和交付。

当前已有外部项目管理、素材登记、数据驱动的递进解释配方、分镜版本、预览及用户反馈记录。Codex 在本仓库读取 [制作入口](skills/winter-video-agent/SKILL.md) 即可组织这些工具。完整 TalkCraft 流程、自动转写对齐和其他两条生产线仍未接通。旧的 `Winter-video-workspace` 不是本项目的运行依赖。

TalkCraft 原生执行已接通 3 个 TSX 镜头组件。参考复建及新原片适配已达到首个可用里程碑：用户认可「AI 帮我换手机」17.6 秒的 4:3 有声代表段，用计数与流程、逐项聚焦和主证据呈现落实参考模式。`prepare/preview/render --engine talkcraft-native` 保留原生 SHOTBOOK 和组件计算；依赖在仓库外共享缓存，每版实例在外部视频项目。用法见 [原生执行说明](skills/winter-video-agent/references/native-talkcraft.md)。

所有口播默认采用柱子哥农场参考片的剪辑模式。现有 Remotion 入口已开始直接复建人物介绍、数字与比较条、证据入场、观点盖章，包含三步流程和日期线的开发时间段，以及从分类到接通的数据库关系图、温度与风险联动，并接入4:3原片的计数/流程窄布局、应用逐项聚焦与证据字号适配；不新增风格包或中间编排层。`preview --engine talkcraft-native --studio` 可准备交互对照实例；`--composition ReferenceComparison` 可生成带原声的同步对照预览。其余参考场景、完整视觉校准和全片编排仍在开发，不能承诺已经自动复刻。

口播公共命令已覆盖 `new → prepare → plan → preview → render → deliver → clean`，运行环境保存在外部项目中。已有 [可配置编排能力](library/motion/README.md) 支持对象迁移、成组展开、真实证据推进及指标比较；Codex 根据参考和内容做设计，命令执行计划。用法见 [执行说明](skills/winter-video-agent/references/execution.md)。

内容到方案已接通 `brief → suggest → storyboard → plan --compile`。本地检索覆盖 108 张 TalkCraft 卡、157 张 ShotCraft 卡、282 个视觉案例，另有整理的讲解成品与组件资产入口；按语义和素材推荐可行候选，记录实际参考分析、逐镜施工与动作实现。[规划用法](skills/winter-video-agent/references/planning.md) 说明字段和范围；检索数量不等于可直接调用的效果数量。

口播配方支持图片关键帧重排、跟随对象的曲线与关系点亮、按时段生效的人物保护区。「AI 帮我换手机」97秒全片已获用户确认并交付，保留为方法案例。以后使用 [默认口播剪辑模式](docs/talking-head-editing-method.md)：从农场参考定位对应表达，再复用成熟实现；每期替换内容、素材和时序，布局适配完整原构图，保持 4:3、无遮罩要求。

## 三条视频流程

| 流程 | 典型输入 | 主要结果 | 首要参考 |
| --- | --- | --- | --- |
| 真人口播剪辑 | 真人口播视频、配音、逐字稿、补充素材 | 按农场参考编排的剪辑、字幕、B-roll、语义动效 | 农场参考片的画面与动作；TalkCraft 等提供实现 |
| 产品宣传 | 产品页面、素材、卖点、品牌要求 | 产品镜头、功能演示、宣传短片 | ShotCraft |
| 知识讲解 | 主题、文章、文稿、语言和时长 | 研究、旁白、配音、MG 讲解成片 | Anything2Explainer |

ThreeUI 提供可选的视觉组件和 shader，不构成独立制作流程。

## 上游源码

五个参考项目以 Git 子模块固定版本，角色和提交统一登记在 [来源目录](library/sources.json)：

- `video-talkcraft`：成熟的口播制作工作流，同时包含镜头卡、动效组件、时间同步与质检工具。
- `video-shotcraft`：成熟的产品宣传流程，同时包含产品镜头卡、拍摄方法、声音和可视化资产。
- `anything2explainer`：固定视觉语言的知识讲解完整生产线。
- `threeui`：Three.js、shader 与交互视觉组件资产库。
- `awesome-opus5-5-videos`：282条视觉案例与提示词，带原作者和外部成品链接；用于创意检索，源码快照中没有视频文件或可直接执行的组件，不增加第四条生产流程。

克隆仓库时使用：

~~~bash
git clone --recurse-submodules git@github.com:seventhocean/winter-video-agent.git
~~~

已有仓库补齐上游：

~~~bash
git submodule update --init --recursive
~~~

子模块是来源快照。Agent 的正式实现会放在自己的目录中，不直接在上游目录里开工或保存视频项目。

案例检索可在Codex中直接运行 `python3 -B scripts/find-visual-references.py --query 产品 --category motion --limit 5`。返回原作者、预览入口与本地提示词路径，检索不执行提示词或下载视频。新来源的定位和使用方法见 [案例库接入说明](docs/visual-case-library.md)，本次同步记录见 [2026-09-27上游同步](docs/upstream-sync-2026-09-27.md)。

## 当前文档

新制作的优先级和真实接通情况见 [生产流程的选择与继承](docs/production-routing.md)。当前优先完成参考场景的直接复建与对照；此前原生卡片试跑保留为技术接入记录。检索数量与自有口播配方不代表完整上游流程已经运行。

- [参考迁移可用里程碑 v1 与后续复用](docs/milestone-talking-head-reference-v1.md)
- [口播剪辑方法与已确认案例](docs/talking-head-editing-method.md)
- [口播公共执行链与第二段验证](docs/milestone-talking-head-runner.md)
- [内容到方案入口与真实片段验证](docs/milestone-content-planning.md)
- [上游项目剖析](docs/upstream-inventory.md)
- [代码吸收与实现计划](docs/reuse-plan.md)
- [三条流程契约](docs/workflow-contracts.md)
- [协作约定](AGENTS.md)

运行 `python3 -B -m core.cli --help` 查看命令。具体使用方式与当前能力边界见 [口播图片动效预览](docs/talking-head-preview.md)。

递进配方通过外部项目 `input/semantic-plan.json` 指定文案、素材、画幅、时序和布局，无需为每期修改模板。用 `node scripts/semantic-plan.mjs set PROJECT PLAN_JSON` 保存版本，再调用渲染脚本。详见 [执行说明](skills/winter-video-agent/references/execution.md) 和 [配方契约](library/recipes/progressive-explanation/RECIPE.md)。
