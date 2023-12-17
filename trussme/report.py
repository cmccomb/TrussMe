import numpy
import pandas

import trussme.components as pp


def generate_summary(the_truss) -> str:
    summary = "# SUMMARY OF ANALYSIS\n"
    summary += (
        "- The truss has a mass of "
        + format(the_truss.mass, ".2f")
        + " kg, and a total factor of safety of "
        + format(the_truss.fos_total, ".2f")
        + ".\n"
    )
    summary += "- The limit state is " + the_truss.limit_state + ".\n"

    success_string = []
    failure_string = []
    if the_truss.minimum_fos_total < the_truss.fos_total:
        success_string.append("total FOS")
    else:
        failure_string.append("total FOS")

    if the_truss.minimum_fos_buckling < the_truss.fos_buckling:
        success_string.append("buckling FOS")
    else:
        failure_string.append("buckling FOS")

    if the_truss.minimum_fos_yielding < the_truss.fos_yielding:
        success_string.append("yielding FOS")
    else:
        failure_string.append("yielding FOS")

    if the_truss.maximum_mass > the_truss.mass:
        success_string.append("mass")
    else:
        failure_string.append("mass")

    if the_truss.maximum_deflection > the_truss.deflection:
        success_string.append("deflection")
    else:
        failure_string.append("deflection")

    if len(success_string) is not 0:
        if len(success_string) is 1:
            summary += (
                " The design goal for " + str(success_string[0]) + " was satisfied.\n"
            )
        elif len(success_string) is 2:
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

    if len(failure_string) is not 0:
        if len(failure_string) is 1:
            summary += (
                "- The design goal for "
                + str(failure_string[0])
                + " was not satisfied.\n"
            )
        elif len(failure_string) is 2:
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

    return summary


def generate_instantiation_information(the_truss) -> str:
    instantiation = "# INSTANTIATION INFORMATION\n"

    # Print joint information
    instantiation += "## JOINTS\n"
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                str(j.coordinates[0]),
                str(j.coordinates[1]),
                str(j.coordinates[2]),
                str(j.translation[0]),
                str(j.translation[1]),
                str(j.translation[2]),
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
    for m in the_truss.members:
        rows.append("Member_" + "{0:02d}".format(m.idx))
        data.append(
            [
                str(m.begin_joint.idx),
                str(m.end_joint.idx),
                m.material_name,
                m.shape.name(),
                m.shape.h,
                m.shape.w,
                m.shape.r,
                m.shape.t,
                m.mass,
            ]
        )

    instantiation += pandas.DataFrame(
        data,
        index=rows,
        columns=[
            "Joint-A",
            "Joint-B",
            "Material",
            "Shape",
            "Height (m)",
            "Width (m)",
            "Radius (m)",
            "Thickness (m)",
            "Mass (kg)",
        ],
    ).to_markdown()

    # Print material list
    instantiation += "\n## MATERIALS\n"
    data = []
    rows = []
    for mat in the_truss.materials:
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


def generate_stress_analysis(the_truss) -> str:
    analysis = "# STRESS ANALYSIS INFORMATION\n"

    # Print information about loads
    analysis += "## LOADING\n"
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                str(j.loads[0] / pow(10, 3)),
                format(
                    (j.loads[1] - sum([m.mass / 2.0 * pp.g for m in j.members]))
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
    for j in the_truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                format(j.reactions[0] / pow(10, 3), ".2f")
                if j.translation[0] != 0.0
                else "N/A",
                format(j.reactions[1] / pow(10, 3), ".2f")
                if j.translation[1] != 0.0
                else "N/A",
                format(j.reactions[2] / pow(10, 3), ".2f")
                if j.translation[2] != 0.0
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
    for m in the_truss.members:
        rows.append("Member_" + "{0:02d}".format(m.idx))
        data.append(
            [
                m.area,
                format(m.moment_of_inertia, ".2e"),
                format(m.force / pow(10, 3), ".2f"),
                m.fos_yielding,
                "Yes" if m.fos_yielding > the_truss.minimum_fos_yielding else "No",
                m.fos_buckling if m.fos_buckling > 0 else "N/A",
                "Yes"
                if m.fos_buckling > the_truss.minimum_fos_buckling or m.fos_buckling < 0
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
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_" + "{0:02d}".format(j.idx))
        data.append(
            [
                format(j.deflections[0] * pow(10, 3), ".5f")
                if j.translation[0] == 0.0
                else "N/A",
                format(j.deflections[1] * pow(10, 3), ".5f")
                if j.translation[1] == 0.0
                else "N/A",
                format(j.deflections[2] * pow(10, 3), ".5f")
                if j.translation[2] == 0.0
                else "N/A",
                "Yes"
                if numpy.linalg.norm(j.deflections) < the_truss.maximum_deflection
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
