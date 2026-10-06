# TalkCraft 原生执行入口

当前接通 3 个选中的原生 TSX：`doc-park-left-pill-deal`、`grid-to-hero`、`media-pop-in`。已用「AI 帮我换手机」人工初剪原片产出 17.6 秒的 4:3 有声样片。完整 TalkCraft 内容、自动时间戳、全套卡片和全片编排还没接通，不能将此入口描述成完整自动剪辑。

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

## 原生配置

- 顶层：`schema_version:1`、`engine:"talkcraft-native"`、`fps:30`、`width`、`height`、`sourceFrame`、`durationInFrames`、`construction`。起始帧在完整原片上定位，画幅与登记项目一致。
- `shots`：`id/from/duration/card/heading/placement/props`；镜内时间由 Remotion Sequence 自动归零。
- `placement`：原生 960px 宽组件的 `x/y/scale`，可设置 `height`。不移动、裁切或缩小底层原片。组件内 `config` 保留原生时序/几何参数，按本期口播适配。
- `props`：`docSrc/srcs` 使用已登记素材 ID；其他参数沿用卡片接口。必须传透明根背景，media 卡必须 `showHost:false`，全部替换演示占位。
- `protected_regions`：原片上的 `x/y/width/height`，可用选段局部 `from/duration` 帧范围声明变化；执行前拒绝组件放置框与保护区相交。文字外伸、CSS 和截图内容仍需检查实际画面。
- `no_mask:true` 还需移除白底卡壳、药丸底色等演示皮肤；真实截图自身的 UI 背景保留。当前通过实际画面确认，无通用 CSS 自动遮罩检测。

## 运行文件

每版实例在外部项目 `work/talkcraft-native/VERSION/`：复制自有原生卡片和 Root，保存原生施工配置、模板/素材哈希、运行命令与依赖版本，渲染到项目 `preview/` 或 `render/`。原片、图片使用同一文件系统的硬链接，依赖使用共享缓存；渲染器只读取输入。跨磁盘时复制素材，快照记录 `cross-volume-copy`。`bundle/public` 链接公共素材目录，不再次复制原片。

新试跑单独登记为 `native_trial`，不覆盖过去已经确认的交付状态。`qa/review/deliver` 使用公共生命周期命令。当前 `clean` 只管理既有语义帧缓存，不能自动清理原生实例；保留源码、配置和产物，不把整个实例当作临时缓存删除。

在已生成实例目录，可调用外部运行库的 CLI：`remotion studio src/Root.tsx --no-open`。外部实例独立运行，不依赖旧 Winter-video-workspace。
