"""Analytic mechanics and regression checks shared with the trussx design model."""

import json

import matplotlib.pyplot as plt
import numpy as np
import pytest

import trussme as tm
from trussme.optimize import make_x0, make_bounds, make_inequality_constraints
from trussme.visualize import plot_truss
from tests.helpers import build_triangle_truss


def column(shape=None, gravity=(0, 0, 0)):
    truss = tm.Truss(gravity=gravity)
    a = truss.add_pinned_joint([0, 0, 0])
    b = truss.add_slotted_joint([2, 0, 0], "x")
    truss.add_member(a, b, shape=shape or tm.Square(w=0.006, h=0.012))
    truss.set_load(b, [-100, 0, 0])
    return truss


def test_directional_euler_capacity_orientation_and_bracing():
    truss = column()
    truss.set_member_buckling(0, tm.BucklingSettings(transverse_reference=(0, 0, 1)))
    truss.analyze()
    member = truss.members[0]
    first, second = member.buckling_modes
    assert member.force == pytest.approx(-100)
    assert first.direction == pytest.approx((0, 0, 1))
    assert second.direction == pytest.approx((0, -1, 0))
    assert first.moment_of_inertia == pytest.approx(8.64e-10)
    assert second.moment_of_inertia == pytest.approx(2.16e-10)
    expected = np.pi**2 * 200e9 * 2.16e-10 / 2**2
    assert member.governing_buckling.critical_load == pytest.approx(expected)
    assert member.fos_buckling == pytest.approx(expected / 100)
    truss.set_buckling_axis("strong")
    assert member.fos_buckling == pytest.approx(4 * expected / 100)
    assert tm.Goals().evaluate(truss)[0] == pytest.approx(100 / expected - 1)
    report = tm.report_to_str(
        truss, tm.Goals(minimum_fos_buckling=2), with_figures=False
    )
    assert "DIRECTIONAL BUCKLING" in report and "Critical load (N)" in report
    assert "buckling FOS was not satisfied" in report
    truss.set_member_buckling(0, tm.BucklingSettings((0, 0, 1), (1, 0.4)))
    truss.analyze()
    assert member.buckling_modes[1].critical_load == pytest.approx(expected / 0.4**2)
    assert member.governing_buckling.direction == pytest.approx((0, 0, 1))


@pytest.mark.parametrize("gravity", [(0, -9.80665, 0), (-10, 2, 3), (0, 0, 0)])
def test_self_weight_loads_reactions_and_axial_displacement(gravity):
    truss = column(gravity=gravity)
    truss.set_load(0, [10, -20, 30])
    truss.analyze()
    member = truss.members[0]
    expected_loads = (
        np.array([[10, -20, 30], [-100, 0, 0]]) + member.mass * np.array(gravity) / 2
    )
    assert truss.nodal_loads == pytest.approx(expected_loads)
    assert np.sum([j.reactions for j in truss.joints], axis=0) == pytest.approx(
        -expected_loads.sum(axis=0)
    )
    assert member.force == pytest.approx(expected_loads[1, 0])
    assert truss.joints[1].deflections[0] == pytest.approx(
        expected_loads[1, 0] * member.length / (member.elastic_modulus * member.area)
    )
    truss.analyze()  # No accumulated self-weight across repeated solves.
    assert truss.nodal_loads == pytest.approx(expected_loads)


def test_support_only_model_reacts_to_its_weight_and_external_load():
    truss = column(gravity=(0, -9.80665, 0))
    truss.joints[1].pinned()
    truss.set_load(1, [0, -100, 0])
    truss.analyze()
    assert sum(j.reactions[1] for j in truss.joints) == pytest.approx(
        100 + 9.80665 * truss.mass
    )


@pytest.mark.parametrize(
    "shape",
    [
        tm.Pipe(0.02, 0.002),
        tm.Bar(0.02),
        tm.Square(0.02, 0.04),
        tm.Box(0.02, 0.04, 0.002),
        tm.Custom(0.001, 2e-7, 1e-7),
    ],
)
def test_native_json_and_trs_preserve_all_design_assumptions(tmp_path, shape):
    truss = column(shape, gravity=(1, -2, 3))
    truss.set_load(1, [100, -100, 0])
    truss.set_buckling_axis("strong")
    truss.set_member_buckling(0, tm.BucklingSettings((0, 0, 1), (0.7, 1.5)))
    truss.analyze()
    path = tmp_path / "model.trs"
    truss.to_trs(str(path))
    for rebuilt in [tm.read_json(truss.to_json()), tm.read_trs(str(path))]:
        assert json.loads(rebuilt.to_json()) == json.loads(truss.to_json())
        rebuilt.analyze()
        assert rebuilt.members[0].buckling_modes == truss.members[0].buckling_modes
        assert rebuilt.nodal_loads == pytest.approx(truss.nodal_loads)
        assert rebuilt.members[0].force == pytest.approx(truss.members[0].force)


def test_cancelling_loads_are_fixed_during_joint_optimization():
    truss = build_triangle_truss()
    truss.set_load(1, [100, -100, 0])
    assert make_x0(truss, "full", None) == []
    assert make_bounds(truss, "full", None) == ([], [])
    generator = tm.make_truss_generator_function(truss, "full", None)
    assert generator([]).joints[1].loads == [100, -100, 0]


def test_mass_goal_and_box_wall_geometry_are_enforced():
    truss = column(tm.Box(0.02, 0.04, 0.002))
    truss.analyze()
    goals = tm.Goals(maximum_mass=truss.mass / 2)
    x0 = make_x0(truss, None, "full")
    constraints = make_inequality_constraints(truss, goals, None, "full")
    assert constraints(x0)[3] == pytest.approx(1)
    assert constraints(x0)[2] == -1  # Unlimited deflection has no hidden cap.
    invalid = [0.02, 0.04, 0.015]
    values = constraints(invalid)
    assert values[4] == pytest.approx(0.01)
    assert all(v > 0 for v in values[:4])
    assert np.isfinite(values).all()
    with pytest.raises(ValueError, match="thickness"):
        tm.make_truss_generator_function(truss, None, "full")(invalid).analyze()
    zero = constraints([0, 0, 0])
    assert len(zero) == len(values) and all(v > 0 for v in zero[:4])


def test_generator_owns_snapshot_and_validates_vector():
    truss = column()
    generator = tm.make_truss_generator_function(truss, None, "full")
    truss.set_gravity([1, 2, 3])
    truss.set_load(1, [-999, 0, 0])
    rebuilt = generator([0.006, 0.012])
    assert rebuilt.gravity == (0, 0, 0)
    assert rebuilt.joints[1].loads == [-100, 0, 0]
    for x in [[], [0.006, 0.012, 1], [np.nan, 0.012]]:
        with pytest.raises(ValueError, match="Design vector"):
            generator(x)
    with pytest.raises(ValueError, match="Custom"):
        make_x0(column(tm.Custom(0.001, 2e-7, 1e-7)), None, "full")
    with pytest.raises(ValueError, match="mode"):
        make_bounds(truss, "invalid", None)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"effective_length_factors": (0, 1)},
        {"effective_length_factors": (1, np.inf)},
        {"transverse_reference": (0, 0, 0)},
        {"transverse_reference": (0, np.nan, 1)},
    ],
)
def test_invalid_buckling_settings_rejected(kwargs):
    with pytest.raises(ValueError):
        tm.BucklingSettings(**kwargs)


def test_parallel_reference_rejected_without_changing_member():
    truss = column()
    original = truss.members[0].buckling
    with pytest.raises(ValueError, match="parallel"):
        truss.set_member_buckling(0, tm.BucklingSettings((1, 0, 0)))
    assert truss.members[0].buckling == original


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["trussx"].update(gravity=[0, np.inf, 0]),
        lambda d: d["trussx"].update(member_buckling=[]),
        lambda d: d["trussx"].update(buckling_axis="invalid"),
        lambda d: d["trussx"].update(unknown=True),
    ],
)
def test_invalid_metadata_is_rejected(change):
    data = json.loads(column().to_json())
    change(data)
    with pytest.raises(ValueError):
        tm.read_json(json.dumps(data))


@pytest.mark.parametrize(
    "field,value",
    [
        ("minimum_fos_buckling", np.nan),
        ("minimum_fos_yielding", -1),
        ("maximum_mass", -1),
        ("maximum_deflection", np.nan),
    ],
)
def test_invalid_goals_are_rejected(field, value):
    with pytest.raises(ValueError):
        tm.Goals(**{field: value}).validate()


@pytest.mark.parametrize(
    "shape",
    [
        tm.Pipe(0.01, 0.02),
        tm.Bar(-1),
        tm.Box(0.02, 0.04, 0.015),
        tm.Square(0, 0.01),
        tm.Custom(1, -1, 1),
    ],
)
def test_invalid_sections_cannot_be_analyzed(shape):
    with pytest.raises(ValueError):
        column(shape).analyze()


def test_projection_and_governing_direction_markers():
    truss = column()
    truss.set_member_buckling(0, tm.BucklingSettings((0, 0, 1)))
    truss.analyze()
    for projection in ["xy", "xz", "yz"]:
        fig = plot_truss(
            truss,
            projection=projection,
            buckling_directions=True,
            deflected_shape="force",
        )
        assert projection.upper() in fig.axes[0].get_title()
        assert fig.axes[0].texts or len(fig.axes[0].lines) == 3
        plt.close(fig)
    with pytest.raises(ValueError, match="Projection"):
        plot_truss(truss, projection="bad")


def test_exact_goal_boundary_is_feasible_in_constraints_and_report():
    truss = column()
    truss.analyze()
    goals = tm.Goals(
        truss.fos_buckling_governing, truss.fos_yielding, truss.mass, truss.deflection
    )
    assert goals.evaluate(truss) == pytest.approx([0, 0, 0, 0])
    report = tm.report_to_str(truss, goals, with_figures=False)
    assert "were not satisfied" not in report and "was not satisfied" not in report


def test_legacy_shape_parameters_need_not_all_be_lengths():
    class RotatedSection(tm.Shape):
        def __init__(self):
            self._params = {"angle": 0.0}

        def name(self):
            return "rotated section"

        def area(self):
            return 0.001

        def moi(self):
            return 1e-7

    truss = column(RotatedSection())
    truss.analyze()
    first, second = truss.members[0].buckling_modes
    assert first.critical_load == second.critical_load
