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
- protected_regions：可选 x/y/width/height 矩形，为脸或字幕预留区域。可加 start/end 限定生效时段；省略则全程生效。人物移动或景别变化时按分镜重新声明，避免沿用错误的保护区。
- beats：id/start/end/purpose；秒数相对项目选段开头。
- layers：按绘制顺序排列，后面的层覆盖前面的层。

图层公共字段：id、beat、type、x/y/width/height、start/end。beat 是语义归属；图层可以跨 beat 保留。位置均为当前画幅像素，不默认随画幅迁移；新画幅由 Agent 根据人物与字幕重新排版。

类型：text 需要 text；image 需要已登记 asset ID；panel 为背景面板；line 为矩形线段；connector 为随两端对象移动的曲线；counter 为动态数字；bar 为动态比例条。

style 可配置 fontSize、fontWeight、color、background、radius、borderWidth、borderColor、padding、align 和 fit。颜色用十六进制。文字以纯文本写入，支持换行，不执行 HTML。图片 fit 为 contain 或 cover。

motion 的 kind 支持 reveal（淡入与轻位移）、pop（缩放落位）、draw（按长边展开）、none；duration 是入场秒数。退出在 end 前短暂淡出。不执行任意 JS 表达式。

## 动态关系重组

适合“中心对象 → 分支累积 → 关系点亮 → 真实证据”的解释。先给锚点足够尺寸和阅读时间，再缩小让出分支空间，避免每句话重新换布局。参见 [无素材关系例子](relations-example.json)。

image 可带 keyframes：至少两项，每项 t/x/y/width/height，绝对秒数相对项目选段，首项 t 等于图层 start。相邻项以 cubic ease-out 插值；末项之后保持。坐标和尺寸均为绝对像素，任意 seek 可重建同一帧，不依赖播放历史。

connector 的 from/to 为 `{layer: '对象ID', anchor: 'top'}`；anchor 可为 top/bottom/left/right/center。active_at 是亮线开始绘制的时间，motion.duration 为描线时长。底线先灰色出现，再叠加彩色线；其端点跟随对象关键帧。图层声明的框体应容纳两端对象的所有位置，且避开保护区。端点必须在连线整个区间内存在；绘制顺序宜将线放在对象之前。

示意图和真实素材各有用途：示意图解释关系，真实素材展示界面。若素材只证明界面存在，不把它标记成某操作已成功的证据。

## 数值与比例信息图

counter/bar 使用 values 数组，每项为 t/value，首项 t 等于图层 start，后续严格递增且不超过 end。相邻值支持 value_easing 为 linear 或 ease-out，末项后保持；counter 可设置 decimals 0–3，bar 的值必须在0–1之间。数字和条长度都可任意 seek，不使用实时计时器。no_mask 不禁止语义条形图，条只占其窄图形框体，不能用它铺满背景。

[metric-card.mjs](metric-card.mjs) 提供成组布局生成器：固定列宽、主数字/单位层级、说明基线、等行高条目和共享比例尺。输入 headline/rows 的原始数值时间线，scale 作为所有条目的共同分母，生成可校验的普通 layers。`metric-comparison-example.json` 是从参考片数值做的动画练习，非事实核查或本期口播数据。

计数/比例的含义必须明确。列举数量不等于性能提升，条目显现不等于执行成功，没有比较数据的概念段不强行使用定量图。具体版式由本期内容决定，不要求每个镜头都放大数字。

## 验证边界

校验包括图层时序、素材存在、画幅、框体与保护区交叉；关键帧移动使用保守扫过矩形检查中间路径；连线检查对象引用、存活区间和声明框体。保护区不做真人自动跟踪，pop/reveal 的额外入场运动仍应留边距。浏览器检查文字溢出后才渲染。

使用同一模板渲染不同内容，验证的是数据复用；不代表自动语义导演或整片自动制作已经完成。新动画能力根据实际镜头需要增加。
