# TalkCraft 原生执行入口

当前接通 3 个选中的原生 TSX：`doc-park-left-pill-deal`、`grid-to-hero`、`media-pop-in`。已用「AI 帮我换手机」人工初剪原片产出 17.6 秒的 4:3 有声样片。完整 TalkCraft 内容、自动时间戳、全套卡片和全片编排还没接通，不能将此入口描述成完整自动剪辑。

2026-10-07，同一执行入口接入七个直接实现的参考场景：`identity-stack`、`metric-comparison`、`evidence-image`、`verdict-stamp`、`development-time`、`database-relations`、`temperature-alert`，源码在 `workflows/talking-head/native/Scenes.tsx`。它们不是 TalkCraft 上游卡片，也没有新增风格包或中间编译器。来源记录在相邻 `scene-provenance.json`。当前覆盖人物介绍、规模比较、证据入场、观点强调，以及大结论加三步流程和双日期线的开发时间段和两侧分类关联的数据库图，以及温度与风险的联动；已补 `metric-process` 窄布局、`grid-to-hero.focusIndices` 逐项聚焦和证据章节/字号参数，产出手机原片的4:3代表预览，用户在2026-10-07明确认可为可用里程碑。固定版本与后续复用见 [里程碑 v1](../../../docs/milestone-talking-head-reference-v1.md)。其余参考表达与全片编排仍未完成；用户认可范围保存在外部项目，不以技术通过替代审美确认。

`cards` 检索中这三项标为 `native-ready`，并返回 `engine:talkcraft-native` 与自有 `native_code`；其余未适配卡保留 `reference-only`。`native-ready` 不表示能经过已有 semantic 图层编译器执行。

## 制作顺序

先分析原片、原声和相关原生成品/演示，在外部项目 `decisions/` 写 SHOTBOOK 施工单。帧锚点来自手工定位时明确记录；不要称为自动字级对齐。再写 `input/talkcraft-shotbook.json`，调用真实 React/Remotion 卡片；此文件不经过 `semantic-plan` 图层转换。现有已确认项目仍可以续作原来的配方。

## 外部依赖和公共调用

`workflows/talking-head/native/runtime/` 仅保存上游固定版本的 package 和锁文件。复制这两个文件到仓库外的共享缓存后，在缓存目录执行 `npm ci --no-audit --no-fund`。每个固定版本只需安装一次。`prepare` 只检查已安装运行环境，不下载或升级依赖。来源和改动见 `library/talkcraft-native/provenance.json`，原始 TSX 保留在 `original/`，方便比较。

```bash
python3 -B -m core.cli prepare PROJECT --engine talkcraft-native \
  --runtime-root EXTERNAL_RUNTIME --node NODE_EXECUTABLE --browser CHROME_EXECUTABLE
python3 -B -m core.cli preview PROJECT --engine talkcraft-native --version native-preview-v1
python3 -B -m core.cli qa PROJECT native-preview-v1.mp4
```

大写词为占位参数。可用 `--native-plan FILE` 指定外部施工 JSON，`--at SECONDS` 检查选段内单帧。每次版本必须新命名，既有产物不覆盖。`render --engine talkcraft-native` 同样执行原生配置；交付仍要求覆盖完整项目区间。技术通过后保持 `awaiting-user`，只有用户明确评价才使用 `review`，不会自动批准审美。

开发参考复建时，用 `preview PROJECT --engine talkcraft-native --studio --version VERSION --native-plan FILE` 只准备同一外部实例，不生成视频、不登记已批准产物，也不改旧交付状态。在返回的实例中运行共享运行库的 `remotion studio src/Root.tsx --no-open`。Studio 的 `OverlayOnly` 显示前景动作，`ReferenceFrame` 显示已登记的对照静帧；校准视图的暗背景不会进入正式 `TalkCraftNative` 成片。复建时逐个镜头对照，不能把原参考上叠加一份相同文字的画面作为交付。

需要观看连续动作时，用 `preview PROJECT --engine talkcraft-native --composition ReferenceComparison --version VERSION --native-plan FILE`。左侧原片、右侧独立前景同步播放，原声仅播放一次；原片中的烘焙动效不复制到复建前景。`--composition OverlayOnly/ReferenceFrame` 也可选；后者要求登记 `referenceSrc`。校准视图只通过 preview 调用，快照和产物记录 composition，deliver 拒绝把校准视频当成正式成片。正式 render 仍选择 TalkCraftNative。

## 原生配置

- 顶层：`schema_version:1`、`engine:"talkcraft-native"`、`fps:30`、`width`、`height`、`sourceFrame`、`durationInFrames`、`construction`。起始帧在完整原片上定位，画幅与登记项目一致。
- `shots`：`id/from/duration/card/heading/placement/props`；镜内时间由 Remotion Sequence 自动归零。
- `placement`：原生 960px 宽组件的 `x/y/scale`，可设置 `height`。不移动、裁切或缩小底层原片。组件内 `config` 保留原生时序/几何参数，按本期口播适配。
- `props`：`docSrc/srcs` 使用已登记素材 ID；其他参数沿用卡片接口。必须传透明根背景，media 卡必须 `showHost:false`，全部替换演示占位。
- `protected_regions`：原片上的 `x/y/width/height`，可用选段局部 `from/duration` 帧范围声明变化；执行前拒绝组件放置框与保护区相交。文字外伸、CSS 和截图内容仍需检查实际画面。
- `no_mask:true` 还需移除白底卡壳、药丸底色等演示皮肤；真实截图自身的 UI 背景保留。当前通过实际画面确认，无通用 CSS 自动遮罩检测。

直接场景使用相同 `shots` 配置；`placement.width` 是实际组件宽度，`height` 必须包含正文、说明和标签。旧三张卡仍使用原生 960px 宽。场景自带标题，不再添加 `heading`；`appearance:light/dark` 由原片背景决定，浅背景使用深色实心字。场景根始终透明，不生成人物或底板。

- `identity-stack`：`chapter:{kicker,label}`、`name/latin`、`facts:[{text,detail?,at,negative?}]`，可选 `nameAt`、`action:{kicker,text,at}`。名字保持，事实按时间累积，最后补行动。
- `metric-comparison`：`chapter`、`metric:{value,unit,label,context,at,decimals?}`、`rows:[{label,value,unit,at,primary?}]`、`scaleMax`、`result:{text,at}`、`source` 和可选 `tags`。计数按参考连续采样重建；横条共用量程，结果只能在最后一条增长完成后出现。
- `evidence-image`：已登记素材 `docSrc`、`imageHeight`、`caption`、可选 `at`。图片向左落位并显现，标签依附图片，使用 contain 保留完整图片。 可选 `chapter:{kicker,label}` 和 `captionSize`（默认24）用于本期窄布局的可读标题与标签；新增章节须增加放置高度。
- `verdict-stamp`：`chapter`、`question/statement/stamp`、`statementAt/stampAt`。先建立观点，再进行短促的缩小落位，之后保持。
- `development-time`：`chapter`、`headline:{value,unit,caption,at}`、三个 `nodes:[{text,detail,at,imageIndex}]`、已登记 `srcs`、`timeline:{at,events:[{date,label,caption,at}],resultAt,caption}`、`clearAt`。两个 ISO 日期按先后顺序输入，间隔天数由日期相减生成。标题、节点、日期和结论顺序建立，清场前全部保持。逻辑框 1300×780，实际宽度按 placement.width 缩放；用本期正文和构图调整放置，不能将参考坐标直接套到 4:3 原片。图标是本期已登记的矢量素材，不在上游子模块生成文件。
- `database-relations`：`chapter/chapterAt`、`hub:{text,system,hint,at,imageIndex}`、`left/right:[{text,at,imageIndex,activeImageIndex}]`、已登记 `srcs`、`activateAt`、`result:{text,detail,at,imageIndex}`、`clearAt`。左右各 1–5 项，中心先建立，分类按各侧读序进入，全部落位后统一激活。灰线、图标与边框同时转绿；中心保留蓝色，平台说明中的分类数由左右节点计数生成。标准态和激活态 SVG 使用相同路径；浅背景项目须登记适合背景的深色标准图标。逻辑框 1500×850，清场必须完整落在镜内。跨底片换镜保持同一场景时序，不重新启动节点。

- `temperature-alert`：`chapter/sectionNumber`、`condition:{text,at,imageIndex}`、`reading:{unit,samples:[{at,value}]}`、`range:{comfortable:{min,max,position},threshold:{value,position}}`、`risk:{text,source,at,imageIndex}`、`before:{label,scaleText,at,nodes:[{text,at,imageIndex}]}`、`after:{kicker,label,at}`、已登记 `srcs` 和 `clearAt`。读数单调上升并跨过上限，同一采样读数驱动色条揭示和超限颜色；风险在升温完成后出现，再建立三个处理节点与自动回报。色条是参考的示意增长，position 是 0–1 的标记位置，不是等比例测量轴。章节从前一证据镜保持，正文先清、章节稍后清；逻辑框 900×730。浅背景须登记深色图标并选择 light。

- `metric-process`：`chapter`、`metric:{value,unit,context,at}`、真实盘点素材 `docSrc`、`evidence:{at,caption}`、三个 `steps:[{text,detail,at}]`、`result:{text,at}`、`clearAt`。与指标比较共用已确认采样计数，来源和三步说明依附主数值、按读序累积；结果并入第三步说明。用于计数＋流程，不能替代共用量程的比较条。逻辑框520×820，按实际背景与人物留白放置；不改变底片大小。

原生 `grid-to-hero` 新增可选 `focusIndices:[0..3]`，可依次聚焦多项，每次沿用同一放大/旁列/归位曲线；不传时保留单主角默认动作。`caption` 可标注真实素材的来源与举例范围。持续时间需覆盖全部聚焦周期：lead＋enterDur＋3×stagger＋holdGrid＋项目数×(2×reflow＋holdHero)＋holdBack＋exit＋3×exitStagger。案例与本期值保存于外部 SHOTBOOK，不把手机应用或坐标写进卡片。

所有 `at` 是镜内秒数，由帧计算驱动。顶层可选 `referenceSrc` 是已登记的参考静帧素材 ID，仅供对照视图使用。位置校验针对放置框和保护区；入场位移、长文字及最终真实背景仍需目视检查，不能将通过校验称为审美通过。

## 运行文件

每版实例在外部项目 `work/talkcraft-native/VERSION/`：复制自有原生卡片和 Root，保存原生施工配置、模板/素材哈希、运行命令与依赖版本，渲染到项目 `preview/` 或 `render/`。原片、图片使用同一文件系统的硬链接，依赖使用共享缓存；渲染器只读取输入。跨磁盘时复制素材，快照记录 `cross-volume-copy`。`bundle/public` 链接公共素材目录，不再次复制原片。

新试跑单独登记为 `native_trial`，不覆盖过去已经确认的交付状态。`qa/review/deliver` 使用公共生命周期命令。当前 `clean` 只管理既有语义帧缓存，不能自动清理原生实例；保留源码、配置和产物，不把整个实例当作临时缓存删除。

在已生成实例目录，可调用外部运行库的 CLI：`remotion studio src/Root.tsx --no-open`。外部实例独立运行，不依赖旧 Winter-video-workspace。
