# 执行与恢复

本 Skill 随仓库使用，命令工作目录为 winter-video-agent 根目录，不依赖旧工作区。

## 项目与素材

~~~bash
python3 -B -m core.cli doctor
python3 -B -m core.cli new PROJECT --source SOURCE --start 0 --duration 10
python3 -B -m core.cli asset PROJECT asset-id /absolute/image.png --origin builtin-imagegen
python3 -B -m core.cli inspect PROJECT
~~~

图像放在项目 input 下或登记用户原始路径。不要把唯一素材放在待清理 work 中。更换文件内容后重新登记，渲染器会检查哈希。图片支持 PNG/JPEG/WebP。

## 计划

先阅读 [配方和数据契约](../../../library/recipes/progressive-explanation/RECIPE.md)。计划是本项目口播流程格式，不要求其他两条流程采用。

~~~bash
node scripts/semantic-plan.mjs check PROJECT /absolute/plan.json
node scripts/semantic-plan.mjs set PROJECT /absolute/plan.json
~~~

set 写入 input/semantic-plan.json，并在 decisions/plans 保存按内容哈希命名的版本。修改当前 JSON 后也要重新 set；不要绕过已登记版本渲染。

## 运行环境与预览

使用已经可用的外部 Playwright 包及 Chrome，可通过 Codex 的工作区依赖定位工具发现运行时。不要从上游子模块加载依赖，也不要把本机路径固化进模板。

~~~bash
node scripts/render-semantic-preview.mjs PROJECT PLAYWRIGHT_PACKAGE_JSON CHROME_EXECUTABLE preview-v3
~~~

最后额外传入一个秒数可只生成一张合成静帧：

~~~bash
node scripts/render-semantic-preview.mjs PROJECT PLAYWRIGHT_PACKAGE_JSON CHROME_EXECUTABLE layout-v1 3
~~~

脚本会校验计划、输入哈希与文字溢出，按帧渲染透明层，再合成原片和原声；保持源画幅比例，必要时补黑边。输出到 preview，临时文件与计划/模板快照到 work。它不会创建界面、发布视频或自动安装环境。

目前帧缓存仅留作故障诊断，不自动复用。失败保留 work 中的不完整文件，选择新版本号重试；禁止把半成品当成交付。项目变更互斥，锁文件 .semantic.lock 存在时先确认对应进程是否仍在运行，不能直接删锁重入。

## 用户反馈

~~~bash
node scripts/semantic-plan.mjs review PROJECT preview-v3.mp4 approved '用户明确确认的反馈'
node scripts/semantic-plan.mjs review PROJECT preview-v3.mp4 changes-requested '用户要求更大的标题'
~~~

只选择符合用户原话的一条。记录绑定产物及当时的计划哈希；批准旧版不会批准新计划。inspect 可在新会话恢复这些决定。仅生成静帧不等于用户看过动态效果。

## 连续分镜与无覆层底板

计划可声明 `no_mask: true`，拒绝 panel 图层和 style.background；文字使用阴影保持可读。图片仍须人工确认没有伪装成遮罩的底图。

可选 `shots` 数组：`[{"id":"opening","start":0,"end":6}]`。区间以选段内秒数计，必须连续覆盖整个 clip，边界对齐帧。图层时间始终以整个选段为准。

原渲染命令末尾加 `--shot opening` 可只预览指定分镜；输出仍选择新版本名，快照记录 render_range。省略参数则输出整个选段；原单帧秒数参数仍可用。当前没有分镜缓存拼接。
