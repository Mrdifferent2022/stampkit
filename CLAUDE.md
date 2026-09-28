# CLAUDE.md

StampKit：钣金 DFM 快速评估引擎。纯 Python ≥3.12，src-layout。

## 硬性约定

- **只有 `src/stampkit/backends/` 和 `src/stampkit/freecad_gui/` 允许 import FreeCAD/Part**。其余包（model/rules/engine/report/extraction/rom/api/cli/beaglar_plugin）必须保持 CAD 内核无关。有 AST 守卫测试（`tests/unit/test_architecture_guard.py`）强制。
- **源码中不得引用任何外部学术出版物**（作者/期刊/DOI 等）。有源码扫描守卫测试（`tests/unit/test_source_scan_guard.py`）强制。
- 提取层只依赖 `stampkit.extraction.kernel.GeometryKernel` Protocol；跨进程传输只走 JSON 可序列化的 `ExtractionResult` / `Report`。
- `Report` schema 是对外稳定契约（CLI/面板/AI agent 共用）：只增不改，结构变更升 `SCHEMA_VERSION`。
- 规则扩展三途径（代码装饰器 / YAML 声明式 / entry-point `stampkit.rules`），统一进 `RuleRegistry`；内置规则以 `rules/library/library.yaml` 声明式定义。

## 开发环境

- 虚拟环境：仓库根目录 `.venv`（Python 3.12），不要用全局 Python
- 安装：`./.venv/Scripts/pip install -e ".[dev]"`
- 测试：`pytest`（默认跳过 freecad/bridge 标记）；lint：`ruff check`；类型：`mypy`

## 目录速查

- `src/stampkit/model` 领域模型；`rules` 规则引擎；`engine` 评估编排；`rom` 拉深降阶模型
- `extraction` 几何算法（内核无关）；`backends` FreeCAD 内核实现；`report` 报告 schema
- `api` 服务门面；`cli` 命令行；`freecad_gui` FreeCAD 面板；`beaglar_plugin` beaglar 桥插件
- `addons/StampKitPanel` FreeCAD addon 壳；`rules_custom` 自定义规则示例；`tests` 测试
