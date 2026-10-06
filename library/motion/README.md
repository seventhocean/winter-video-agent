# 可配置的口播编排能力

这是对自有数据配方的整理，返回普通图层，不绑定题材、画幅、字体或素材。方法选择遵循 [先参考、再编排](../../docs/talking-head-editing-method.md)。上游成品与源码用于设计依据；本轮没有复制上游组件代码。

运行 `node scripts/find-motion.mjs 展开` 可查用途、参数和参考来源。完整目录见 [catalog.json](catalog.json)，确定性实现见 [choreography.mjs](choreography.mjs)。

| method | 输入 | 产物 |
| --- | --- | --- |
| `object-motion` | 普通图层信息、`poses: [{t,x,y,width,height}, ...]`、`end` | 同一对象的位移和缩放关键帧，可用于大标题变标签、物体迁移 |
| `group-sequence` | `id/beat/items/phases/end`、可选 `stagger` | 每个 item 在多个阶段保持身份；phase 为 `{t,poses}`，poses 按 items 顺序给出几何 |
| `evidence-focus` | `id/beat/asset/views/end/style` | 同一真实截图的窗口与裁切关键帧；view 为 `{t,x,y,width,height,crop}`，crop 是归一化区域 |
| `metric-card` | [既有指标布局参数](../recipes/progressive-explanation/RECIPE.md)、可选 `theme` | 有共同比例尺的计数、单位、说明与比较条 |

group 的首阶段时间加 `stagger × item序号` 作为入场起点；后续阶段在共同时间重排。时间按当前选段的秒数声明，不能把参考卡的固定节奏直接套到口播。style 用单期选择，物体先大后小也必须有内容上的理由。

## 用配置生成计划

外部项目的 `input/motion-plan.json` 保留现有配方的 `schema_version/recipe/intent/canvas/beats/shots/protected_regions`，可直接放 `layers`，再用 `motions` 声明上述方法：

~~~json
{
  "motions": [
    {
      "method": "object-motion",
      "id": "subject",
      "beat": "explanation",
      "type": "image",
      "asset": "registered-illustration",
      "end": 6,
      "style": {"fit": "contain"},
      "poses": [
        {"t": 0, "x": 850, "y": 200, "width": 360, "height": 320},
        {"t": 1.5, "x": 850, "y": 200, "width": 360, "height": 320},
        {"t": 2.2, "x": 900, "y": 180, "width": 160, "height": 140}
      ]
    }
  ]
}
~~~

以上只是 motions 字段的示例，须与本期完整分镜、已登记素材和实际人物区域一起使用。执行 `python3 -B -m core.cli plan PROJECT CONSTRUCTION_JSON --compile`，公共编译器生成并登记 `input/semantic-plan.json`；施工配置另存到 `decisions/constructions/`，方法来源写入计划。无任意 JavaScript 表达式执行。

此格式只服务当前口播配方，不要求产品宣传或知识讲解采用它。代码能表达动作不代表设计获认可；图解也不代表操作成功。
