import json
import io
import re

import numpy
import pandas
from matplotlib.figure import Figure

import trussme.visualize

from trussme.truss import Truss, Goals


def _fig_to_svg(fig: Figure) -> str:
    imgdata = io.StringIO()
    fig.savefig(imgdata, format="svg")
    imgdata.seek(0)  # rewind the data

    svg = imgdata.getvalue()
    svg = re.sub("<dc:date>(.*?)</dc:date>", "<dc:date></dc:date>", svg)
    svg = re.sub(r"url\(#(.*?)\)", "url(#truss)", svg)
    svg = re.sub('<clipPath id="(.*?)">', '<clipPath id="truss">', svg)

    return svg


def report_to_str(truss: Truss, goals: Goals, with_figures: bool = True) -> str:
    """
    Generates a report on the truss

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss
    with_figures: bool, default=True
        Whether to include figures in the report

    Returns
    -------
    str
        A full report on the truss
    """
    goals.validate()
    truss.analyze()

    report_string = __generate_summary(truss, goals) + "\n"
    report_string += __generate_instantiation_information(truss, with_figures) + "\n"
    report_string += __generate_stress_analysis(truss, goals, with_figures) + "\n"

    return report_string


def print_report(truss: Truss, goals: Goals) -> None:
    """
    Prints a report on the truss

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss

    Returns
    -------
    None
    """
    print(report_to_str(truss, goals, with_figures=False))


def report_to_md(
    file_name: str, truss: Truss, goals: Goals, with_figures: bool = True
) -> None:
    """
    Writes a report in Markdown format

    Parameters
    ----------
    file_name: str
        The name of the file
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss
    with_figures: bool, default=True
        Whether to include figures in the report

    Returns
    -------
    None
    """
    with open(file_name, "w") as f:
        f.write(report_to_str(truss, goals, with_figures=with_figures))


def __generate_summary(truss: Truss, goals: Goals) -> str:
    """
    Generate a summary of the analysis.

    Parameters
    ----------
    truss: Truss
        The truss to be summarized
    goals: Goals
        The goals against which to evaluate the truss

    Returns
    -------
    str
        A string containing the summary
    """
    summary = "# SUMMARY OF ANALYSIS\n"
    summary += (
        "- The truss has a mass of "
        + format(truss.mass, ".2f")
        + " kg, and a total factor of safety of "
        + format(min(truss.fos_yielding, truss.fos_buckling_governing), ".2f")
        + ".\n"
    )
    summary += (
        "- The limit state is "
        + (
            "buckling"
            if truss.fos_buckling_governing < truss.fos_yielding
            else "yielding"
        )
        + ".\n"
    )
    summary += f"- Gravity: {truss.gravity} m/s²; member self-weight is split equally between endpoints.\n"

    success_string: list[str] = []
    failure_string: list[str] = []

    if goals.minimum_fos_buckling <= truss.fos_buckling_governing:
        success_string.append("buckling FOS")
    else:
        failure_string.append("buckling FOS")

    if goals.minimum_fos_yielding <= truss.fos_yielding:
        success_string.append("yielding FOS")
    else:
        failure_string.append("yielding FOS")

    if goals.maximum_mass >= truss.mass:
        success_string.append("mass")
    else:
        failure_string.append("mass")

    if goals.maximum_deflection >= truss.deflection:
        success_string.append("deflection")
    else:
        failure_string.append("deflection")

    if len(success_string) != 0:
        if len(success_string) == 1:
            summary += (
                " The design goal for " + str(success_string[0]) + " was satisfied.\n"
            )
        elif len(success_string) == 2:
            summary += (
                "- The design goals for "
                + str(success_string[0])
                + " and "
                + str(success_string[1])
                + " were satisfied.\n"
            )
        else:
            summary += "- The design goals for "
            for st in success_string[0:-1]:
                summary += st + ", "
            summary += "and " + str(success_string[-1]) + " were satisfied.\n"

    if len(failure_string) != 0:
        if len(failure_string) == 1:
            summary += (
                "- The design goal for "
                + str(failure_string[0])
                + " was not satisfied.\n"
            )
        elif len(failure_string) == 2:
            summary += (
                "- The design goals for "
                + str(failure_string[0])
                + " and "
                + str(failure_string[1])
                + " were not satisfied.\n"
            )
        else:
            summary += "- The design goals for "
            for st in failure_string[0:-1]:
                summary += st + ","
            summary += "and " + str(failure_string[-1]) + " were not satisfied.\n"

    data: list[list[float | str]] = []
    rows: list[str] = [
        "Minimum FOS for Buckling",
        "Minimum FOS for Yielding",
        "Maximum Mass",
        "Maximum Deflection",
    ]
    data.append(
        [
            goals.minimum_fos_buckling,
            truss.fos_buckling_governing,
            "Yes"
            if truss.fos_buckling_governing >= goals.minimum_fos_buckling
            else "No",
        ]
    )
    data.append(
        [
            goals.minimum_fos_yielding,
            truss.fos_yielding,
            "Yes" if truss.fos_yielding >= goals.minimum_fos_yielding else "No",
        ]
    )
    data.append(
        [
            goals.maximum_mass,
            truss.mass,
            "Yes" if truss.mass <= goals.maximum_mass else "No",
        ]
    )
    data.append(
        [
            goals.maximum_deflection,
            truss.deflection,
            "Yes" if truss.deflection <= goals.maximum_deflection else "No",
        ]
    )

    summary += (
        "\n"
        + pandas.DataFrame(
            data,
            index=rows,
            columns=["Target", "Actual", "Ok?"],
        ).to_markdown()
    )

    return summary


def __generate_instantiation_information(
    truss: Truss, with_figures: bool = True
) -> str:
    """
    Generate a summary of the instantiation information.

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    with_figures: bool, default=True
        Whether to include figures in the report

    Returns
    -------
    str
        A report of the instantiation information
    """
    instantiation = "# INSTANTIATION INFORMATION\n"

    if with_figures:
        instantiation += _fig_to_svg(trussme.visualize.plot_truss(truss)) + "\n"

    # Print joint information
    instantiation += "## JOINTS\n"
    joint_data: list[list[str]] = []
    joint_rows: list[str] = []
    for j in truss.joints:
        joint_rows.append("Joint_" + "{0:02d}".format(j.idx))
        joint_data.append(
            [
                str(j.coordinates[0]),
                str(j.coordinates[1]),
                str(j.coordinates[2]),
                str(j.translation_restricted[0]),
                str(j.translation_restricted[1]),
                str(j.translation_restricted[2]),
            ]
        )

    instantiation += pandas.DataFrame(
        joint_data,
        index=joint_rows,
        columns=["X", "Y", "Z", "X Support?", "Y Support?", "Z Support?"],
    ).to_markdown()

    # Print member information
    instantiation += "\n## MEMBERS\n"
    member_data: list[list[str | float]] = []
    member_rows: list[str] = []
    for m in truss.members:
        member_rows.append("Member_" + "{0:02d}".format(m.idx))
        member_data.append(
            [
                str(m.begin_joint.idx),
                str(m.end_joint.idx),
                m.material_name,
                m.shape.name(),
                json.dumps(m.shape._params)
                .replace('"', "")
                .replace(": ", "=")
                .replace("{", "")
                .replace("}", ""),
                m.mass,
            ]
        )

    instantiation += pandas.DataFrame(
        member_data,
        index=member_rows,
        columns=[
            "Beginning Joint",
            "Ending Joint",
            "Material",
            "Shape",
            "Parameters (m)",
            "Mass (kg)",
        ],
    ).to_markdown()

    # Print material list
    instantiation += "\n## MATERIALS\n"
    material_data: list[list[str]] = []
    material_rows: list[str] = []
    for mat in truss.materials:
        material_rows.append(mat["name"])
        material_data.append(
            [
                str(mat["density"]),
                str(mat["elastic_modulus"] / pow(10, 9)),
                str(mat["yield_strength"] / pow(10, 6)),
            ]
        )

    instantiation += pandas.DataFrame(
        material_data,
        index=material_rows,
        columns=[
            "Density (kg/m3)",
            "Elastic Modulus (GPa)",
            "Yield Strength (MPa)",
        ],
    ).to_markdown()

    return instantiation


def __generate_stress_analysis(
    truss: Truss, goals: Goals, with_figures: bool = True
) -> str:
    """
    Generate a summary of the stress analysis information.

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss
    with_figures: bool, default=True
        Whether to include figures in the report

    Returns
    -------
    str
        A report of the stress analysis information
    """
    analysis = "# STRESS ANALYSIS INFORMATION\n"

    # Print information about loads
    analysis += "## LOADING\n"
    load_data: list[list[str]] = []
    load_rows: list[str] = []
    for j, loads in zip(truss.joints, truss.nodal_loads):
        load_rows.append("Joint_" + "{0:02d}".format(j.idx))
        load_data.append([format(value / 1000, ".2f") for value in loads])

    analysis += pandas.DataFrame(
        load_data,
        index=load_rows,
        columns=["X Load (kN)", "Y Load (kN)", "Z Load (kN)"],
    ).to_markdown()

    # Print information about reactions
    analysis += "\n## REACTIONS\n"
    reaction_data: list[list[str]] = []
    reaction_rows: list[str] = []
    for j in truss.joints:
        reaction_rows.append("Joint_" + "{0:02d}".format(j.idx))
        reaction_data.append(
            [
                (
                    format(j.reactions[0] / pow(10, 3), ".2f")
                    if j.translation_restricted[0] != 0.0
                    else "N/A"
                ),
                (
                    format(j.reactions[1] / pow(10, 3), ".2f")
                    if j.translation_restricted[1] != 0.0
                    else "N/A"
                ),
                (
                    format(j.reactions[2] / pow(10, 3), ".2f")
                    if j.translation_restricted[2] != 0.0
                    else "N/A"
                ),
            ]
        )

    analysis += pandas.DataFrame(
        reaction_data,
        index=reaction_rows,
        columns=["X Reaction (kN)", "Y Reaction (kN)", "Z Reaction (kN)"],
    ).to_markdown()

    # Print information about members
    analysis += "\n## FORCES AND STRESSES\n"

    if with_figures:
        analysis += (
            _fig_to_svg(trussme.visualize.plot_truss(truss, starting_shape="force"))
            + "\n"
        )

    member_data: list[list[str | float]] = []
    member_rows: list[str] = []
    for m in truss.members:
        member_rows.append("Member_" + "{0:02d}".format(m.idx))
        member_data.append(
            [
                m.area,
                format(m.moment_of_inertia, ".2e"),
                format(m.force / pow(10, 3), ".2f"),
                m.fos_yielding,
                "Yes" if m.fos_yielding >= goals.minimum_fos_yielding else "No",
                m.governing_buckling.factor_of_safety
                if m.governing_buckling.factor_of_safety > 0
                else "N/A",
                (
                    "Yes"
                    if m.governing_buckling.factor_of_safety
                    >= goals.minimum_fos_buckling
                    or m.governing_buckling.factor_of_safety < 0
                    else "No"
                ),
            ]
        )

    analysis += pandas.DataFrame(
        member_data,
        index=member_rows,
        columns=[
            "Area (m^2)",
            "Moment of Inertia (m^4)",
            "Axial force(kN)",
            "FOS yielding",
            "OK yielding?",
            "FOS buckling",
            "OK buckling?",
        ],
    ).to_markdown()

    analysis += "\n## DIRECTIONAL BUCKLING\n"
    analysis += (
        "Euler member checks use Pcr = π² E I / (K L)². Both transverse "
        "directions are checked regardless of the legacy scalar setting. "
        "K represents caller-supplied end conditions or bracing; it adds "
        "no physical brace. These are capacity directions, not eigenmodes "
        "or post-buckling shapes. Equal capacities have no unique direction.\n\n"
    )
    mode_data = []
    for member in truss.members:
        for index, mode in enumerate(member.buckling_modes):
            mode_data.append(
                [
                    member.idx,
                    index + 1,
                    str(mode.direction),
                    mode.moment_of_inertia,
                    member.buckling.effective_length_factors[index],
                    mode.effective_length,
                    mode.critical_load,
                    mode.factor_of_safety,
                    "Yes" if mode == member.governing_buckling else "No",
                ]
            )
    analysis += pandas.DataFrame(
        mode_data,
        columns=[
            "Member",
            "Mode",
            "Global deflection direction",
            "I (m^4)",
            "K",
            "KL (m)",
            "Critical load (N)",
            "FOS",
            "Governs?",
        ],
    ).to_markdown(index=False)

    # Print information about members
    analysis += "\n## DEFLECTIONS\n"

    if with_figures:
        analysis += (
            _fig_to_svg(
                trussme.visualize.plot_truss(
                    truss, starting_shape="k", deflected_shape="m"
                )
            )
            + "\n"
        )

    deflection_data: list[list[str]] = []
    deflection_rows: list[str] = []
    for j in truss.joints:
        deflection_rows.append("Joint_" + "{0:02d}".format(j.idx))
        deflection_data.append(
            [
                (
                    format(j.deflections[0] * pow(10, 3), ".5f")
                    if j.translation_restricted[0] == 0.0
                    else "N/A"
                ),
                (
                    format(j.deflections[1] * pow(10, 3), ".5f")
                    if j.translation_restricted[1] == 0.0
                    else "N/A"
                ),
                (
                    format(j.deflections[2] * pow(10, 3), ".5f")
                    if j.translation_restricted[2] == 0.0
                    else "N/A"
                ),
                (
                    "Yes"
                    if numpy.linalg.norm(j.deflections) <= goals.maximum_deflection
                    else "No"
                ),
            ]
        )

    analysis += pandas.DataFrame(
        deflection_data,
        index=deflection_rows,
        columns=[
            "X Deflection(mm)",
            "Y Deflection (mm)",
            "Z Deflection (mm)",
            "OK Deflection?",
        ],
    ).to_markdown()

    return analysis
