import json
from types import SimpleNamespace

import pytest

import trussme

from tests.helpers import build_triangle_truss, default_goals


@pytest.mark.parametrize(
    ("restriction", "expected"),
    [
        ([True, False, False], "x"),
        ([False, True, False], "y"),
        ([False, False, True], "z"),
        ([False, False, False], "none"),
    ],
)
def test_is_planar_reports_expected_axis(restriction, expected) -> None:
    truss = trussme.Truss()
    truss.add_free_joint([0.0, 0.0, 0.0])
    truss.add_free_joint([1.0, 0.0, 0.0])
    for joint in truss.joints:
        joint.translation_restricted = list(restriction)

    assert truss.is_planar() == expected


@pytest.mark.parametrize(
    ("buckling", "yielding", "expected"),
    [
        (0.9, 1.1, "buckling"),
        (1.2, 0.8, "yielding"),
    ],
)
def test_limit_state_reports_smallest_factor_of_safety(
    buckling, yielding, expected
) -> None:
    truss = trussme.Truss()
    truss.members = [SimpleNamespace(fos_buckling=buckling, fos_yielding=yielding)]

    assert truss.limit_state == expected


def test_read_trs_parses_custom_file(tmp_path) -> None:
    input_path = tmp_path / "custom.trs"
    input_path.write_text(
        "\n".join(
            [
                "# Custom truss",
                "S\tA36_Steel\t7850.0\t200000000000.0\t250000000.0\thttps://example.com/material",
                "",
                "J\t0.0\t0.0\t0.0\t1\t1\t1",
                "J\t1.0\t0.0\t0.0\t0\t1\t1",
                "M\t0\t1\tA36_Steel\tbar\tr=0.02",
                "L\t1\t10.0\t-20.0\t0.0",
            ]
        )
    )

    truss = trussme.read_trs(str(input_path))

    assert truss.number_of_joints == 2
    assert truss.number_of_members == 1
    assert truss.members[0].material["source"] == "https://example.com/material"
    assert truss.joints[1].loads == [10.0, -20.0, 0.0]


def test_read_trs_invalid_line_raises_value_error(tmp_path) -> None:
    input_path = tmp_path / "invalid.trs"
    input_path.write_text("X\tbad\n")

    with pytest.raises(ValueError, match="not a valid line initializer"):
        trussme.read_trs(str(input_path))


def test_read_json_accepts_inline_json_string() -> None:
    truss = build_triangle_truss()
    json_blob = truss.to_json()
    rebuilt = trussme.read_json(json_blob)

    assert trussme.report_to_str(
        rebuilt,
        default_goals(),
        with_figures=False,
    ) == trussme.report_to_str(truss, default_goals(), with_figures=False)


def test_read_json_rejects_custom_shape_in_json() -> None:
    json_blob = json.dumps(
        {
            "materials": [
                {
                    "name": "A36_Steel",
                    "density": 7850.0,
                    "elastic_modulus": 200000000000.0,
                    "yield_strength": 250000000.0,
                    "source": "https://example.com/material",
                }
            ],
            "joints": [
                {
                    "coordinates": [0.0, 0.0, 0.0],
                    "loads": [0.0, 0.0, 0.0],
                    "translation": [True, True, True],
                },
                {
                    "coordinates": [1.0, 0.0, 0.0],
                    "loads": [0.0, 0.0, 0.0],
                    "translation": [False, True, True],
                },
            ],
            "members": [
                {
                    "begin_joint": 0,
                    "end_joint": 1,
                    "material": "A36_Steel",
                    "shape": {
                        "name": "custom-shape",
                        "parameters": [["size", 1.0]],
                    },
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="custom type and not supported"):
        trussme.read_json(json_blob)
