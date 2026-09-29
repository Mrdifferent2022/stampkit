"""End-to-end integration runner, executed by freecadcmd:

    freecadcmd scripts/run_integration.py

Generates fixtures, evaluates them through StampKitService, and asserts the
expected feature counts and violations. Exits non-zero on failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))


def _failures(results: list[tuple[str, bool, str]]) -> int:
    failed = 0
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
        failed += 0 if ok else 1
    return failed


def main() -> int:
    from stampkit.api.dto import EvaluateRequest, LocalPathInput
    from stampkit.api.service import StampKitService

    # Regenerate fixtures for reproducibility.
    subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts", "gen_fixtures.py")], check=False
    )

    service = StampKitService()
    fixtures = os.path.join(REPO, "tests", "fixtures", "step")
    results: list[tuple[str, bool, str]] = []

    def evaluate(name: str, t: float, material: str):
        req = EvaluateRequest(
            part=LocalPathInput(path=os.path.join(fixtures, name)),
            thickness_mm=t,
            material=material,
        )
        return service.evaluate(req)

    # Fixture A: flat plate t=3 -> 5 holes, 2 slots, 0 bends, all Accept.
    rep = service and evaluate("plate_a.step", 3.0, "aluminum")
    kinds = rep.summary  # noqa: F841
    counts = {}
    for f in rep.features:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    results.append(("plate_a holes", counts.get("hole") == 5, f"got {counts.get('hole')}"))
    results.append(("plate_a slots", counts.get("slot") == 2, f"got {counts.get('slot')}"))
    results.append(("plate_a bends", counts.get("bend", 0) == 0, f"got {counts.get('bend', 0)}"))
    results.append(("plate_a all accept", rep.summary.to_fix == 0, f"to_fix={rep.summary.to_fix}"))

    # Fixture B: L-bracket t=2.5 -> 3 holes, 1 bend (R=5), all Accept.
    rep = evaluate("bracket_b.step", 2.5, "steel")
    counts = {}
    for f in rep.features:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    bends = [f for f in rep.features if f.kind == "bend"]
    results.append(("bracket_b holes", counts.get("hole") == 3, f"got {counts.get('hole')}"))
    results.append(("bracket_b bend", counts.get("bend") == 1, f"got {counts.get('bend')}"))
    results.append(
        ("bracket_b bend radius", bends and abs(bends[0].params["radius_mm"] - 5.0) < 0.01,
         f"R={bends[0].params.get('radius_mm') if bends else None}")
    )
    results.append(("bracket_b all accept", rep.summary.to_fix == 0, f"to_fix={rep.summary.to_fix}"))

    # Fixture B2: one hole 4.0mm from edge (< 2t=5) -> exactly 1 violation.
    rep = evaluate("bracket_b2.step", 2.5, "steel")
    fixes = [f for f in rep.findings if f.verdict == "fix"]
    results.append(("bracket_b2 one violation", rep.summary.to_fix == 1, f"to_fix={rep.summary.to_fix}"))
    results.append(
        ("bracket_b2 violation rule",
         len(fixes) == 1 and fixes[0].rule_id == "hole_edge_min_dist",
         f"rules={[f.rule_id for f in fixes]}")
    )
    results.append(
        ("bracket_b2 violation values",
         len(fixes) == 1 and abs(fixes[0].actual - 4.0) < 0.05 and abs(fixes[0].required - 5.0) < 1e-9,
         f"actual={fixes[0].actual if fixes else None} required={fixes[0].required if fixes else None}")
    )

    # Fixture A2: plate t=3 -> 2 holes, 1 notch (8x6), 1 projection (12x10), all Accept.
    rep = evaluate("plate_a2.step", 3.0, "aluminum")
    counts = {}
    for f in rep.features:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    notches = [f for f in rep.features if f.kind == "notch"]
    tabs = [f for f in rep.features if f.kind == "projection"]
    results.append(("plate_a2 holes", counts.get("hole") == 2, f"got {counts.get('hole')}"))
    results.append(("plate_a2 notch", len(notches) == 1, f"got {len(notches)}"))
    results.append(
        ("plate_a2 notch width", notches and abs(notches[0].params["width_mm"] - 8.0) < 1.5,
         f"w={notches[0].params.get('width_mm') if notches else None}")
    )
    results.append(("plate_a2 projection", len(tabs) == 1, f"got {len(tabs)}"))
    results.append(
        ("plate_a2 projection width", tabs and abs(tabs[0].params["width_mm"] - 12.0) < 1.5,
         f"w={tabs[0].params.get('width_mm') if tabs else None}")
    )
    results.append(("plate_a2 all accept", rep.summary.to_fix == 0, f"to_fix={rep.summary.to_fix}"))

    # Fixture C: bracket t=2.5 -> 1 bend, 1 relief-cut (6x8), 1 notch; all Accept.
    rep = evaluate("bracket_c.step", 2.5, "steel")
    counts = {}
    for f in rep.features:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    reliefs = [f for f in rep.features if f.kind == "relief_cut"]
    results.append(("bracket_c bend", counts.get("bend") == 1, f"got {counts.get('bend')}"))
    results.append(("bracket_c relief_cut", len(reliefs) == 1, f"got {len(reliefs)}"))
    results.append(("bracket_c notch", counts.get("notch") == 1, f"got {counts.get('notch')}"))
    results.append(
        ("bracket_c relief dims",
         reliefs
         and abs(reliefs[0].params["width_mm"] - 6.0) < 1.5
         and abs(reliefs[0].params["length_mm"] - 8.0) < 1.5,
         f"{reliefs[0].params if reliefs else None}")
    )
    results.append(("bracket_c all accept", rep.summary.to_fix == 0, f"to_fix={rep.summary.to_fix}"))

    # Fixture D: plate t=2 -> 1 emboss, 1 drawing, 1 extruded hole.
    rep = evaluate("plate_d.step", 2.0, "steel")
    counts = {}
    for f in rep.features:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    results.append(("plate_d emboss", counts.get("emboss") == 1, f"got {counts.get('emboss')}"))
    results.append(("plate_d drawing", counts.get("drawing") == 1, f"got {counts.get('drawing')}"))
    results.append(
        ("plate_d extruded_hole", counts.get("extruded_hole") == 1,
         f"got {counts.get('extruded_hole')}")
    )

    # In-memory shape path (FreeCAD panel path): same result as file path.
    from stampkit.backends import get_kernel

    kernel = get_kernel()
    shape = kernel.import_step(os.path.join(fixtures, "bracket_b2.step"))
    rep2 = service.evaluate_shape(shape, thickness_mm=2.5, material="steel")
    results.append(
        ("evaluate_shape parity", rep2.summary.to_fix == 1, f"to_fix={rep2.summary.to_fix}")
    )

    failed = _failures(results)
    print(f"\n{len(results) - failed}/{len(results)} integration checks passed")
    return 1 if failed else 0


try:
    code = main()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    code = 2
sys.stdout.flush()
sys.exit(code)
