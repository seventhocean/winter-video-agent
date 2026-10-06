# 口播公共执行链

2026-10-06。将已实际制作使用的口播配方收成公共入口，减少单期专用执行脚本。

## 本轮实现

- `core.cli prepare` 检查外部 Node、Playwright、浏览器与素材路径，保存到外部项目；后续直接 preview/render，可从其他项目复用环境配置。
- `plan` 校验/登记语义计划，`plan --compile` 将施工配置的动作方法编译为普通图层，并保存配置与来源。
- `preview` 输出静帧、指定镜头或完整选段；`render` 输出完整项目 clip。渲染器在产物登记前检查尺寸、帧数、时长与音轨，失败文件保留在 work。
- `qa/deliver` 核对产物哈希、当前登记输入与快照；交付保留渲染源，拒绝覆盖不同内容和写入素材目录，用户评价不由技术检查替代。
- `clean` 预览或清理已完成渲染所关联的帧缓存，保留输入、计划、快照和全部视频。`inspect` 按目录列出项目磁盘占用。
- 自有编排目录提供 object-motion、group-sequence、evidence-focus、metric-card；字体、配色、布局、素材与动作时间由单期配置。来源记录区分上游设计参考与自有实现，本轮没有复制上游代码。

## 真实验证

另建外部项目 `2026-10-06-nginx-workflow-validation`，取历史 Nginx 原片29.6–53.1秒。分析用户参考片的连续状态、TalkCraft人物在场成组呈现与ShotCraft标题延续方法，先写施工单，再用JSON配置对象、分组与真实SFTP证据。

公共入口输出23.5秒、705帧、1280×960、30fps且有原声的视频。执行过布局预览与一次完整选段渲染，没有反复审美重渲。交付状态保持awaiting-user；这是工作流验证样片，不是Nginx整期已获批准的成片。

清理回收61,376,806字节，原素材、配置、版本、模板/命令/运行环境快照、预览、渲染和交付均保留。定向验证确认：不同内容的同名交付文件不被覆盖，input目标拒绝写入，未登记目录不被清理。详细记录位于该项目 `decisions/reference-and-construction.md` 与 `decisions/lifecycle-verification.json`。

## 能力边界

Codex继续承担内容分析、成品参考阅读和分镜设计。当前不自动转写对齐、不做人脸跟踪、不自动复用或拼接局部渲染缓存；补充视频素材层与其他两条生产线仍未接通。完成公共执行链及第二段实际验证，不等于所有题材的审美已经稳定。

使用 [公共命令](../skills/winter-video-agent/references/execution.md) 与 [编排能力](../library/motion/README.md)。
