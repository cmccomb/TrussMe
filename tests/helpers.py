from pathlib import Path

import trussme


TEST_TRUSS_FILENAME = Path(__file__).with_name("example.trs")


def default_goals() -> trussme.Goals:
    return trussme.Goals(
        minimum_fos_buckling=1.5,
        minimum_fos_yielding=1.5,
        maximum_mass=5.0,
        maximum_deflection=6e-3,
    )


def build_reference_truss() -> trussme.Truss:
    truss = trussme.Truss()
    truss.add_pinned_joint([0.0, 0.0, 0.0])
    truss.add_free_joint([1.0, 0.0, 0.0])
    truss.add_free_joint([2.0, 0.0, 0.0])
    truss.add_free_joint([3.0, 0.0, 0.0])
    truss.add_free_joint([4.0, 0.0, 0.0])
    truss.add_pinned_joint([5.0, 0.0, 0.0])

    truss.add_free_joint([0.5, 1.0, 0.0])
    truss.add_free_joint([1.5, 1.0, 0.0])
    truss.add_free_joint([2.5, 1.0, 0.0])
    truss.add_free_joint([3.5, 1.0, 0.0])
    truss.add_free_joint([4.5, 1.0, 0.0])

    truss.add_out_of_plane_support("z")

    truss.joints[7].loads[1] = -20000
    truss.joints[8].loads[1] = -20000
    truss.joints[9].loads[1] = -20000

    for start, end in (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (6, 7),
        (7, 8),
        (8, 9),
        (9, 10),
        (0, 6),
        (6, 1),
        (1, 7),
        (7, 2),
        (2, 8),
        (8, 3),
        (3, 9),
        (9, 4),
        (4, 10),
        (10, 5),
    ):
        truss.add_member(start, end)

    return truss


def build_optimization_truss() -> trussme.Truss:
    truss = build_reference_truss()
    truss.joints[7].loads[1] = 0.0
    truss.joints[9].loads[1] = 0.0
    return truss


def build_triangle_truss(shape=None) -> trussme.Truss:
    truss = trussme.Truss()
    pin = truss.add_pinned_joint([0.0, 0.0, 0.0])
    free = truss.add_free_joint([2.5, 2.5, 0.0])
    roller = truss.add_roller_joint([5.0, 0.0, 0.0])

    truss.add_out_of_plane_support("z")
    truss.set_load(free, [0.0, -10000.0, 0.0])

    for start, end in ((pin, free), (pin, roller), (roller, free)):
        if shape is None:
            truss.add_member(start, end)
        else:
            truss.add_member(start, end, shape=shape())

    return truss
