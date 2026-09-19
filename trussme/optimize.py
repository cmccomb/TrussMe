from copy import deepcopy
from typing import Callable, Literal, Optional

import numpy

from trussme import Truss, Goals, Pipe, Box, Square, Bar


def _joint_can_move(joint, planar_direction: str) -> bool:
    return not any(value != 0 for value in joint.loads) and all(
        not fixed or axis == planar_direction
        for axis, fixed in zip("xyz", joint.translation_restricted)
    )


def _validate_modes(truss, joint_optimization, member_optimization):
    if joint_optimization not in (None, "full") or member_optimization not in (
        None,
        "scaled",
        "full",
    ):
        raise ValueError("Unsupported optimization mode")
    if member_optimization and any(
        m.shape.name() not in ("pipe", "bar", "square", "box") for m in truss.members
    ):
        raise ValueError("Custom sections require caller-defined sizing logic")


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


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

    _validate_modes(truss, joint_optimization, member_optimization)
    planar_direction: str = truss.is_planar()
    x0: list[float] = []

    configured_truss = deepcopy(truss)

    if joint_optimization:
        for i in range(len(configured_truss.joints)):
            if _joint_can_move(configured_truss.joints[i], planar_direction):
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

    _validate_modes(truss, joint_optimization, member_optimization)
    planar_direction: str = truss.is_planar()
    lb: list[float] = []
    ub: list[float] = []

    configured_truss = deepcopy(truss)

    if joint_optimization:
        for i in range(len(configured_truss.joints)):
            if _joint_can_move(configured_truss.joints[i], planar_direction):
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

    _validate_modes(truss, joint_optimization, member_optimization)
    planar_direction: str = truss.is_planar()

    snapshot = deepcopy(truss)
    vector_length = len(make_x0(snapshot, joint_optimization, member_optimization))

    def truss_generator(x: list[float]) -> Truss:
        if len(x) != vector_length or not numpy.isfinite(x).all():
            raise ValueError(
                "Design vector must have the expected length and finite values"
            )
        configured_truss = deepcopy(snapshot)
        idx = 0

        if joint_optimization:
            for i in range(len(configured_truss.joints)):
                if _joint_can_move(configured_truss.joints[i], planar_direction):
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
                    thickness_ratio = _safe_ratio(p["t"], p["r"])
                    configured_truss.members[i].shape = Pipe(
                        r=x[idx], t=x[idx] * thickness_ratio
                    )
                    idx += 1
                elif shape_name == "box":
                    height_ratio = _safe_ratio(p["h"], p["w"])
                    thickness_ratio = _safe_ratio(p["t"], p["w"])
                    configured_truss.members[i].shape = Box(
                        w=x[idx],
                        h=x[idx] * height_ratio,
                        t=x[idx] * thickness_ratio,
                    )
                    idx += 1
                elif shape_name == "bar":
                    configured_truss.members[i].shape = Bar(r=x[idx])
                    idx += 1
                elif shape_name == "square":
                    height_ratio = _safe_ratio(p["h"], p["w"])
                    configured_truss.members[i].shape = Square(
                        w=x[idx], h=x[idx] * height_ratio
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
        This informs constraints on both buckling directions, yielding, deflection, and mass.
        The first four residuals are dimensionless and feasible at <= 0. Full
        sizing appends pipe t-r or box 2t-w, 2t-h residuals in metres.
        Invalid or singular trials return finite positive design penalties.
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

    goals = deepcopy(goals)
    goals.validate()
    truss.validate()

    def inequality_constraints(x: list[float]) -> list[float]:
        recon_truss = truss_generator(x)
        geometry = []
        if member_optimization == "full":
            for member in recon_truss.members:
                p = member.shape._params
                if member.shape.name() == "pipe":
                    geometry.append(p["t"] - p["r"])
                elif member.shape.name() == "box":
                    geometry.extend([2 * p["t"] - p["w"], 2 * p["t"] - p["h"]])
        try:
            recon_truss.analyze()
        except (ValueError, numpy.linalg.LinAlgError):
            # Finite infeasibility penalties let solvers reject zero/invalid
            # sections or singular trial geometries without losing vector shape.
            return [1e6] * 4 + geometry
        return goals.evaluate(recon_truss) + geometry

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
