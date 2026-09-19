"""Frozen trussx 0.3 directional examples and historical TrussMe 0.1 evidence."""

from pathlib import Path
import json

import numpy as np
import pytest
import trussme as tm

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "expected",
    json.loads((FIXTURES / "trussx-results.json").read_text()),
    ids=lambda x: x["stage"],
)
def test_rust_directional_example_has_same_python_result(expected):
    truss = tm.read_json(str(FIXTURES / f"trussx-{expected['stage']}.json"))
    truss.analyze()
    mode = truss.members[0].governing_buckling
    assert truss.mass == pytest.approx(expected["mass_kg"])
    assert truss.fos_buckling_governing == pytest.approx(expected["buckling_fos"])
    assert mode.critical_load == pytest.approx(expected["critical_load_n"])
    assert mode.direction == pytest.approx(expected["direction"])
    assert bool(all(v <= 0 for v in tm.Goals().evaluate(truss))) == expected["feasible"]


@pytest.mark.parametrize(
    "case",
    json.loads((FIXTURES / "legacy-parity.json").read_text())["cases"],
    ids=lambda x: x["name"],
)
def test_pinned_legacy_models_retain_equilibrium_and_explicit_scalar_compatibility(
    case,
):
    truss = tm.read_json(json.dumps(case["model"]))
    truss.set_buckling_axis("strong")
    truss.analyze()
    expected = case["expected"]
    for key in ["mass", "deflection", "fos_yielding", "fos_buckling"]:
        assert getattr(truss, key) == pytest.approx(expected[key], rel=1e-9, abs=1e-8)
    assert np.array([j.deflections for j in truss.joints]) == pytest.approx(
        np.array(expected["joint_displacements"]), abs=1e-8
    )
    assert np.array([j.reactions for j in truss.joints]) == pytest.approx(
        np.array(expected["physical_reactions"]), abs=1e-8
    )
    assert [m.force for m in truss.members] == pytest.approx(
        expected["member_forces"], abs=1e-8
    )
    for member, buckling in zip(truss.members, expected["member_buckling"]):
        assert member.fos_buckling == pytest.approx(
            np.inf if buckling is None else buckling
        )
