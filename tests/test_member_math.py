import warnings

import numpy
import pytest

import trussme

from tests.helpers import build_triangle_truss


def test_member_safety_factors_handle_zero_force_without_runtime_warnings() -> None:
    truss = build_triangle_truss()
    member = truss.members[0]

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        yielding = member.fos_yielding
        buckling = member.fos_buckling

    runtime_warnings = [
        warning for warning in captured if issubclass(warning.category, RuntimeWarning)
    ]

    assert numpy.isinf(yielding)
    assert numpy.isinf(buckling)
    assert not runtime_warnings


def test_zero_length_member_direction_returns_zero_vector() -> None:
    truss = trussme.Truss()
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_member(0, 1)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        direction = truss.members[0].direction

    runtime_warnings = [
        warning for warning in captured if issubclass(warning.category, RuntimeWarning)
    ]

    assert numpy.allclose(direction, numpy.zeros(3))
    assert not runtime_warnings


def test_zero_length_member_stiffness_raises_value_error() -> None:
    truss = trussme.Truss()
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_member(0, 1)

    with pytest.raises(ValueError, match="length must be greater than zero"):
        _ = truss.members[0].stiffness
