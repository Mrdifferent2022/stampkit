# StampKit

钣金件可制造性（DFM）快速评估引擎：输入 STEP + 板厚 + 材料，**不跑有限元仿真**，纯几何算法秒级输出特征级 Accept/Fix 报告与修改建议。

## 它能做什么

- 自动识别 9 类钣金特征：孔、槽、缺口、凸台、止裂口、折弯、拉深、压筋、翻边孔
- 剪切类特征走**规则引擎**（内置工艺规则库，三种方式扩展：代码装饰器 / YAML 声明式 / entry-point 插件）
- 拉深类特征走**混合降阶模型**（解析简化分析 + 机器学习分类 + 置信度融合）
- 每条结论给出实测值、要求值与修改建议，机器可读（JSON schema 版本化）

## 架构

```
STEP ──> 几何内核适配层(backends) ──> 特征提取(extraction) ──> ExtractionResult(纯数据)
                                                                │
                                              ┌─────────────────┼─────────────────┐
                                              ▼                                   ▼
                                     规则引擎(rules/engine)              降阶模型(rom)
                                              └─────────────────┬─────────────────┘
                                                                ▼
                                                  报告(report, JSON/MD)
```

唯一与 CAD 内核接触的包是 `stampkit.backends`（FreeCAD/OCCT 实现 `GeometryKernel` 协议）与 `stampkit.freecad_gui`；其余全部纯 Python，可在任意 CPython ≥3.12 上测试运行。

## 安装

```bash
# 开发环境（仓库自带 .venv）
.venv/Scripts/pip install -e ".[dev]"

# 装入 beaglar 的内置 Python（桥插件模式）
scripts/install_beaglar_plugin.py
```

## 使用

```bash
stampkit evaluate part.step -t 2.5 -m steel --format md
stampkit evaluate part.step -t 2.5 -m steel --rules rules_custom/   # 叠加自定义规则
stampkit doctor                                                      # 检查 CAD 内核环境
```

FreeCAD 内手工模式：安装 `addons/StampKitPanel`（见 `addons/README.md`），面板与 CLI/插件调用同一个 `stampkit.api.StampKitService`。

## 自定义规则

无需写代码，放一个 YAML 即可（变量 `t`=板厚，`R`=折弯半径）：

```yaml
- id: hole_min_diameter
  feature: hole
  metric: diameter_mm
  op: ">="
  expr: "t"
  fix: 孔径加大至 >= {required:.2f} mm（当前 {actual:.2f} mm）
```

详见 `rules_custom/example.yaml`。

## 测试

```bash
pytest                        # 单元测试（无需 FreeCAD）
pytest -m freecad             # 需本机 FreeCAD 1.x
pytest -m bridge              # 需可连通的 FreeCAD 桥（本地或云端）
```
