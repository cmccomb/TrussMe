import doctest

import pytest

import trussme
import trussme.components
import trussme.report
import trussme.truss

from tests.helpers import TEST_TRUSS_FILENAME, build_reference_truss, default_goals


@pytest.mark.parametrize(
    "module",
    [trussme, trussme.truss, trussme.components, trussme.report],
)
def test_doctests(module) -> None:
    failed, _ = doctest.testmod(module, optionflags=doctest.ELLIPSIS)
    assert failed == 0


def test_build_methods() -> None:
    goals = default_goals()
    truss_from_commands = build_reference_truss()
    truss_from_file = trussme.read_trs(str(TEST_TRUSS_FILENAME))

    assert trussme.report_to_str(
        truss_from_file,
        goals,
        with_figures=False,
    ) == trussme.report_to_str(
        truss_from_commands,
        goals,
        with_figures=False,
    )


def test_save_to_trs_and_rebuild(tmp_path) -> None:
    goals = default_goals()
    truss_from_file = trussme.read_trs(str(TEST_TRUSS_FILENAME))
    output_path = tmp_path / "saved.trs"

    truss_from_file.to_trs(str(output_path))
    truss_rebuilt_from_file = trussme.read_trs(str(output_path))

    assert trussme.report_to_str(
        truss_from_file,
        goals,
        with_figures=False,
    ) == trussme.report_to_str(
        truss_rebuilt_from_file,
        goals,
        with_figures=False,
    )


def test_save_to_json_and_rebuild(tmp_path) -> None:
    goals = default_goals()
    truss_from_file = trussme.read_trs(str(TEST_TRUSS_FILENAME))
    output_path = tmp_path / "saved.json"

    truss_from_file.to_json(str(output_path))
    truss_rebuilt_from_file = trussme.read_json(str(output_path))

    assert trussme.report_to_str(
        truss_from_file,
        goals,
        with_figures=False,
    ) == trussme.report_to_str(
        truss_rebuilt_from_file,
        goals,
        with_figures=False,
    )
