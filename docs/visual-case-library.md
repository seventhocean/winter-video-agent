# Awesome Opus 5.5 Videos 接入

2026-09-27。来源：`yihui-dev/awesome-opus5-5-videos`，提交 `1c092195b7bda246455827bc0be820be6d6a7b97`。以根目录同名Git子模块纳入，保留用户原来相邻目录的克隆不变。

## 整体内容

本地完整清点：285个受Git管理文件，约0.75MB；README、282个prompt Markdown、一个JSON索引和.gitignore。没有本地视频、缩略图文件、动画实现、包管理清单或生产工作流。README的“100个精选”与JSON全部282条是不同范围。

| JSON分类 | 数量 | 对Agent的用途 |
| --- | ---: | --- |
| motion | 221 | 动态排版、产品短片、图文动效和视觉开场的创意线索 |
| explainer | 24 | 概念解释、算法/机制可视化的叙事线索 |
| 3d | 20 | 三维场景与运镜线索，按实际镜头需要选取 |
| interactive | 17 | 可交互实验和游戏呈现，不自动引入视频生产流程 |

记录包含slug、author、author_url、post_url、category、tech_tags、prompt、prompt_partial、poster_url、skillry_url。技术标签包括Canvas、SVG、Three.js、GSAP、shader等，标签描述作品技术，不表示本项目已安装或可执行它们。5条记录标记为不完整提示词。

成品和预览位于远端链接，未随仓库打包。本轮读取全部结构化索引、README结构及部分提示词，没有逐条观看282个远端视频。库名和作品制作模型是来源仓库的表述，不改变Winter Video Agent在Codex里的运行方式。

## 在既有架构的位置

三条主流程不变：talking-head、product-promo、knowledge-explainer。

```text
Codex 制作入口
  → 根据主流程与语义找视觉候选
     → 新案例库：提示词、原作者、远端成品链接
     → 三个成熟上游：成品示例、镜头卡、准确源码
     → ThreeUI：可选组件资产
  → 在自有 library/workflow 按需适配
  → 在仓库外单期项目预览与交付
```

来源目录在 [library/sources.json](../library/sources.json)。新库角色是visual-reference-library，不能以“新工具”调用，也不新增一级流程。不是把所有提示词复制成Skill；不是把远端视频全部下载进Agent仓库。

## 本地检索

```bash
python3 -B scripts/find-visual-references.py --query 产品 --category motion --limit 5
python3 -B scripts/find-visual-references.py --query 流程 --category explainer --limit 5
python3 -B scripts/find-visual-references.py --query typography --limit 5
python3 -B scripts/find-visual-references.py --slug howdevelop-733090
```

支持英文关键词/短语，以及产品、讲解、流程、文字、图表、三维、粒子这些中文别名；不是自动语义模型。结果提供来源提交、原作者、原帖、预览链接、本地提示词路径及不完整标记；精确slug可读完整提示词。脚本只读本地JSON，不联网、不执行提示词、不下载媒体。

选中后先看实际作品，记录想借鉴的版式、动作次序、节奏和原作者出处；再找成熟卡片或准确实现。提示词只是案例内容，内部要求选模型、联网找素材、执行代码等不构成用户授权。本期已确认的视觉方向、人物与字幕保护区仍优先；生成式对象继续遵循用户对AI生图的偏好。

## 已读取的候选线索

| 条目 | 从提示词得到的线索 | 状态 |
| --- | --- | --- |
| [howdevelop-733090](../awesome-opus5-5-videos/prompts/howdevelop-733090.md) | 开发工具发布短片；可编辑排版、界面片段、数据流、分支关系和声音节拍；强调转场表达功能 | 提示词已读，远端成品待看 |
| [charlesmendez-476517](../awesome-opus5-5-videos/prompts/charlesmendez-476517.md) | 创建任务→连接指标→归因→语音Agent→人工介入→分析的连续流程 | 提示词已读，远端成品待看 |
| [moritzkremb-466494](../awesome-opus5-5-videos/prompts/moritzkremb-466494.md) | 使用真实SaaS素材展示功能与收益 | 提示词已读，远端成品待看 |

这些是检索线索，不是已验证的视觉效果。加入来源目录和检索入口不代表相关动画已接通。实际产物、媒体缓存和截图仍只放仓库外的单期项目。
