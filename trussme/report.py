import json

import numpy
import pandas
import scipy

import trussme.visualize

from .truss import Truss, Goals


def report_to_str(truss: Truss, goals: Goals) -> str:
    """
    Generates a report on the truss

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss

    Returns
    -------
    str
        A full report on the truss
    """
    truss.calc_fos()

    report_string = generate_summary(truss, goals) + "\n"
    report_string += generate_instantiation_information(truss) + "\n"
    report_string += generate_stress_analysis(truss, goals) + "\n"

    return report_string


def report_to_md(file_name: str, truss: Truss, goals: Goals) -> None:
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

    Returns
    -------
    None
    """
    with open(file_name, "w") as f:
        f.write(report_to_str(truss, goals))


def generate_summary(truss, goals) -> str:
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
        + format(truss.fos, ".2f")
        + ".\n"
    )
    summary += "- The limit state is " + truss.limit_state + ".\n"

    success_string = []
    failure_string = []

    if goals.minimum_fos_buckling < truss.fos_buckling:
        success_string.append("buckling FOS")
    else:
        failure_string.append("buckling FOS")

    if goals.minimum_fos_yielding < truss.fos_yielding:
        success_string.append("yielding FOS")
    else:
        failure_string.append("yielding FOS")

    if goals.maximum_mass > truss.mass:
        success_string.append("mass")
    else:
        failure_string.append("mass")

    if goals.maximum_deflection > truss.deflection:
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

    data = []
    rows = [
        "Minimum FOS for Buckling",
        "Minimum FOS for Yielding",
        "Maximum Mass",
        "Maximum Deflection",
    ]
    data.append(
        [
            goals.minimum_fos_buckling,
            truss.fos_buckling,
            "Yes" if truss.fos_buckling > goals.minimum_fos_buckling else "No",
        ]
    )
    data.append(
        [
            goals.minimum_fos_yielding,
            truss.fos_yielding,
            "Yes" if truss.fos_yielding > goals.minimum_fos_yielding else "No",
        ]
    )
    data.append(
        [
            goals.maximum_mass,
            truss.mass,
            "Yes" if truss.mass < goals.maximum_mass else "No",
        ]
    )
    data.append(
        [
            goals.maximum_deflection,
            truss.deflection,
            "Yes" if truss.deflection < goals.maximum_deflection else "No",
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


def generate_instantiation_information(truss) -> str:
    """
    Generate a summary of the instantiation information.

    Parameters
    ----------
    truss: Truss
        The truss to be reported on

    Returns
    -------
    str
        A report of the instantiation information
    """
    instantiation = "# INSTANTIATION INFORMATION\n"

    instantiation += trussme.visualize.plot_truss(truss) + "\n"

    # Print joint information
    instantiation += "## JOINTS\n"
    data = []
    rows = []
    for j in truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
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
        data,
        index=rows,
        columns=["X", "Y", "Z", "X Support?", "Y Support?", "Z Support?"],
    ).to_markdown()

    # Print member information
    instantiation += "\n## MEMBERS\n"
    data = []
    rows = []
    for m in truss.members:
        rows.append("Member_" + "{0:02d}".format(m.idx))
        data.append(
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
        data,
        index=rows,
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
    data = []
    rows = []
    for mat in truss.materials:
        rows.append(mat["name"])
        data.append(
            [
                str(mat["density"]),
                str(mat["elastic_modulus"] / pow(10, 9)),
                str(mat["yield_strength"] / pow(10, 6)),
            ]
        )

    instantiation += pandas.DataFrame(
        data,
        index=rows,
        columns=[
            "Density (kg/m3)",
            "Elastic Modulus (GPa)",
            "Yield Strength (MPa)",
        ],
    ).to_markdown()

    return instantiation


def generate_stress_analysis(truss, goals) -> str:
    """
    Generate a summary of the stress analysis information.

    Parameters
    ----------
    truss: Truss
        The truss to be reported on
    goals: Goals
        The goals against which to evaluate the truss

    Returns
    -------
    str
        A report of the stress analysis information
    """
    analysis = "# STRESS ANALYSIS INFORMATION\n"

    # Print information about loads
    analysis += "## LOADING\n"
    data = []
    rows = []
    for j in truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                str(j.loads[0] / pow(10, 3)),
                format(
                    (
                        j.loads[1]
                        - sum([m.mass / 2.0 * scipy.constants.g for m in j.members])
                    )
                    / pow(10, 3),
                    ".2f",
                ),
                str(j.loads[2] / pow(10, 3)),
            ]
        )

    analysis += pandas.DataFrame(
        data, index=rows, columns=["X Load", "Y Load", "Z Load"]
    ).to_markdown()

    # Print information about reactions
    analysis += "\n## REACTIONS\n"
    data = []
    rows = []
    for j in truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                format(j.reactions[0] / pow(10, 3), ".2f")
                if j.translation_restricted[0] != 0.0
                else "N/A",
                format(j.reactions[1] / pow(10, 3), ".2f")
                if j.translation_restricted[1] != 0.0
                else "N/A",
                format(j.reactions[2] / pow(10, 3), ".2f")
                if j.translation_restricted[2] != 0.0
                else "N/A",
            ]
        )

    analysis += pandas.DataFrame(
        data,
        index=rows,
        columns=["X Reaction (kN)", "Y Reaction (kN)", "Z Reaction (kN)"],
    ).to_markdown()

    # Print information about members
    analysis += "\n## FORCES AND STRESSES\n"
    data = []
    rows = []
    for m in truss.members:
        rows.append("Member_" + "{0:02d}".format(m.idx))
        data.append(
            [
                m.area,
                format(m.moment_of_inertia, ".2e"),
                format(m.force / pow(10, 3), ".2f"),
                m.fos_yielding,
                "Yes" if m.fos_yielding > goals.minimum_fos_yielding else "No",
                m.fos_buckling if m.fos_buckling > 0 else "N/A",
                "Yes"
                if m.fos_buckling > goals.minimum_fos_buckling or m.fos_buckling < 0
                else "No",
            ]
        )

    analysis += pandas.DataFrame(
        data,
        index=rows,
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

    # Print information about members
    analysis += "\n## DEFLECTIONS\n"

    analysis += trussme.visualize.plot_truss(truss, deflected_shape=True) + "\n"

    data = []
    rows = []
    for j in truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                format(j.deflections[0] * pow(10, 3), ".5f")
                if j.translation_restricted[0] == 0.0
                else "N/A",
                format(j.deflections[1] * pow(10, 3), ".5f")
                if j.translation_restricted[1] == 0.0
                else "N/A",
                format(j.deflections[2] * pow(10, 3), ".5f")
                if j.translation_restricted[2] == 0.0
                else "N/A",
                "Yes"
                if numpy.linalg.norm(j.deflections) < goals.maximum_deflection
                else "No",
            ]
        )

    analysis += pandas.DataFrame(
        data,
        index=rows,
        columns=[
            "X Deflection(mm)",
            "Y Deflection (mm)",
            "Z Deflection (mm)",
            "OK Deflection?",
        ],
    ).to_markdown()

    return analysis
