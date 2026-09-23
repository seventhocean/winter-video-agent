# 递进关系讲解

适用：口播逐步解释一个对象、一组事实或一条因果链。目的不是保持所有元素运动，而是让观众看见信息如何累积。可用 AI 对象、真实证据和可编辑标注共同表达。

## 导演步骤

1. 找出语义段的主张、困难、过程、结果，不强制每段四项齐全。
2. 为每个 beat 写 purpose，说明观众应理解什么。
3. 选一个视觉锚点，决定哪些信息跨 beat 保留、哪些退场。
4. 为新概念选择真实证据或解释性图片；用文字和线说明关系。
5. 按口播安排显现时间，保留阅读时间和人物/字幕区域。

配方不绑定服务器、机器人、暗色背景或右侧布局。示例 [example.json](example.json) 是不同题材的 16:9 资料整理图，没有图片依赖。

## 计划字段

- schema_version：1。
- recipe：progressive-explanation。
- intent：该镜头解释什么。
- canvas：width/height，与项目 format 一致。
- protected_regions：可选 x/y/width/height 矩形，为脸或字幕预留区域。
- beats：id/start/end/purpose；秒数相对项目选段开头。
- layers：按绘制顺序排列，后面的层覆盖前面的层。

图层公共字段：id、beat、type、x/y/width/height、start/end。beat 是语义归属；图层可以跨 beat 保留。位置均为当前画幅像素，不默认随画幅迁移；新画幅由 Agent 根据人物与字幕重新排版。

类型：text 需要 text；image 需要已登记 asset ID；panel 为背景面板；line 为矩形线段。

style 可配置 fontSize、fontWeight、color、background、radius、borderWidth、borderColor、padding、align 和 fit。颜色用十六进制。文字以纯文本写入，支持换行，不执行 HTML。图片 fit 为 contain 或 cover。

motion 的 kind 支持 reveal（淡入与轻位移）、pop（缩放落位）、draw（横向展开）、none；duration 是入场秒数。退出在 end 前短暂淡出。当前不提供路径运动或任意 JS 表达式。

## 验证边界

静态校验包括图层时序、素材存在、画幅、框体与保护区交叉；保护区不做真人自动跟踪，也不保证运动过程的每帧安全，Agent 应为入场留边距。浏览器检查文字溢出后才渲染。

使用同一模板渲染不同内容，验证的是数据复用；不代表自动语义导演或整片自动制作已经完成。新动画能力根据实际镜头需要增加。
