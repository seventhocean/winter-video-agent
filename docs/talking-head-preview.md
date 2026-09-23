# 口播图片动效预览 v0

## 当前阶段：数据驱动配方

2026-09-23：渲染入口改为读取外部项目 input/semantic-plan.json，使用 library/recipes/progressive-explanation/stage.html。文案、素材、画幅、坐标和时序都来自计划，具体命令见 [Skill 执行说明](../skills/winter-video-agent/references/execution.md)。

计划按内容哈希保存版本，预览绑定计划和素材指纹。用户反馈只作用于对应版本；修改计划不会继承旧版批准。所有项目写入命令与语义渲染互斥，输入变更会在渲染前报告。浏览器做文字溢出检查，FFmpeg 保留源视频比例。

原 V2 专用模板保留作历史参考，不再由当前渲染入口加载。下面 V0/V2 的说明是阶段记录，不能用它们推断当前命令仍写死内容。

## 递进解释样片 v2

新增 `workflows/talking-head/semantic-stage.html` 和 `scripts/render-semantic-preview.mjs`，用于 1280×960、开头约 9.6 秒的已登记口播样例。当前是特定样片 profile，内容、坐标与语义时间点写在模板内，尚不是自动规划器。

顺序为章节导航与服务器对象 → 真实 OpenCode 终端截图 → 自然语言需求示意 → AI 助手和需求/理解/执行链路。图片继续使用内置 AI 生图结果，终端来自用户实录，标题、连线和状态由独立图层控制。没有新增配音或覆盖原字幕，也未声称实际完成画面中示意的部署任务。

脚本用已有外部 Playwright 运行时和 Chrome 按帧捕获透明图层，再由 FFmpeg 合成口播。依赖不安装到 Agent 仓库；帧缓存、模板快照、执行命令与预览写入外部项目，默认不覆盖旧版本。

~~~bash
node scripts/render-semantic-preview.mjs /absolute/project /absolute/node_modules/playwright/package.json /absolute/chrome preview-v2
~~~

本 profile 只代表本次参考片方向，未经用户确认不升级为其他项目的默认风格。下一次先依据用户审片意见调整布局、节奏和信息密度，再决定是否抽象为通用语义镜头。

本版用真实口播验证最小闭环：创建仓库外项目 → 登记素材 → 写图片运动关键帧 → FFmpeg 合成 → 等用户看样片。图片由 AI 生图或用户提供，代码只处理运动和合成。

## 命令

在 Agent 仓库运行：

~~~bash
python3 -B -m core.cli doctor
python3 -B -m core.cli new /absolute/external/project --source /absolute/source.mov --duration 9.6
python3 -B -m core.cli asset /absolute/external/project robot /absolute/robot.png --origin builtin-imagegen
python3 -B -m core.cli inspect /absolute/external/project
python3 -B -m core.cli preview /absolute/external/project --output preview-v1.mp4
~~~

每个命令输出 JSON。项目原片只登记路径和 SHA-256，不复制。重复渲染必须使用新版本文件名，不覆盖用户已经看过的预览。

## 图片运动配置

项目内的 `input/motion.json` 保存 `layers` 数组。每层有已登记的 `asset`、片段局部秒数 `start/end` 和 `keys`。每个关键帧包含 `t`、`width`、`x`、`y`：宽度为像素，x/y 是图片中心。所有时间相对于选取片段的开头。

~~~json
{
  "layers": [{
    "asset": "robot",
    "start": 1,
    "end": 5,
    "keys": [
      {"t": 1, "width": 100, "x": 1400, "y": 450},
      {"t": 1.6, "width": 440, "x": 1050, "y": 450},
      {"t": 2, "width": 390, "x": 1060, "y": 470},
      {"t": 5, "width": 420, "x": 1050, "y": 450}
    ]
  }]
}
~~~

关键帧采用余弦缓入缓出，支持滑入、放大、回落、缩小让位。透明 PNG 的 alpha 在合成时保留。原视频与已嵌入字幕整体等比缩至 1280 宽；保留原声，不再次剪口气。

分镜设计参考固定版本 TalkCraft 的语义节拍和让位方法。当前合成代码为自有 FFmpeg 实现，没有宣称已经移植 Remotion 卡片、时间戳对齐或上游 QA。

## 第一次实际样例

- 日期：2026-09-22。
- 原片：用户 Videos 中 9 月 16 日智能助手的人工粗剪版本。
- 选段：开头 0–9.6 秒。
- 外部项目：`~/Movies/WinterVideoAgentProjects/2026-09-22-assistant-preview/`。
- 画面：右侧服务器与疑问终端放大、缩小让位，再由 AI 助手滑入接管。
- 图片：内置 imagegen 生成透明 PNG；原始提示词保存在项目 `input/image-prompts.json`。
- 语义定位：读取原片已有字幕，未运行字级强制对齐。本地 Whisper small 未缓存，未下载模型。
- 验证范围：一次实际预览渲染、媒体参数读取、代表帧检查。审美和节奏等待用户确认。

## 当前边界

这是图片叠加预览子流程，尚不支持自动语义规划、自动字幕、字级对齐、完整素材清理、渲染缓存失效、并行写入或全片生产交付。`doctor` 只检查这条 FFmpeg 流程所需的三个命令，不代表完整 Remotion 环境就绪。

保留原片、原字幕和原口播。无需生成的元素不占用 AI 调用；需要生成的解释性插图不由代码假画。用户修改时间点或运动幅度后，再用新的预览版本渲染。
