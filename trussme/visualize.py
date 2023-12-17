import matplotlib.pyplot
import io
import re


def plot_truss(truss, deflected_shape: bool = False) -> str:
    """Plot the truss.

    Args:
        truss (Truss): The truss to plot.
        deflected_shape (bool, optional): Plot the deflected shape. Defaults to False.

    Returns:
        matplotlib.pyplot.Figure: The figure containing the plot.
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

    factor = 10

    if deflected_shape:
        for member in truss.members:
            ax.plot(
                [
                    member.begin_joint.coordinates[0]
                    + factor * member.begin_joint.deflections[0],
                    member.end_joint.coordinates[0]
                    + factor * member.end_joint.deflections[0],
                ],
                [
                    member.begin_joint.coordinates[1]
                    + factor * member.begin_joint.deflections[1],
                    member.end_joint.coordinates[1]
                    + factor * member.end_joint.deflections[1],
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
