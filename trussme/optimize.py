from typing import Callable

import numpy

from trussme import Truss, Goals, read_json, Pipe, Box, Square, Bar


def make_x0(
    truss: Truss,
    joint_coordinates: bool = True,
    shape_parameters: bool = True,
) -> list[float]:
    """
    Returns a vector that encodes the current truss design

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_coordinates: bool, default=True
        Whether to include joint location parameters.
    shape_parameters: bool, default=True
        Whether to include shape parameters.

    Returns
    -------
    list[float]
        A starting vector that encodes the current truss design
    """

    planar_direction: str = truss.is_planar()
    x0: list[float] = []

    configured_truss = read_json(truss.to_json())

    if joint_coordinates:
        for i in range(len(configured_truss.joints)):
            if (
                numpy.sum(configured_truss.joints[i].translation_restricted)
                == (0 if planar_direction == "none" else 1)
                and numpy.sum(configured_truss.joints[i].loads) == 0
            ):
                if planar_direction != "x":
                    x0.append(configured_truss.joints[i].coordinates[0])
                if planar_direction != "y":
                    x0.append(configured_truss.joints[i].coordinates[1])
                if planar_direction != "z":
                    x0.append(configured_truss.joints[i].coordinates[2])

    if shape_parameters:
        for i in range(len(configured_truss.members)):
            shape_name: str = configured_truss.members[i].shape.name()
            if shape_name == "pipe":
                x0.append(configured_truss.members[i].shape._params["r"])
            elif shape_name == "box":
                x0.append(configured_truss.members[i].shape._params["w"])
            elif shape_name == "bar":
                x0.append(configured_truss.members[i].shape._params["r"])
            elif shape_name == "square":
                x0.append(configured_truss.members[i].shape._params["w"])

    return x0


def make_bounds(
    truss: Truss,
    joint_coordinates: bool = True,
    shape_parameters: bool = True,
) -> tuple[list[float], list[float]]:
    """
    Returns a vector that encodes the current truss design

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_coordinates: bool, default=True
        Whether to include joint location parameters.
    shape_parameters: bool, default=True
        Whether to include shape parameters.

    Returns
    -------
    list[float]
        A starting vector that encodes the current truss design
    """

    planar_direction: str = truss.is_planar()
    lb: list[float] = []
    ub: list[float] = []

    configured_truss = read_json(truss.to_json())

    if joint_coordinates:
        for i in range(len(configured_truss.joints)):
            if (
                numpy.sum(configured_truss.joints[i].translation_restricted)
                == (0 if planar_direction == "none" else 1)
                and numpy.sum(configured_truss.joints[i].loads) == 0
            ):
                if planar_direction != "x":
                    lb.append(-numpy.inf)
                    ub.append(numpy.inf)
                if planar_direction != "y":
                    lb.append(-numpy.inf)
                    ub.append(numpy.inf)
                if planar_direction != "z":
                    lb.append(-numpy.inf)
                    ub.append(numpy.inf)

    if shape_parameters:
        for i in range(len(configured_truss.members)):
            shape_name: str = configured_truss.members[i].shape.name()
            if shape_name == "pipe":
                lb.append(0.0)
                ub.append(numpy.inf)
            elif shape_name == "box":
                lb.append(0.0)
                ub.append(numpy.inf)
            elif shape_name == "bar":
                lb.append(0.0)
                ub.append(numpy.inf)
            elif shape_name == "square":
                lb.append(0.0)
                ub.append(numpy.inf)

    return lb, ub


def make_truss_generator_function(
    truss: Truss,
    joint_coordinates: bool = True,
    shape_parameters: bool = True,
) -> Callable[[list[float]], Truss]:
    """
    Returns a function that takes a list of floats and returns a truss.

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_coordinates: bool, default=True
        Whether to include joint location parameters.
    shape_parameters: bool, default=True
        Whether to include shape parameters.

    Returns
    -------
    Callable[[list[float]]
        A tuple containing a vector that describes the input truss and a function that takes a list of floats and returns a truss.
    """

    planar_direction: str = truss.is_planar()

    def truss_generator(x: list[float]) -> Truss:
        configured_truss = read_json(truss.to_json())
        idx = 0

        if joint_coordinates:
            for i in range(len(configured_truss.joints)):
                if (
                    numpy.sum(configured_truss.joints[i].translation_restricted)
                    == (0 if planar_direction == "none" else 1)
                    and numpy.sum(configured_truss.joints[i].loads) == 0
                ):
                    if planar_direction != "x":
                        configured_truss.joints[i].coordinates[0] = x[idx]
                        idx += 1
                    if planar_direction != "y":
                        configured_truss.joints[i].coordinates[1] = x[idx]
                        idx += 1
                    if planar_direction != "z":
                        configured_truss.joints[i].coordinates[2] = x[idx]
                        idx += 1

        if shape_parameters:
            for i in range(len(configured_truss.members)):
                shape_name: str = configured_truss.members[i].shape.name()
                p = configured_truss.members[i].shape._params
                if shape_name == "pipe":
                    configured_truss.members[i].shape = Pipe(
                        r=x[idx], t=x[idx] * p["t"] / p["r"]
                    )
                    idx += 1
                elif shape_name == "box":
                    configured_truss.members[i].shape = Box(
                        w=x[idx], h=x[idx] * p["h"] / p["w"], t=x[idx] * p["t"] / p["w"]
                    )
                    idx += 1
                elif shape_name == "bar":
                    configured_truss.members[i].shape = Bar(r=x[idx])
                    idx += 1
                elif shape_name == "square":
                    configured_truss.members[i].shape = Square(
                        w=x[idx], h=x[idx] * p["h"] / p["w"]
                    )
                    idx += 1

        return configured_truss

    return truss_generator


def make_optimization_functions(
    truss: Truss,
    goals: Goals,
    joint_coordinates: bool = True,
    shape_parameters: bool = True,
) -> tuple[
    list[float],
    Callable[[list[float]], float],
    Callable[[list[float]], list[float]],
    Callable[[list[float]], Truss],
    tuple[list[float], list[float]],
]:
    """
    Creates functions for use in optimization, including a starting vector, objective function, a constraint function, and a truss generator function.

    Parameters
    ----------
    truss: Truss
        The truss to use as a starting configuration
    goals: Goals
        The goals to use for optimization
    joint_coordinates: bool, default=True
        Whether to include joint location parameters.
    shape_parameters: bool, default=True
        Whether to include shape parameters.

    Returns
    -------
    tuple[
        list[float],
        Callable[[list[float]], float],
        Callable[[list[float]], list[float]],
        Callable[[list[float]], Truss],
    ]
        A tuple containing the starting vector, objective function, constraint function, and truss generator function.
        :param goals:
    """

    x0 = make_x0(truss, joint_coordinates, shape_parameters)

    truss_generator = make_truss_generator_function(
        truss, joint_coordinates, shape_parameters
    )

    def objective_function(x: list[float]) -> float:
        truss = truss_generator(x)
        return truss.mass

    def inequality_constraints(x: list[float]) -> list[float]:
        truss = truss_generator(x)
        truss.analyze()
        return [
            goals.minimum_fos_buckling - truss.fos_buckling,
            goals.minimum_fos_yielding - truss.fos_yielding,
            truss.deflection - numpy.min([goals.maximum_deflection, 10000.0]),
        ]

    bounds = make_bounds(truss, joint_coordinates, shape_parameters)

    return (
        x0,
        objective_function,
        inequality_constraints,
        truss_generator,
        bounds,
    )
