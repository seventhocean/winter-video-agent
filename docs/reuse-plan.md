# 代码吸收与实现计划

## 目标

Winter Video Agent 不做四个上游仓库的薄封装，也不重新发明已经成熟的制作流程。它将经过验证的代码吸收到自己的三条流程中，并统一项目生命周期、素材管理、运行环境、预览、质检和交付入口。

## 五层结构

~~~text
Codex Skill / Agent 入口
        ↓
三条独立 workflow
        ↓
共享 core
        ↓
自有 library
        ↓
固定版本的 upstream source
~~~

计划中的自有目录：

~~~text
winter-video-agent/
├── core/
├── workflows/
│   ├── talking-head/
│   ├── product-promo/
│   └── knowledge-explainer/
├── library/
│   ├── cards/
│   ├── motion/
│   ├── three/
│   ├── audio/
│   └── profiles/
├── skills/
├── scripts/
└── docs/
~~~

当前不提前创建空目录。目录在首个可运行功能落地时建立。

## 吸收规则

### 上游保持原样

四个子模块只用于阅读、比较、运行上游基线测试和同步版本。禁止在子模块里保存自有修改或单期视频产物。

### 精确复制后再改

成熟代码可以直接复制到自有目录。每次吸收记录：

- 来源仓库。
- 来源提交。
- 原始相对路径。
- 本项目目标路径。
- 是否原样复制、适配或重写。
- 适配原因和回归验证。

复制后的文件归本项目维护，不依赖子模块运行时路径。

### 用黄金样例守住行为

先在上游提交上运行一个最小黄金样例，记录命令、输入、产物和关键帧。复制后对同一输入做等价验证，再开始结构调整。这样可以区分“吸收失败”和“新设计有误”。

### 按需纳入资产

卡片、音效和 ThreeUI 组件只在真实镜头需要时纳入。资产目录维护可搜索元数据，但不在第一阶段复制数百个文件。

## 各上游处理方式

| 上游 | 第一批直接吸收 | 需要适配 | 暂缓 |
| --- | --- | --- | --- |
| TalkCraft | CPU 时间戳、SHOTBOOK、preflight、分段渲染、静帧与 QA | 配置化画幅、字幕、B-roll 和运行目录 | Workbench、全部卡片 |
| ShotCraft | pipeline、styleframe、卖点映射、页面捕获、PageCam/helper | 产品项目 manifest、确定性随机数、声音登记 | Workbench、剪映导出、全部图库 |
| Anything2Explainer | TTS、storyboard、分组预览、自检与黄金示例 | 动态分组、隔离运行时、风格 profile | 多风格扩展 |
| ThreeUI | 首批被项目实际选中的组件 | 帧驱动、固定 seed、离线渲染 | 整站迁移、全量 shader |

## 运行与存储

Agent 仓库只保存源码和规则。每期视频在仓库外运行：

~~~text
<projects-root>/<project-id>/
├── project.json
├── input/
├── decisions/
├── work/
├── preview/
├── render/
└── delivery/
~~~

其中：

- `input/` 可以保存小型文本和清单；大素材通过登记路径或受控链接引用。
- `work/` 保存该项目可重建的中间文件。
- `preview/` 和 `render/` 可以安全删除后重建。
- `delivery/` 只保存确认交付的文件和校验信息。
- 依赖与浏览器缓存放在统一 cache root，按 workflow、lockfile 和运行版本的哈希隔离。
- 项目配置保存运行时标识，不复制完整 `node_modules`。

项目根目录和 cache root 以后由用户配置，不写死到旧工作区。

## 统一什么

三条流程对外统一这些操作：

~~~text
new → inspect → prepare → preview → render → qa → deliver → clean
~~~

同时统一：

- 项目标识和主流程。
- 输入素材登记与哈希。
- 当前阶段、阻塞原因和用户决定。
- 预览、正式渲染和交付产物清单。
- 可安全清理与必须保留的文件分类。
- 命令退出码和机器可读结果。

## 保留什么

以下内容由各 workflow 自己维护：

- 口播流程的字词时间锚点和 SHOTBOOK。
- 产品流程的 styleframe、卖点映射和镜头 manifest。
- 讲解流程的研究来源、句级 storyboard、TTS 时间轴和视觉 profile。
- 各流程独有的 QA 阈值、预览方式和回修粒度。

这可以避免为了统一协议而破坏上游已经成熟的结构。

## 实现阶段

### M0：仓库与契约

- 固定四个上游提交。
- 写清三条流程、资产层和仓库边界。
- 定义统一生命周期和每条流程的输入输出。

### M1：最小公共底座

- `doctor`：检查 ffmpeg、ffprobe、Node、Python、浏览器和字体。
- `new`：在配置的外部 projects root 创建轻量项目。
- `inspect`：列出项目输入、状态、产物和磁盘占用。
- `assets`：登记外部素材路径、媒体信息和哈希。
- `clean`：只清理可重建文件，先展示回收空间。
- runtime resolver：按 workflow 选择隔离依赖缓存。

### M2：真人口播垂直流程

- 选择一段短口播作为黄金样例。
- 复制并跑通 TalkCraft 的 CPU 时间戳。
- 生成 SHOTBOOK 和一个镜头预览。
- 使用一张现有卡片或一个 motion system。
- 分段渲染、合成并运行最小 QA。
- 在 Codex 中完成一次“修改某一镜并局部重渲”。

### M3：产品宣传垂直流程

- 跑通产品理解、styleframe 和卖点到镜头映射。
- 吸收页面捕获和 PageCam。
- 完成一条短产品样片及声音检查。

### M4：知识讲解垂直流程

- 以 Anything2Explainer 黄金示例验证完整上游。
- 吸收研究、TTS、storyboard、分组预览和 QA。
- 将固定视觉语言拆成第一个 profile。

### M5：资产目录

- 建立 TalkCraft/ShotCraft 卡片的搜索索引。
- 为纳入的 ThreeUI 组件增加确定性渲染适配。
- 为每个自有资产生成缩略图、输入参数和兼容 workflow。

## 第一条流程的验收标准

真人口播 M2 完成时，应当满足：

1. Agent 仓库保持轻量，没有单期素材、依赖或渲染产物。
2. 从一个外部项目目录可重复生成相同预览。
3. 用户只描述需求，不需要手动理解 TalkCraft 目录。
4. 口播时间戳、分镜、镜头代码、预览、QA 和交付状态都能追溯。
5. 修改一个镜头只重建受影响的区段。
6. 清理预览和缓存后仍可从项目配置重建。
7. 上游子模块没有产生未提交修改。

## 当前不做

- 网页或桌面应用。
- 旧中央工作区迁移。
- 通用拖拽时间轴。
- 云端账号、计费和多人协作。
- 一次性导入所有镜头卡、shader 和音效。
- 用一种内部模型重写三条成熟流程。
