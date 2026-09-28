"""Human-readable report rendering (markdown tables)."""

from __future__ import annotations

from stampkit.report.schema import Report


def render_markdown(report: Report) -> str:
    lines = [
        "# StampKit 可制造性评估报告",
        "",
        f"- 板厚: {report.thickness_mm} mm",
        f"- 材料: {report.material}",
        f"- 规则集: {report.ruleset}",
        f"- 特征总数: {report.summary.total_features}"
        f"（通过 {report.summary.accepted} / 需修改 {report.summary.to_fix}）",
        "",
    ]
    if report.warnings:
        lines.append("## 警告")
        lines += [f"- {w}" for w in report.warnings]
        lines.append("")
    lines += [
        "## 明细",
        "",
        "| 规则 | 特征 | 结论 | 实测 | 要求 | 修改建议 |",
        "|---|---|---|---|---|---|",
    ]
    for f in report.findings:
        actual = f"{f.actual:.2f}" if f.actual is not None else "-"
        required = f"{f.required:.2f}" if f.required is not None else "-"
        lines.append(
            f"| {f.rule_id} | {f.feature_id} | {f.verdict} | {actual} | {required} | {f.fix_suggestion} |"
        )
    return "\n".join(lines) + "\n"
