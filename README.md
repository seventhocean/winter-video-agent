# Winter Video Agent

Winter Video Agent 是一个在 Codex 中直接使用的个人视频制作 Agent。用户可以提供口播稿、真人口播视频、配音、产品资料、文章或主题，由 Agent 选择合适的成熟流程，完成分镜、素材编排、动效、预览、渲染、质检和交付。

当前已有第一版口播图片动效预览命令：环境检查、外部项目创建、素材登记、项目查询和关键帧合成。使用 Python 标准库与本机 FFmpeg，尚未完成完整 TalkCraft 流程吸收。旧的 `Winter-video-workspace` 不是本项目的运行依赖。

## 三条视频流程

| 流程 | 典型输入 | 主要结果 | 首要参考 |
| --- | --- | --- | --- |
| 真人口播剪辑 | 真人口播视频、配音、逐字稿、补充素材 | 内容驱动的剪辑、字幕、B-roll、语义动效 | TalkCraft |
| 产品宣传 | 产品页面、素材、卖点、品牌要求 | 产品镜头、功能演示、宣传短片 | ShotCraft |
| 知识讲解 | 主题、文章、文稿、语言和时长 | 研究、旁白、配音、MG 讲解成片 | Anything2Explainer |

ThreeUI 提供可选的视觉组件和 shader，不构成独立制作流程。

## 上游源码

四个参考项目以 Git 子模块固定版本：

- `video-talkcraft`：成熟的口播制作工作流，同时包含镜头卡、动效组件、时间同步与质检工具。
- `video-shotcraft`：成熟的产品宣传流程，同时包含产品镜头卡、拍摄方法、声音和可视化资产。
- `anything2explainer`：固定视觉语言的知识讲解完整生产线。
- `threeui`：Three.js、shader 与交互视觉组件资产库。

克隆仓库时使用：

~~~bash
git clone --recurse-submodules git@github.com:seventhocean/winter-video-agent.git
~~~

已有仓库补齐上游：

~~~bash
git submodule update --init --recursive
~~~

子模块是来源快照。Agent 的正式实现会放在自己的目录中，不直接在上游目录里开工或保存视频项目。

## 当前文档

- [上游项目剖析](docs/upstream-inventory.md)
- [代码吸收与实现计划](docs/reuse-plan.md)
- [三条流程契约](docs/workflow-contracts.md)
- [协作约定](AGENTS.md)

运行 `python3 -B -m core.cli --help` 查看命令。具体使用方式与当前能力边界见 [口播图片动效预览](docs/talking-head-preview.md)。
