import numpy
import pytest
import scipy.optimize

import trussme
import trussme.optimize as optimize

from tests.helpers import build_optimization_truss, build_triangle_truss


def build_non_planar_joint_truss() -> trussme.Truss:
    truss = trussme.Truss()
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_free_joint([1.0, 2.0, 3.0])
    return truss


@pytest.mark.parametrize(
    ("joint_optimization", "member_optimization", "expected_length"),
    [
        (None, None, 0),
        ("full", None, 16),
        (None, "scaled", 19),
        (None, "full", 38),
        ("full", "full", 54),
    ],
)
def test_make_x0_respects_requested_modes(
    joint_optimization, member_optimization, expected_length
) -> None:
    truss = build_optimization_truss()

    x0 = optimize.make_x0(
        truss,
        joint_optimization=joint_optimization,
        member_optimization=member_optimization,
    )

    assert len(x0) == expected_length


@pytest.mark.parametrize(
    ("joint_optimization", "member_optimization", "expected_length"),
    [
        (None, None, 0),
        ("full", None, 16),
        (None, "scaled", 19),
        (None, "full", 38),
        ("full", "full", 54),
    ],
)
def test_make_bounds_respects_requested_modes(
    joint_optimization, member_optimization, expected_length
) -> None:
    truss = build_optimization_truss()

    lower_bounds, upper_bounds = optimize.make_bounds(
        truss,
        joint_optimization=joint_optimization,
        member_optimization=member_optimization,
    )

    assert len(lower_bounds) == expected_length
    assert len(upper_bounds) == expected_length


def test_make_optimization_functions_round_trip_matches_original() -> None:
    truss = build_optimization_truss()
    goals = trussme.Goals()

    x0, _, _, generator, _ = trussme.make_optimization_functions(truss, goals)

    assert trussme.report_to_str(
        generator(x0),
        goals,
        with_figures=False,
    ) == trussme.report_to_str(
        truss,
        goals,
        with_figures=False,
    )


def test_make_optimization_functions_returns_expected_shapes() -> None:
    truss = build_optimization_truss()
    goals = trussme.Goals()

    x0, objective, constraints, generator, bounds = trussme.make_optimization_functions(
        truss, goals
    )

    assert x0
    assert callable(objective)
    assert callable(constraints)
    assert callable(generator)
    assert len(bounds) == 2
    assert len(bounds[0]) == len(bounds[1]) == len(x0)
    assert objective(x0) == pytest.approx(generator(x0).mass)


def test_joint_optimization_non_planar_includes_z_coordinates() -> None:
    truss = build_non_planar_joint_truss()

    x0 = optimize.make_x0(
        truss,
        joint_optimization="full",
        member_optimization=None,
    )
    lower_bounds, upper_bounds = optimize.make_bounds(
        truss,
        joint_optimization="full",
        member_optimization=None,
    )
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization="full",
        member_optimization=None,
    )

    assert x0 == [0.0, 0.0, 0.0, 1.0, 2.0, 3.0]
    assert lower_bounds == [-numpy.inf] * 6
    assert upper_bounds == [numpy.inf] * 6

    updated = list(x0)
    updated[2] = 5.0
    generated = generator(updated)

    assert generated.joints[0].coordinates[2] == pytest.approx(5.0)


@pytest.mark.parametrize(
    ("shape_factory", "scaled_length", "full_length", "scaled_prefix", "full_prefix"),
    [
        (
            lambda: trussme.Box(w=0.02, h=0.03, t=0.002),
            3,
            9,
            [0.02],
            [0.02, 0.03, 0.002],
        ),
        (
            lambda: trussme.Bar(r=0.02),
            3,
            3,
            [0.02],
            [0.02],
        ),
        (
            lambda: trussme.Square(w=0.02, h=0.03),
            3,
            6,
            [0.02],
            [0.02, 0.03],
        ),
    ],
)
def test_make_x0_covers_non_pipe_shapes(
    shape_factory,
    scaled_length,
    full_length,
    scaled_prefix,
    full_prefix,
) -> None:
    truss = build_triangle_truss(shape=shape_factory)

    scaled = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    full = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )

    assert len(scaled) == scaled_length
    assert len(full) == full_length
    assert scaled[: len(scaled_prefix)] == scaled_prefix
    assert full[: len(full_prefix)] == full_prefix


@pytest.mark.parametrize(
    ("shape_factory", "scaled_length", "full_length"),
    [
        (lambda: trussme.Box(w=0.02, h=0.03, t=0.002), 3, 9),
        (lambda: trussme.Bar(r=0.02), 3, 3),
        (lambda: trussme.Square(w=0.02, h=0.03), 3, 6),
    ],
)
def test_make_bounds_covers_non_pipe_shapes(
    shape_factory,
    scaled_length,
    full_length,
) -> None:
    truss = build_triangle_truss(shape=shape_factory)

    scaled_lb, scaled_ub = optimize.make_bounds(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    full_lb, full_ub = optimize.make_bounds(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )

    assert len(scaled_lb) == len(scaled_ub) == scaled_length
    assert len(full_lb) == len(full_ub) == full_length
    assert all(value == 0.0 for value in scaled_lb + full_lb)
    assert all(numpy.isinf(value) for value in scaled_ub + full_ub)


def test_make_truss_generator_function_scaled_updates_shapes() -> None:
    truss = build_optimization_truss()
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0[0] = 0.03

    generated = generator(x0)

    assert generated.members[0].shape._params["r"] == pytest.approx(0.03)
    assert generated.members[0].shape._params["t"] == pytest.approx(0.003)


@pytest.mark.parametrize(
    ("shape_factory", "replacement", "expected"),
    [
        (
            lambda: trussme.Box(w=0.02, h=0.03, t=0.002),
            0.04,
            {"w": 0.04, "h": 0.06, "t": 0.004},
        ),
        (
            lambda: trussme.Bar(r=0.02),
            0.04,
            {"r": 0.04},
        ),
        (
            lambda: trussme.Square(w=0.02, h=0.03),
            0.04,
            {"w": 0.04, "h": 0.06},
        ),
    ],
)
def test_make_truss_generator_function_scaled_updates_other_shapes(
    shape_factory,
    replacement,
    expected,
) -> None:
    truss = build_triangle_truss(shape=shape_factory)
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0[0] = replacement

    generated = generator(x0)

    for key, value in expected.items():
        assert generated.members[0].shape._params[key] == pytest.approx(value)


@pytest.mark.parametrize(
    ("shape_factory", "expected"),
    [
        (
            lambda: trussme.Pipe(r=0.0, t=0.0),
            {"r": 0.04, "t": 0.0},
        ),
        (
            lambda: trussme.Box(w=0.0, h=0.0, t=0.0),
            {"w": 0.04, "h": 0.0, "t": 0.0},
        ),
        (
            lambda: trussme.Square(w=0.0, h=0.0),
            {"w": 0.04, "h": 0.0},
        ),
    ],
)
def test_make_truss_generator_function_scaled_handles_zero_reference_dimensions(
    shape_factory,
    expected,
) -> None:
    truss = build_triangle_truss(shape=shape_factory)
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="scaled",
    )
    x0[0] = 0.04

    generated = generator(x0)

    for key, value in expected.items():
        assert generated.members[0].shape._params[key] == pytest.approx(value)


def test_make_truss_generator_function_full_updates_shapes() -> None:
    truss = build_optimization_truss()
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    x0[0] = 0.03
    x0[1] = 0.004

    generated = generator(x0)

    assert generated.members[0].shape._params["r"] == pytest.approx(0.03)
    assert generated.members[0].shape._params["t"] == pytest.approx(0.004)


@pytest.mark.parametrize(
    ("shape_factory", "replacement", "expected"),
    [
        (
            lambda: trussme.Box(w=0.02, h=0.03, t=0.002),
            [0.04, 0.05, 0.006],
            {"w": 0.04, "h": 0.05, "t": 0.006},
        ),
        (
            lambda: trussme.Bar(r=0.02),
            [0.04],
            {"r": 0.04},
        ),
        (
            lambda: trussme.Square(w=0.02, h=0.03),
            [0.04, 0.05],
            {"w": 0.04, "h": 0.05},
        ),
    ],
)
def test_make_truss_generator_function_full_updates_other_shapes(
    shape_factory,
    replacement,
    expected,
) -> None:
    truss = build_triangle_truss(shape=shape_factory)
    generator = trussme.make_truss_generator_function(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    x0[: len(replacement)] = replacement

    generated = generator(x0)

    for key, value in expected.items():
        assert generated.members[0].shape._params[key] == pytest.approx(value)


def test_make_inequality_constraints_full_pipe_adds_geometry_constraints() -> None:
    truss = build_optimization_truss()
    goals = trussme.Goals()
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    constraints = optimize.make_inequality_constraints(
        truss,
        goals,
        joint_optimization=None,
        member_optimization="full",
    )

    values = constraints(x0)

    assert len(values) == 22


def test_make_inequality_constraints_full_box_adds_geometry_constraints() -> None:
    truss = build_triangle_truss(shape=lambda: trussme.Box(w=0.02, h=0.03, t=0.002))
    goals = trussme.Goals()
    x0 = optimize.make_x0(
        truss,
        joint_optimization=None,
        member_optimization="full",
    )
    constraints = optimize.make_inequality_constraints(
        truss,
        goals,
        joint_optimization=None,
        member_optimization="full",
    )

    values = constraints(x0)

    assert len(values) == 9


@pytest.mark.slow
def test_joint_optimization_smoke(tmp_path) -> None:
    truss = build_optimization_truss()
    goals = trussme.Goals()
    x0, objective, constraints, generator, _ = trussme.make_optimization_functions(
        truss,
        goals,
        joint_optimization="full",
        member_optimization=None,
    )

    result = scipy.optimize.minimize(
        objective,
        x0,
        constraints=[
            scipy.optimize.NonlinearConstraint(
                constraints, -numpy.inf, 0.0, keep_feasible=True
            )
        ],
        method="trust-constr",
        options={"maxiter": 5},
    )

    result_truss = generator(result.x)
    result_truss.analyze()
    output_path = tmp_path / "joint_optim.md"
    trussme.report_to_md(str(output_path), result_truss, goals)

    assert output_path.exists()
    assert result.x.shape[0] == len(x0)
