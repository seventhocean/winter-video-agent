# 执行与恢复

本 Skill 随仓库使用，命令工作目录为 winter-video-agent 根目录，不依赖旧工作区。

## 公共入口与运行环境

当前口播流程通过 `python3 -B -m core.cli` 操作。Codex 完成参考分析与逐镜编排，命令负责可重复的执行步骤。每期使用外部项目；依赖不下载到仓库。

首次 prepare 使用可用的外部 Node、Playwright 和浏览器路径，写入本期 project.json.runtime；新会话无需重传。路径变化时重跑 prepare。另一项目可用 `prepare NEW_PROJECT --from-project CONFIGURED_PROJECT` 复用并检查环境。

~~~bash
python3 -B -m core.cli doctor
python3 -B -m core.cli prepare PROJECT --node NODE_EXECUTABLE --playwright-package PLAYWRIGHT_PACKAGE_JSON --browser BROWSER_EXECUTABLE
python3 -B -m core.cli doctor PROJECT
~~~

prepare 检查实际包解析、可执行文件和素材路径，不自动安装或联网。公共入口执行时使用本期保存的运行路径，渲染快照另记实际 Node/Playwright 版本及浏览器路径。

## 项目与素材

~~~bash
python3 -B -m core.cli doctor
python3 -B -m core.cli new PROJECT --source SOURCE --start 0 --duration 10 --width 1280 --fps 30
python3 -B -m core.cli asset PROJECT asset-id /absolute/image.png --origin builtin-imagegen
python3 -B -m core.cli inspect PROJECT
~~~

图像放在项目 input 下或登记用户原始路径。不要把唯一素材放在待清理 work 中。更换文件内容后重新登记，渲染器会检查哈希。图片支持 PNG/JPEG/WebP。

## 计划

先阅读 [配方和数据契约](../../../library/recipes/progressive-explanation/RECIPE.md)。计划是本项目口播流程格式，不要求其他两条流程采用。

~~~bash
python3 -B -m core.cli plan PROJECT /absolute/plan.json --check
python3 -B -m core.cli plan PROJECT /absolute/plan.json
~~~

set 写入 input/semantic-plan.json，并在 decisions/plans 保存按内容哈希命名的版本。修改当前 JSON 后也要重新 set；不要绕过已登记版本渲染。

已完成参考分析和施工单后，可用 [编排能力](../../../library/motion/README.md) 的 object-motion、group-sequence、evidence-focus 和 metric-card 生成图层。`node scripts/find-motion.mjs 关键词` 查用途与来源；`plan PROJECT CONSTRUCTION_JSON --compile` 编译并登记配置。单期仍决定位置、动作、配色和素材，不自动套用上一期计划。

## 运行环境与预览

使用已经可用的外部 Playwright 包及 Chrome，可通过 Codex 的工作区依赖定位工具发现运行时。不要从上游子模块加载依赖，也不要把本机路径固化进模板。

~~~bash
python3 -B -m core.cli preview PROJECT --version preview-v3
python3 -B -m core.cli preview PROJECT --version opening-v1 --shot opening
python3 -B -m core.cli preview PROJECT --version layout-v1 --at 3
python3 -B -m core.cli render PROJECT --version render-v1
~~~

preview 可输出完整选段、一个已声明分镜或静帧，保存到 preview。render 输出完整项目 clip，保存到 render；不自动将短样片拼成全片。版本名在当前项目内唯一，不能覆盖旧输出或同名故障文件。

渲染器校验计划、输入哈希与文字溢出，按帧渲染透明层，再合成原片和原声。保持源画幅比例；是否使用 source_layout 由单期明确决定。成功产物登记前检查尺寸、帧数、时长和源音轨覆盖；失败文件留在 work，不进入正式产物列表。临时帧、计划/模板/运行环境与命令快照保存到 work。

目前帧缓存仅留作故障诊断，不自动复用。失败保留 work 中的不完整文件，选择新版本号重试；禁止把半成品当成交付。项目变更互斥，锁文件 .semantic.lock 存在时先确认对应进程是否仍在运行，不能直接删锁重入。

## 用户反馈

~~~bash
python3 -B -m core.cli review PROJECT preview-v3.mp4 --verdict approved --feedback '用户明确确认的反馈'
python3 -B -m core.cli review PROJECT preview-v3.mp4 --verdict changes-requested --feedback '用户要求更大的标题'
~~~

只选择符合用户原话的一条。记录绑定产物及当时的计划哈希；批准旧版不会批准新计划。inspect 可在新会话恢复这些决定。仅生成静帧不等于用户看过动态效果。

review 根据产物快照的 render_range 与 clip 记录审批范围。单帧、局部分镜或范围未知的产物获得批准时，计划标记 partial-approved；只有覆盖整个 clip 的视频获批，才将该计划标记 approved。

## 交付与清理

~~~bash
python3 -B -m core.cli qa PROJECT render-v1.mp4
python3 -B -m core.cli deliver PROJECT render-v1.mp4
python3 -B -m core.cli deliver PROJECT /absolute/render/render-v1.mp4 --destination /external/Videos/video-v1.mp4
python3 -B -m core.cli clean PROJECT
python3 -B -m core.cli clean PROJECT --apply
~~~

deliver 要求当前计划对应的完整 clip 视频及有效快照，核对文件哈希与媒体参数；复制到项目 delivery 或指定外部目的地，不移动唯一渲染文件。不同内容的同名文件拒绝覆盖，同内容交付可以重复执行。原始素材、input 和 work 不能作为交付目标。默认交付后两个目录中的文件同名，继续操作某一份时使用其绝对路径。

交付继承该产物已有的用户评价；未被评价的技术验收样片保持 awaiting-user，不能宣称审美通过。qa 检查媒体与来源，不作审美批准。渲染器已保存媒体探测结果时复用它，并核对产物哈希，不重复编码视频。

clean 默认列出可回收目录与字节数，--apply 执行。只删除已登记成功产物所关联、快照匹配的 work/VERSION-frames 中的数字命名 PNG。目录有符号链接、其他文件或登记的原始素材时跳过；未完成渲染、未登记目录也保留。素材、计划、模板/命令/环境快照、预览、渲染与交付始终保留。公共命令使用同一项目锁，不自动删除遗留锁。

## 连续分镜与无覆层底板

计划可声明 `no_mask: true`，拒绝 panel 图层和 style.background；文字对比与边缘处理按实际背景选择。图片仍须人工确认没有伪装成遮罩的底图。

可选 `shots` 数组：`[{"id":"opening","start":0,"end":6}]`。区间以选段内秒数计，必须连续覆盖整个 clip，边界对齐帧。图层时间始终以整个选段为准。

公共 preview 的 `--shot opening` 只输出指定分镜，快照记录 render_range。当前没有分镜缓存拼接。旧 Node 计划与渲染脚本仍可直接调用；没有 semantic-plan 的早期 motion.json 项目可继续使用原 Python preview，但不具备上述语义计划、快照和交付链，新增项目使用公共语义入口。
