from typing import TypedDict

import numpy
from numpy.typing import NDArray


TrussInfo = TypedDict("TrussInfo", {
    "coordinates": numpy.ndarray,
    "connections": numpy.ndarray,
    "loads": numpy.ndarray,
    "reactions": numpy.ndarray,
    "area": float,
    "elastic_modulus": float
})


def the_forces(truss_info: TrussInfo) -> tuple[NDArray[float], NDArray[float], NDArray[float], float]:
    tj: numpy.ndarray = numpy.zeros([3, numpy.size(truss_info["connections"], axis=1)])
    w: numpy.ndarray = numpy.array(
        [numpy.size(truss_info["reactions"], axis=0), numpy.size(truss_info["reactions"], axis=1)])
    dof: numpy.ndarray = numpy.zeros([3 * w[1], 3 * w[1]])
    deflections: numpy.ndarray = numpy.ones(w)
    deflections -= truss_info["reactions"]

    # This identifies joints that can be loaded
    ff: numpy.ndarray = numpy.where(deflections.T.flat == 1)[0]

    # Build the global stiffness matrix
    for i in range(numpy.size(truss_info["connections"], axis=1)):
        ends = truss_info["connections"][:, i]
        length_vector = truss_info["coordinates"][:, ends[1]] - truss_info["coordinates"][:, ends[0]]
        length = numpy.linalg.norm(length_vector)
        direction = length_vector / length
        d2 = numpy.outer(direction, direction)
        ea_over_l = truss_info["elastic_modulus"][i] * truss_info["area"][i] / length
        ss = ea_over_l * numpy.concatenate((numpy.concatenate((d2, -d2), axis=1), numpy.concatenate((-d2, d2), axis=1)),
                                           axis=0)
        tj[:, i] = ea_over_l * direction
        e = list(range((3 * ends[0]), (3 * ends[0] + 3))) + list(range((3 * ends[1]), (3 * ends[1] + 3)))
        for ii in range(6):
            for j in range(6):
                dof[e[ii], e[j]] += ss[ii, j]

    SSff = numpy.zeros([len(ff), len(ff)])
    for i in range(len(ff)):
        for j in range(len(ff)):
            SSff[i, j] = dof[ff[i], ff[j]]

    flat_loads = truss_info["loads"].T.flat[ff]
    flat_deflections = numpy.linalg.solve(SSff, flat_loads)

    ff = numpy.where(deflections.T == 1)
    for i in range(len(ff[0])):
        deflections[ff[1][i], ff[0][i]] = flat_deflections[i]
    forces = numpy.sum(numpy.multiply(tj,
        deflections[:, truss_info["connections"][1, :]] - deflections[:, truss_info["connections"][0, :]]), axis=0)

    # Check the condition number, and warn the user if it is out of range
    cond = numpy.linalg.cond(SSff)

    # Compute the reactions
    reactions = numpy.sum(dof * deflections.T.flat[:], axis=1).reshape([w[1], w[0]]).T

    return forces, deflections, reactions, cond
