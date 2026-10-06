# 内容、参考与逐镜施工

用于新口播或需要重新设计的语义段。Codex 判断口播任务、查看参考、填写编排；本地命令校验输入、推荐候选并关联执行计划。已有明确施工单的小修订无需重新检索全库。

## 使用顺序

~~~bash
python3 -B -m core.cli cards --query '传输' --limit 6
python3 -B -m core.cli cards --semantic 定义 --limit 6
python3 -B -m core.cli brief PROJECT
# Codex 检查原片/文稿并编辑内容说明
python3 -B -m core.cli brief PROJECT /absolute/annotated-brief.json
python3 -B -m core.cli suggest PROJECT --top 5
python3 -B -m core.cli storyboard PROJECT --init
# Codex 查看候选成品/源码，完成施工单和本期 motion JSON
python3 -B -m core.cli storyboard PROJECT /absolute/storyboard-v1.json --construction /absolute/motion-v1.json
python3 -B -m core.cli plan PROJECT /external/project/input/motion-plan-planned.json --compile
python3 -B -m core.cli preview PROJECT --version reference-v1 --shot REPRESENTATIVE_SHOT
~~~

所有输出在外部项目。brief 只生成待标注骨架；已有计划时读取语义段与已有 caption 图层，不转写音频。storyboard --init 只生成待填写字段，不把排名第一当作设计。运行时、素材登记和后续反馈见 [执行说明](execution.md)。

## 内容说明：input/content-brief.json

顶层为 schema_version: 1、intent、timing_basis、project_basis、segments。project_basis 由 brief 生成，包含源/素材哈希、选段与格式。素材登记变化后更新内容说明并重新 suggest。手工时间、既有字幕、转写对齐应如实说明；语义概述注明不是逐字稿。

| 每段字段 | 含义 |
| --- | --- |
| id / start / end | 整个选段内秒数，语义段连续覆盖选段；不按每句话机械换卡 |
| text / purpose | 实际口播或注明的语义概述；观众需要理解的事 |
| mode | enhance 或 source；保留口播/操作原片也是主动选择 |
| semantics | TalkCraft 已发布的 26 项词表；Codex 按内容判断 |
| needs | 证据、身份、量化、对比、结构、强调、无，可多选 |
| entities / host_present | 本段对象与实际人物是否在场 |
| materials | `[{"asset":"registered-id","kind":"image或screenshot或video"}]`；登记来源不代表素材适合本段 |
| material_requests | `[{"description":"需要什么","required":true,"asset":"补齐后登记的ID"}]`；未补齐的 required 请求阻止完成施工 |
| position / reference_query | 开场、中段、收尾或任意；跨库关键词检索 |
| previously_selected | 续作时填写此前实际选择的卡 ID，供前两段重复提示；未使用的首选候选不计入历史 |

自动语义匹配目前使用 TalkCraft 卡片、自有已接通编排和两项已整理的 Anything2Explainer 案例。ShotCraft 的全量卡片与 AwesomeOpus 案例参加关键词检索；它们没有同一套语义标注，不能声称已完成全库自动语义匹配。ThreeUI 仅提供组件资产入口。

候选输出 input/card-candidates.json，按哈希归档到 decisions/candidates。排序复用 TalkCraft 的输入可行性、素材匹配、位置、前两段实际重复、多图数量和写死内容代价，再加语义匹配数量。ready_candidates 单列已接通项；不为“能运行”强行改写画面任务。

## 逐镜施工单

顶层为 schema_version: 1、当前 brief_sha256、candidates_sha256、references、segments。使用 --init 的骨架即可取得当前哈希。

references 每项记录 id、候选 card_id（用户案例可省略）、task、grouping、motion、adaptation。evidence 为实际查看/读取的证据：`[{"kind":"image或video或code或document","path":"实际文件绝对路径","locator":"时间段、静帧或源码位置","findings":"具体发现"}]`。静帧和源码分析不能冒充观看动态样片；命令检查来源可追溯，不验证 Agent 的视觉判断。远端候选未观看时保持候选，当前施工证据入口使用已有本地文件。

每个 segments 项与 brief 的 id/mode 对应：

- selections：`[{"card_id":"...","reason":"适配本段的理由"}]`。候选外选择补 deviation_reason；reference-only 条目补 implementation_note，不能把它写成已能直接调用。
- reference_ids：所选卡自己的分析，可另加用户案例。
- objects：`[{"id":"local","role":"本地端点","basis":"source或schematic或evidence或text","asset":"可选登记ID"}]`。evidence 对象须有登记素材；真实操作原片使用 source。
- phases：`[{"start":1.4,"end":3.7,"kind":"establish","objects":["local"],"action":"完整过程"}]`。kind 为 establish/change/read/handoff/hold，时间连续覆盖本段，增强段保留 read/hold。阶段可以描述多种同时发生的动作。
- layout、handoff_in、handoff_out：本期人物/字幕空间、背景对比，上一段留下什么、下一段承接什么。
- render_ids：本期 construction JSON 的 layers 或 motions ID。每个 motion 须映射到施工段；持续对象可被多段引用。已接通卡的选择须对应实际 method。
- source 段写 reason，说明原片为何足够，仍记录停留与交接。

storyboard --check 只校验；常规命令归档施工单、生成可读 Markdown 和 input/motion-plan-planned.json。无需用户逐项批准施工单；Codex 按授权出代表预览，审美状态保持 awaiting-user。

编译及渲染校验内容说明、候选索引、施工单、本期 construction 输入和已分析参考文件哈希。输入变化后更新关联施工；历史产物和快照保留。这不等于支持自动局部重组。

## 当前接通的成熟编排

TalkCraft 的 title-demote-to-label 已适配为可调用 method，复用时间参数和内容交叠调度；标题缩放/位置共享 cubic inOut。单期指定标题、起终几何、至多四个内容对象、口播锚点和样式。未移植 blur、clip-path、整屏底色和装饰，不能声称逐像素复刻上游成品。参数见 [编排库](../../../library/motion/README.md)，来源见 [适配记录](../../../library/planning/provenance.json)。
