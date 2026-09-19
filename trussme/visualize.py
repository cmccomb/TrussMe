from typing import Literal, Any, Optional, Union

import matplotlib.colors
import matplotlib.pyplot
import numpy

from matplotlib.figure import Figure

from trussme.truss import Truss

MatplotlibColor = Any
"""Type: New type to represent a matplotlib color, simply an alias of Any"""


def plot_truss(
    truss: Truss,
    starting_shape: Optional[Union[Literal["fos", "force"], MatplotlibColor]] = "k",
    deflected_shape: Optional[Union[Literal["fos", "force"], MatplotlibColor]] = None,
    exaggeration_factor: float = 10,
    fos_threshold: float = 1.0,
    projection: Literal["xy", "xz", "yz"] = "xy",
    buckling_directions: bool = False,
) -> Figure:
    """Plot the truss.

    Parameters
    ----------
    truss: Truss
        The truss to plot.
    starting_shape: None or "fos" or "force" or MatplotlibColor, default="k"
        How to show the starting shape. If None, the starting shape is not shown. If "fos", the members are colored
        green if the factor of safety is above the threshold and red if it is below. If "force", the members are colored
        according to the force in the member. If a color, the members are colored that color.
    deflected_shape:  None or "fos" or "force" or MatplotlibColor, default = None
        How to show the deflected shape. If None, the starting shape is not shown. If "fos", the members are colored
        green if the factor of safety is above the threshold and red if it is below. If "force", the members are colored
        according to the force in the member. If a color, the members are colored that color.
    exaggeration_factor: float, default=10
        The factor by which to exaggerate the deflected shape.
    fos_threshold: float, default=1.0
        The threshold for the factor of safety. If the factor of safety is below this value, the member is colored red.

    projection: "xy", "xz", or "yz", default="xy"
        Global coordinate plane to display.
    buckling_directions: bool, default=False
        Mark the governing Euler capacity direction for compressed members.
        A circle with a dot denotes a direction normal to the projection plane.
        These marks are not eigenmode or post-buckling shapes.

    Returns
    -------
    Figure
        A matplotlib figure containing the truss
    """

    if projection not in ("xy", "xz", "yz"):
        raise ValueError("Projection must be xy, xz, or yz")
    a, b = ("xyz".index(axis) for axis in projection)
    fig: Figure = matplotlib.pyplot.figure()
    ax = fig.add_subplot(
        111,
    )

    ax.axis("equal")
    ax.set_axis_off()

    scaler = max((abs(member.force) for member in truss.members), default=0.0)
    if scaler == 0.0:
        scaler = 1.0

    force_colormap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "force",
        numpy.array([[1.0, 0.0, 0.0], [0.8, 0.8, 0.8], [0.0, 0.0, 1.0]]),
    )

    for member in truss.members:
        start_color: MatplotlibColor
        if starting_shape == "fos":
            start_color = (
                "g"
                if numpy.min(
                    [member.governing_buckling.factor_of_safety, member.fos_yielding]
                )
                > fos_threshold
                else "r"
            )
        elif starting_shape == "force":
            start_color = force_colormap(member.force / (2 * scaler) + 0.5)
        elif starting_shape is None:
            break
        else:
            start_color = starting_shape
        ax.plot(
            [member.begin_joint.coordinates[a], member.end_joint.coordinates[a]],
            [member.begin_joint.coordinates[b], member.end_joint.coordinates[b]],
            color=start_color,
        )

    for member in truss.members:
        def_color: MatplotlibColor
        if deflected_shape == "fos":
            def_color = (
                "g"
                if numpy.min(
                    [member.governing_buckling.factor_of_safety, member.fos_yielding]
                )
                > fos_threshold
                else "r"
            )
        elif deflected_shape == "force":
            def_color = force_colormap(member.force / (2 * scaler) + 0.5)
        elif deflected_shape is None:
            break
        else:
            def_color = deflected_shape
        ax.plot(
            [
                member.begin_joint.coordinates[a]
                + exaggeration_factor * member.begin_joint.deflections[a],
                member.end_joint.coordinates[a]
                + exaggeration_factor * member.end_joint.deflections[a],
            ],
            [
                member.begin_joint.coordinates[b]
                + exaggeration_factor * member.begin_joint.deflections[b],
                member.end_joint.coordinates[b]
                + exaggeration_factor * member.end_joint.deflections[b],
            ],
            color=def_color,
        )

    if buckling_directions:
        ax.set_title(f"{projection.upper()}: governing Euler capacity directions")
        for member in truss.members:
            if member.force >= 0:
                continue
            center = (
                numpy.array(member.begin_joint.coordinates)
                + numpy.array(member.end_joint.coordinates)
            ) / 2
            direction = numpy.array(member.governing_buckling.direction)[[a, b]]
            if numpy.linalg.norm(direction) < 1e-12:
                ax.plot(center[a], center[b], marker=r"$\odot$", color="darkorange")
            else:
                delta = direction * member.length * 0.08
                ax.annotate(
                    "",
                    xy=center[[a, b]] + delta,
                    xytext=center[[a, b]] - delta,
                    arrowprops={"arrowstyle": "<->", "color": "darkorange"},
                )

    return fig
