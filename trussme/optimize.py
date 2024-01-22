from typing import Callable, Literal, Optional

import numpy

from trussme import Truss, Goals, read_json, Pipe, Box, Square, Bar


def make_x0(
    truss: Truss,
    joint_optimization: Optional[Literal["full"]] = "full",
    member_optimization: Optional[Literal["scaled", "full"]] = "full",
) -> list[float]:
    """
    Returns a vector that encodes the current truss design

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_optimization: None or "full", default = "full"
        If None, no optimization of joint location. If "full", then full optimization of joint locations will be used.
        This will add up to `3n` variables to the optimization vector, where `n` is the number of joints in the truss.
    member_optimization: None or "scaled" or "full", default = "full"
        If None, no optimization of member cross-section is performed. If "scaled", then member cross-section is
        optimally scaled based on initial shape, adding `m` variables to the optimization vector, where `m`, is the
        number of members in the truss. If "full", then member cross-section parameters will be separately
        optimized, adding up to `km` variables to the optimization vector, where `k` is the number of parameters
        defining the cross-section of an individual member.

    Returns
    -------
    list[float]
        A starting vector that encodes the current truss design
    """

    planar_direction: str = truss.is_planar()
    x0: list[float] = []

    configured_truss = read_json(truss.to_json())

    if joint_optimization:
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

    if member_optimization == "scaled":
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

    if member_optimization == "full":
        for i in range(len(configured_truss.members)):
            shape_name: str = configured_truss.members[i].shape.name()
            if shape_name == "pipe":
                x0.append(configured_truss.members[i].shape._params["r"])
                x0.append(configured_truss.members[i].shape._params["t"])
            elif shape_name == "box":
                x0.append(configured_truss.members[i].shape._params["w"])
                x0.append(configured_truss.members[i].shape._params["h"])
                x0.append(configured_truss.members[i].shape._params["t"])
            elif shape_name == "bar":
                x0.append(configured_truss.members[i].shape._params["r"])
            elif shape_name == "square":
                x0.append(configured_truss.members[i].shape._params["w"])
                x0.append(configured_truss.members[i].shape._params["h"])

    return x0


def make_bounds(
    truss: Truss,
    joint_optimization: Optional[Literal["full"]] = "full",
    member_optimization: Optional[Literal["scaled", "full"]] = "full",
) -> tuple[list[float], list[float]]:
    """
    Returns a tuple of vectors that represent lower and upper bounds for the variables of the optimization problem.

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_optimization: None or "full", default = "full"
        If None, no bounds are added. If "full", infinite bounds (lower = -inf, upper = inf) are added. This will add
        `n` bounds, where `n` is the number of joints in the truss.
    member_optimization: None or "scaled" or "full", default = "full"
        If None, no bounds are added. If "scaled", then 'm' bounds are added, where `m`, is the number of members in the
        truss. If "full", then up to `km` bounds are added, where `k` is the number of parameters defining the
        cross-section of an individual member.

    Returns
    -------
    list[float]
        A starting vector that encodes the current truss design
    """

    planar_direction: str = truss.is_planar()
    lb: list[float] = []
    ub: list[float] = []

    configured_truss = read_json(truss.to_json())

    if joint_optimization:
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

    if member_optimization == "scaled":
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

    if member_optimization == "full":
        for i in range(len(configured_truss.members)):
            shape_name: str = configured_truss.members[i].shape.name()
            if shape_name == "pipe":
                for _ in range(2):
                    lb.append(0.0)
                    ub.append(numpy.inf)
            elif shape_name == "box":
                for _ in range(3):
                    lb.append(0.0)
                    ub.append(numpy.inf)
            elif shape_name == "bar":
                lb.append(0.0)
                ub.append(numpy.inf)
            elif shape_name == "square":
                for _ in range(2):
                    lb.append(0.0)
                    ub.append(numpy.inf)

    return lb, ub


def make_truss_generator_function(
    truss: Truss,
    joint_optimization: Optional[Literal["full"]] = "full",
    member_optimization: Optional[Literal["scaled", "full"]] = "full",
) -> Callable[[list[float]], Truss]:
    """
    Returns a function that takes a list of floats and returns a truss.

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    joint_optimization: None or "full", default = "full"
        If None, no optimization of joint location. If "full", then full optimization of joint locations will be used.
    member_optimization: None or "scaled" or "full", default = "full"
        If None, no optimization of member cross-section is performed. If "scaled", then member cross-section is
        optimally scaled based on initial shape. If "full", then member cross-section parameters will be separately
        optimized.

    Returns
    -------
    Callable[list[float], Truss]
        A function that takes a list of floats and returns a truss.
    """

    planar_direction: str = truss.is_planar()

    def truss_generator(x: list[float]) -> Truss:
        configured_truss = read_json(truss.to_json())
        idx = 0

        if joint_optimization:
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

        if member_optimization == "scaled":
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

        if member_optimization == "full":
            for i in range(len(configured_truss.members)):
                shape_name: str = configured_truss.members[i].shape.name()
                if shape_name == "pipe":
                    configured_truss.members[i].shape = Pipe(r=x[idx], t=x[idx + 1])
                    idx += 2
                elif shape_name == "box":
                    configured_truss.members[i].shape = Box(
                        w=x[idx], h=x[idx + 1], t=x[idx + 2]
                    )
                    idx += 3
                elif shape_name == "bar":
                    configured_truss.members[i].shape = Bar(r=x[idx])
                    idx += 1
                elif shape_name == "square":
                    configured_truss.members[i].shape = Square(w=x[idx], h=x[idx + 1])
                    idx += 2

        return configured_truss

    return truss_generator


def make_inequality_constraints(
    truss: Truss,
    goals: Goals,
    joint_optimization: Optional[Literal["full"]] = "full",
    member_optimization: Optional[Literal["scaled", "full"]] = "full",
) -> Callable[[list[float]], list[float]]:
    """
    Returns a function that evaluates the inequality constraints.

    Parameters
    ----------
    truss: Truss
        The truss to configure.
    goals: Goals
        This informs constraints on yielding FOS, buckling FOS, and deflection.
    joint_optimization: Literal[None, "full"], default = "full"
        If None, no optimization of joint location. If "full", then full optimization of joint locations will be used.
    member_optimization: Literal[None, "scaled", "full"], default = "full"
        If None, no optimization of member cross-section is performed. If "scaled", then member cross-section is
        optimally scaled based on initial shape. If "full", then member cross-section parameters will be separately
        optimized.

    Returns
    -------
    Callable[[list[float]], list[float]]
        A function that evaluates constraints for the truss
    """
    truss_generator = make_truss_generator_function(
        truss, joint_optimization, member_optimization
    )

    def inequality_constraints(x: list[float]) -> list[float]:
        recon_truss = truss_generator(x)
        recon_truss.analyze()
        constraints = [
            goals.minimum_fos_buckling - recon_truss.fos_buckling,
            goals.minimum_fos_yielding - recon_truss.fos_yielding,
            recon_truss.deflection - numpy.min([goals.maximum_deflection, 10000.0]),
        ]
        if member_optimization == "full":
            for i in range(len(recon_truss.members)):
                shape_name: str = recon_truss.members[i].shape.name()
                if shape_name == "pipe":
                    constraints.append(
                        recon_truss.members[i].shape._params["t"]
                        - recon_truss.members[i].shape._params["r"]
                    )
                elif shape_name == "box":
                    constraints.append(
                        recon_truss.members[i].shape._params["t"]
                        - recon_truss.members[i].shape._params["w"]
                    )
                    constraints.append(
                        recon_truss.members[i].shape._params["t"]
                        - recon_truss.members[i].shape._params["h"]
                    )

        return constraints

    return inequality_constraints


def make_optimization_functions(
    truss: Truss,
    goals: Goals,
    joint_optimization: Optional[Literal["full"]] = "full",
    member_optimization: Optional[Literal["scaled", "full"]] = "full",
) -> tuple[
    list[float],
    Callable[[list[float]], float],
    Callable[[list[float]], list[float]],
    Callable[[list[float]], Truss],
    tuple[list[float], list[float]],
]:
    """
    Creates functions for use in optimization, including a starting vector, objective function, a constraint function,
    and a truss generator function.

    Parameters
    ----------
    truss: Truss
        The truss to use as a starting configuration
    goals: Goals
        The goals to use for optimization
    joint_optimization: Literal[None, "full"] = "full"
        If None, no optimization of joint location. If "full", then full optimization of joint locations will be used.
    member_optimization: Literal[None, "scaled", "full"] = "full",
        Whether to include shape parameters.

    Returns
    -------
    tuple[
        list[float],
        Callable[[list[float]], float],
        Callable[[list[float]], list[float]],
        Callable[[list[float]], Truss],
        tuple[list[float], list[float]]
    ]
        A tuple containing the starting vector, objective function, constraint function, and truss generator function.
    """

    x0 = make_x0(truss, joint_optimization, member_optimization)

    truss_generator = make_truss_generator_function(
        truss, joint_optimization, member_optimization
    )

    lower_bounds, upper_bounds = make_bounds(
        truss, joint_optimization, member_optimization
    )

    inequality_constraints = make_inequality_constraints(
        truss, goals, joint_optimization, member_optimization
    )

    def objective_function(x: list[float]) -> float:
        return truss_generator(x).mass

    return (
        x0,
        objective_function,
        inequality_constraints,
        truss_generator,
        (lower_bounds, upper_bounds),
    )
