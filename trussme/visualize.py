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

    Returns
    -------
    Figure
        A matplotlib figure containing the truss
    """

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
                if numpy.min([member.fos_buckling, member.fos_yielding]) > fos_threshold
                else "r"
            )
        elif starting_shape == "force":
            start_color = force_colormap(member.force / (2 * scaler) + 0.5)
        elif starting_shape is None:
            break
        else:
            start_color = starting_shape
        ax.plot(
            [member.begin_joint.coordinates[0], member.end_joint.coordinates[0]],
            [member.begin_joint.coordinates[1], member.end_joint.coordinates[1]],
            color=start_color,
        )

    for member in truss.members:
        def_color: MatplotlibColor
        if deflected_shape == "fos":
            def_color = (
                "g"
                if numpy.min([member.fos_buckling, member.fos_yielding]) > fos_threshold
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
                member.begin_joint.coordinates[0]
                + exaggeration_factor * member.begin_joint.deflections[0],
                member.end_joint.coordinates[0]
                + exaggeration_factor * member.end_joint.deflections[0],
            ],
            [
                member.begin_joint.coordinates[1]
                + exaggeration_factor * member.begin_joint.deflections[1],
                member.end_joint.coordinates[1]
                + exaggeration_factor * member.end_joint.deflections[1],
            ],
            color=def_color,
        )

    return fig
