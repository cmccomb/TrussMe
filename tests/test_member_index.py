"""Tests for member addition functions."""

import trussme
import pytest


def test_add_member_returns_index() -> None:
    """Ensure ``add_member`` returns the new member index."""
    # Arrange
    truss = trussme.Truss()
    start = truss.add_free_joint([0.0, 0.0, 0.0])
    end = truss.add_free_joint([1.0, 0.0, 0.0])

    # Act
    idx = truss.add_member(start, end)

    # Assert
    assert idx == 0


def test_add_member_invalid_index() -> None:
    """``add_member`` should raise when given an invalid joint index."""
    # Arrange
    truss = trussme.Truss()
    valid = truss.add_free_joint([0.0, 0.0, 0.0])
    _ = truss.add_free_joint([1.0, 0.0, 0.0])

    # Act / Assert
    with pytest.raises(IndexError):
        truss.add_member(5, valid)


def test_add_member_identical_indices() -> None:
    """``add_member`` rejects using the same joint for both ends."""
    # Arrange
    truss = trussme.Truss()
    joint = truss.add_free_joint([0.0, 0.0, 0.0])

    # Act / Assert
    with pytest.raises(ValueError):
        truss.add_member(joint, joint)
