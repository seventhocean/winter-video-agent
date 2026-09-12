# 四个上游项目剖析

更新日期：2026-09-12

## 结论

四个上游项目不在同一个能力层级。它们应当按“生产流程”和“资产来源”拆开理解：

- TalkCraft：口播生产流程，同时也是镜头卡和质检工具库。
- ShotCraft：产品宣传生产流程，同时也是产品镜头卡和声音资产库。
- Anything2Explainer：知识讲解的端到端生产流程，视觉语言较固定。
- ThreeUI：视觉组件资产库，不负责从需求到成片的生产流程。

Winter Video Agent 应维护自己的三条流程，吸收这些项目已经跑通的实现。上游子模块只负责保存可追溯的源码快照。

## 固定版本

| 上游 | 提交 | 上游许可证 | 在本项目中的角色 |
| --- | --- | --- | --- |
| Anything2Explainer | `5544f599522cc0f7bab6d0dfe823905059641172` | PolyForm Noncommercial | 知识讲解流程来源 |
| TalkCraft | `b7fb9ac943c64b1d6dd61f9576635b173602a4a4` | PolyForm Noncommercial | 口播流程与卡片来源 |
| ShotCraft | `5e71af35a2daee492dd3ea93e5e8903f32dcd13c` | Apache-2.0 | 产品流程与卡片来源 |
| ThreeUI | `68802d5428071ada5c20db8094b1649e6bb770ed` | MIT | 视觉组件来源 |

用户已确认获得 Vincent 对前三个相关项目进行代码复用和二次开发的授权。实现时仍然记录每段吸收代码的来源提交和路径，方便维护与同步。

## TalkCraft

### 它已经解决的问题

TalkCraft 是一条成熟的口播或配音驱动视频管线：

1. 确认画幅和视觉语言。
2. 确认文稿。
3. 以最终人声生成 CPU 字级时间戳。
4. 准备真实素材、图标和生成素材。
5. 用 SHOTBOOK 将句子、字词锚点、镜头卡、画面层、声音和转场组织起来。
6. 在 Remotion 中逐镜实现。
7. 分段渲染并执行节拍、静止、卡片一致性和音效检查。
8. 合成、响度标准化并交付。

它并不只是一个卡片仓库。SHOTBOOK、时间锚点、素材预检、局部渲染和机器质检共同组成了可执行的制作方法。

### 可直接吸收的资产

- `template/cards/` 中 108 张镜头卡实现。
- `references/cards/` 中 108 份卡片语义说明。
- camera、lifecycle、background、transition、schematic、timing、subtitle 等 motion system。
- CPU 字级时间戳、SHOTBOOK lint、素材预检、分段渲染、静帧渲染和联系表脚本。
- freeze、motion、beat、SFX、frame signature 等 QA 工具。
- 经过示例工程验证的主题框架、字幕和镜头组件。

### 需要改造的部分

- 上游要求单片工程内部准备运行环境；本项目要改成隔离且可复用的运行时。
- 强制 B-roll 比例、固定字幕和固定视觉教条应成为流程配置，不能成为所有口播项目的硬规则。
- Workbench 的 Project → Track → Clip 数据模型可作为未来审片界面参考，当前 Codex 版本不需要先实现 UI。
- 上游的独立多 Agent 复核只能作为可选执行方式，流程本身必须能顺序完成。

### 决策

TalkCraft 作为 `talking-head` 的首个实现基线。第一条可运行垂直流程优先复用它的时间戳、SHOTBOOK、分段渲染和 QA，而不是先重写一套通用剪辑引擎。

## ShotCraft

### 它已经解决的问题

ShotCraft 是一条完整的产品宣传制作流程：

1. 理解产品、受众和使用场景。
2. 确定视觉方向并先做 styleframe。
3. 将产品卖点映射到镜头。
4. 完成 storyboard 并锁定制作范围。
5. 捕获产品真实页面、布局和裁切素材。
6. 逐镜实现，组织镜头、转场、字幕、覆盖层和声音。
7. 统一声音设计并执行最终审片。

它支持模板化、Agent 自主创作和引导式共创三种方式。产品真实页面捕获、功能到镜头的映射和先 styleframe 后量产，是这条流程最成熟的部分。

### 可直接吸收的资产

- 157 张镜头卡及其参考说明。
- 214 个风格记录和对应预览媒体。
- PageCam、FlashCut、ClipCard、DigitRoll、VerticalTicker 等组件。
- camera、motion、rand、shake 等 helper。
- 156 个音频文件。
- 页面 2 倍分辨率捕获、透明裁切和 `layout.json` 的实物素材方法。
- 基于 manifest 的 shot、transition、caption、overlay、audio 分层思想。

### 需要改造的部分

- 镜头卡不应被当作产品工作流本身；它们属于可复用资产层。
- Workbench 和剪映导出是后续能力，当前不用它们来阻塞 Codex 内制作。
- ShotCraft 使用的 Remotion、React 和 Three 版本与其他上游不同，不能把四个仓库的依赖合并到一个 `node_modules`。
- 只在真实项目需要时吸收具体卡片和音频，不一次性复制整个图库。

### 决策

ShotCraft 作为 `product-promo` 的流程基线。产品理解、styleframe、卖点映射、真实页面捕获和逐镜制作整套保留；卡片、组件和音效进入独立资产层。

## Anything2Explainer

### 它已经解决的问题

Anything2Explainer 是一条从主题到成片的知识讲解管线：

1. 研究主题并保存事实来源。
2. 撰写和确认旁白。
3. 生成 TTS 与时间轴。
4. 按句生成 storyboard。
5. 配置 overlay、章节、字幕和图标。
6. 先渲染前 30 秒预览。
7. 分组完成全片。
8. 正式渲染并执行静态和动态质检。

模板已经包含主 Video、Overlay 以及 G1 到 G8 的分组预览 composition。脚本覆盖建项目、TTS、storyboard、预览、正式渲染、静帧、测试渲染、自检、帧指标、运动检查和联系表。

### 可直接吸收的资产

- 研究 → 文稿 → TTS → storyboard → 分组预览 → QA 的完整顺序。
- 中英文、星点或点阵背景、标题、credits、章节和 HUD 配置。
- TTS 时间线生成器和按句 storyboard token renderer。
- selfcheck、frame metrics、motion check 等质量工具。
- 完整示例工程，可作为吸收代码后的回归基线。

### 需要改造的部分

- 黑底白线与紫色强调应成为一个视觉 profile，不等于整个知识讲解流程。
- 固定 G1 到 G8 要根据片长和句数动态生成。
- 上游 `new_project.sh` 会复制模板并在单期项目执行 `npm install`，要改为共享缓存的隔离运行时。
- 多 Agent 分组执行改成可选加速方式，顺序执行也必须能完成。
- 项目结束后必须有清理和归档规则，避免每期复制完整依赖造成膨胀。

### 决策

Anything2Explainer 作为 `knowledge-explainer` 的首个固定风格 profile 和流程基线。先原样跑通其黄金示例，再拆分流程与视觉 profile。

## ThreeUI

### 它提供什么

ThreeUI 是 Three.js、shader 和交互视觉组件的展示与源码集合。当前快照包含：

- 50 个 Community 父级组件、111 条 Community 路由。
- 164 条可浏览的免费 variant/singleton 记录。
- 约 104 个已登记 renderer。
- 47 个 shader family 目录。
- 68 个公开资产文件。

它适合补充背景、shader、3D 标题、光效和高级转场，不负责文稿、分镜、时间同步、渲染验收或交付。

### 需要改造的部分

不少组件使用 `requestAnimationFrame`、`performance.now`、`Date.now` 或 `Math.random`。视频渲染要求同一帧重复计算得到相同结果，因此选中的组件要改为：

- 用 Remotion 的当前帧驱动时间。
- 用固定 seed 代替随机数。
- 明确尺寸、像素比、颜色空间和资源加载时机。
- 在正式纳入资产库前做 seek-safe 和离线渲染验证。

### 决策

ThreeUI 只进入 `library` 资产筛选流程。先建立目录和预览能力，再按真实镜头需求移植组件，不把整个网站或组件库并入 Agent 运行时。

## 横向比较

| 维度 | TalkCraft | ShotCraft | Anything2Explainer | ThreeUI |
| --- | --- | --- | --- | --- |
| 成熟生产流程 | 口播 | 产品宣传 | 知识讲解 | 无 |
| 分镜方法 | SHOTBOOK 与字词锚点 | 卖点到镜头映射 | 按句 storyboard | 无 |
| 可复用资产 | 卡片、motion、QA | 卡片、组件、音效 | 模板、overlay、脚本 | shader、3D、组件 |
| 真实素材策略 | B-roll、图片、证据素材 | 产品页面捕获与裁切 | 研究来源与图标 | 示例资产 |
| 局部预览 | 分镜/分段 | 单镜/styleframe | 前 30 秒/分组 | 组件预览 |
| UI | 可选 Workbench | 可选 Workbench | 无主要工作台 | 展示站 |
| 本项目处理 | 口播基线 | 产品基线 | 讲解基线与 profile | 资产来源 |

## 跨项目技术结论

1. 三条流程可以统一外部生命周期，但不能强行统一内部时间轴、分镜语法和视觉规则。
2. 三个 Remotion 项目使用不同版本组合，应采用按工作流和版本哈希隔离的运行时。
3. 上游仓库不承担单期项目运行，避免源码、依赖、素材和渲染缓存混在一起。
4. UI 数据模型有参考价值，但当前目标是在 Codex 内完成真实视频任务，先做命令和文件契约。
5. 资产按需吸收。每个被吸收的文件都要进入本项目维护范围，并保留来源记录。
