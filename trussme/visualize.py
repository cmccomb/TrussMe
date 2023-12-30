import matplotlib.pyplot
import io
import re


def plot_truss(
    truss, deflected_shape: bool = False, exaggeration_factor: float = 10
) -> str:
    """Plot the truss.

    Parameters
    ----------
    truss: Truss
        The truss to plot.
    deflected_shape: bool, default=False
        Whether to plot the deflected shape.
    exaggeration_factor: float, default=10
        The factor by which to exaggerate the deflected shape.

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

    for member in truss.members:
        ax.plot(
            [member.begin_joint.coordinates[0], member.end_joint.coordinates[0]],
            [member.begin_joint.coordinates[1], member.end_joint.coordinates[1]],
            color="k",
        )

    if deflected_shape:
        for member in truss.members:
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
                color="m",
            )

    imgdata = io.StringIO()
    fig.savefig(imgdata, format="svg")
    imgdata.seek(0)  # rewind the data

    svg = imgdata.getvalue()
    svg = re.sub("<dc:date>(.*?)</dc:date>", "<dc:date></dc:date>", svg)
    svg = re.sub("url\(#(.*?)\)", "url(#truss)", svg)
    svg = re.sub('<clipPath id="(.*?)">', '<clipPath id="truss">', svg)

    return svg
