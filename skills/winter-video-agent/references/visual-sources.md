# 成品视觉参考与效果候选

2026-09-26，用户明确要求今后多参考三个上游项目的成品视觉设计，再扩充效果。此文件是选型入口，不是已实现能力清单。当前项目V8成组信息图已获用户认可；该视觉评价仍只属于本期。

## 使用顺序

1. 明确这一段是比较、趋势、步骤、并列、证据、概念机制还是章节交接。
2. 先看下表的成品帧/预览，再读对应卡片和准确实现；有动态样片时检查进场、展开、停留、退出，不能凭封面猜时序。本轮本地检查了预览静帧与部分准确源码，没有声称看完三个项目所有视频。
3. 在外部项目的决定或分镜里记录来源提交、卡片/镜头、选用的版式关系、动作顺序和必要适配。沿用本期人物位置、画幅和确认方向。
4. 有成熟代码就按项目吸收规则复制到自有目录适配；保留来源提交和路径。未移植条目仍是候选，不能在制作时当成可调用组件。
5. 出一个代表镜头供用户判断。只修明确故障，不自动审美重渲；按需增加效果，不为了覆盖图库而增加镜头。

## 三个来源的分工

- TalkCraft：口播与图片证据的版式关系、逐项/成组时序、图表、人物互动。
- ShotCraft：标题到章节标签的转换、真实产品页运镜、数字滚轮、转场的完整动作弧。
- Anything2Explainer：实际知识讲解成片的主次、概念流程、结果强调与章节延续。

ThreeUI仍是资产来源，不作为第四条制作流程。

## 第一批候选

| 语义用途 | 成品/预览入口 | 卡片或准确实现 | 选用要点与限制 |
| --- | --- | --- | --- |
| 整体增长趋势 | [TalkCraft 柱状增长](../../../video-talkcraft/gallery/thumbs/bar-chart-growth.png) | [卡片](../../../video-talkcraft/references/cards/bar-chart-growth.md)、[源码](../../../video-talkcraft/template/cards/bar-chart-growth.tsx) | 基线先出现，柱子密错峰作为一次连续动作，结论在数据落稳后出现；需要真实趋势数据，不能用于并列操作举例 |
| 有顺序的步骤 | [TalkCraft 竖向步骤线](../../../video-talkcraft/gallery/thumbs/step-timeline-vertical.png) | [卡片](../../../video-talkcraft/references/cards/step-timeline-vertical.md)、[源码](../../../video-talkcraft/template/cards/step-timeline-vertical.tsx) | 线到哪节点才亮，文字略滞后；清单不伪装成因果时间轴 |
| 主张加两条证据 | [TalkCraft 多图接力](../../../video-talkcraft/gallery/thumbs/still-layout-relay.png) | [卡片](../../../video-talkcraft/references/cards/still-layout-relay.md)、[源码](../../../video-talkcraft/template/cards/still-layout-relay.tsx) | 一主两辅，主图先落，焦点随口播接力；上游适用于人物离场的素材镜头，人物在场先查 parallel-items-with-host，不直接套其布局 |
| 章节标题延续 | TalkCraft [同类预览](../../../video-talkcraft/gallery/thumbs/title-demote-to-label.png)；ShotCraft提供动作实现 | [ShotCraft 卡片](../../../video-shotcraft/references/shots/typography/title-demote-to-label.md)、[源码](../../../video-shotcraft/demos/typography/title-demote-to-label/TitleDemoteToLabel.tsx) | 大标题读完再一次缩小移到章节标签，内容交接不断档；当前未实看此卡动态视频，不能宣称复制其全部视觉参数 |
| 王牌指标亮相 | ShotCraft卡片/实现；本地未发现同名视频或封面 | [卡片](../../../video-shotcraft/references/shots/data/odometer-digit-roll.md)、[源码](../../../video-shotcraft/demos/data/odometer-digit-roll/OdometerDigitRoll.tsx) | 各数位滚动并逐位停稳，区别于当前数值递增；仅候选，需先确认动态成品再移植，不用循环乱数假装真实计算 |
| 真实页面主角 | [ShotCraft 聚焦主卡](../../../video-shotcraft/gallery/media/poster/spotlight-hero-card.jpg) | [卡片](../../../video-shotcraft/references/shots/opening/spotlight-hero-card.md)、[源码](../../../video-shotcraft/demos/opening/spotlight-hero-card/SpotlightHeroCard.tsx) | 页面推进、卡片浮起、轮廓扫描、归位是一个动作弧；本期不要遮罩，不能连同vignette压暗照搬到人物底片 |
| 图文接力 | [ShotCraft 胶片条](../../../video-shotcraft/gallery/media/poster/word-relay-filmstrip.jpg) | [卡片](../../../video-shotcraft/references/shots/typography/word-relay-filmstrip.md)、[源码](../../../video-shotcraft/demos/typography/word-relay-filmstrip/WordRelayFilmstrip.tsx) | 让关键词和对应素材接力，而不是每项漂在不同位置；先确认素材关系和阅读时间 |
| 信息筛选/收敛 | [Anything2Explainer 重排漏斗](../../../anything2explainer/examples/rag/frames/ref_rerank_funnel_f4900.jpg) | [SC26](../../../anything2explainer/examples/rag/shots_src/G6/SC26.tsx)、[分镜表](../../../anything2explainer/examples/rag/分镜表.md) | 输入集合→筛选→留下重点；上方流程导航与主体关系分层，图文密度来自分组 |
| 反复执行到条件满足 | [Anything2Explainer Agentic闭环](../../../anything2explainer/examples/rag/frames/ref_agentic_loop_f6900.jpg) | [SC37](../../../anything2explainer/examples/rag/shots_src/G7/SC37.tsx) | 循环节点、移动状态、评估结果、独立回答出口；读过准确源码中的时间编排，不能把出口画在每轮必经位置 |

## 成品审美对照

查看 [Anything2Explainer 正反例对照](../../../anything2explainer/examples/contrast/contrast_sheet.jpg) 和 [对照说明](../../../anything2explainer/examples/contrast/README.md)：主体太小、结果不突出、背景碎屑太多，即使动效数量相同仍会显散。学习其主次与信息关系；黑底、紫光、抖动不是当前真人口播的全局视觉规则。

## 固定来源

- TalkCraft：`b7fb9ac943c64b1d6dd61f9576635b173602a4a4`
- ShotCraft：`5e71af35a2daee492dd3ea93e5e8903f32dcd13c`
- Anything2Explainer：`5544f599522cc0f7bab6d0dfe823905059641172`

本轮只有参考阅读、用户反馈记录和入口更新，未复制上游组件、安装依赖或重渲视频。后续移植以具体镜头需要为单位，优先步骤线、图文证据接力、章节标题延续；数字滚轮与页面运镜在有适合内容时再接入。
