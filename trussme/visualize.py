import matplotlib.pyplot
import io
import re
import numpy
from typing import Union, Literal


def plot_truss(
    truss,
    starting_shape: Union[
        None, Literal["fos", "force", "b", "g", "r", "c", "m", "y", "k"]
    ] = "k",
    deflected_shape: Union[
        None, Literal["fos", "force", "b", "g", "r", "c", "m", "y", "k"]
    ] = None,
    exaggeration_factor: float = 10,
    fos_threshold: float = 1.0,
) -> str:
    """Plot the truss.

    Parameters
    ----------
    truss: Truss
        The truss to plot.
    starting_shape: : Union[None, Literal["fos", "force", "b", "g", "r", "c", "m", "y", "k"]], default="k"
        How to show the starting shape. If None, the starting shape is not shown. If "fos", the members are colored
        green if the factor of safety is above the threshold and red if it is below. If "force", the members are colored
        according to the force in the member. If a color, the members are colored that color.
    deflected_shape: : Union[None, Literal["fos", "force", "b", "g", "r", "c", "m", "y", "k"]], default = None
        How to show the deflected shape. If None, the starting shape is not shown. If "fos", the members are colored
        green if the factor of safety is above the threshold and red if it is below. If "force", the members are colored
        according to the force in the member. If a color, the members are colored that color.
    exaggeration_factor: float, default=10
        The factor by which to exaggerate the deflected shape.
    fos_threshold: float, default=1.0
        The threshold for the factor of safety. If the factor of safety is below this value, the member is colored red.

    Returns
    -------
    str
        An svg string of the truss
    """
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(
        111,
    )

    ax.axis("equal")
    ax.set_axis_off()

    scaler: float = numpy.max(numpy.abs([member.force for member in truss.members]))

    for member in truss.members:
        if starting_shape == "fos":
            color = "g" if member.fos > fos_threshold else "r"
        elif starting_shape == "force":
            color = matplotlib.pyplot.cm.bwr(member.force / (2 * scaler) + 0.5)
        elif starting_shape is None:
            break
        else:
            color = starting_shape
        ax.plot(
            [member.begin_joint.coordinates[0], member.end_joint.coordinates[0]],
            [member.begin_joint.coordinates[1], member.end_joint.coordinates[1]],
            color=color,
        )

    if deflected_shape:
        for member in truss.members:
            if starting_shape == "fos":
                color = "g" if member.fos > fos_threshold else "r"
            elif starting_shape == "force":
                color = matplotlib.pyplot.cm.bwr(member.force / (2 * scaler) + 0.5)
            elif starting_shape is None:
                break
            else:
                color = starting_shape
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
                color=color,
            )

    imgdata = io.StringIO()
    fig.savefig(imgdata, format="svg")
    imgdata.seek(0)  # rewind the data

    svg = imgdata.getvalue()
    svg = re.sub("<dc:date>(.*?)</dc:date>", "<dc:date></dc:date>", svg)
    svg = re.sub("url\(#(.*?)\)", "url(#truss)", svg)
    svg = re.sub('<clipPath id="(.*?)">', '<clipPath id="truss">', svg)

    return svg
