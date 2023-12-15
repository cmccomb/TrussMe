import numpy
import pandas
import trussme.physical_properties as pp
from trussme.truss import Truss


def print_summary(f, the_truss: Truss, verbose: bool = False):
    pw(f, "\n", v=verbose)
    pw(f, "(0) SUMMARY OF ANALYSIS", v=verbose)
    pw(f, "=============================", v=verbose)
    pw(f, "\t- The truss has a mass of "
          + format(the_truss.mass, '.2f')
          + " kg, and a total factor of safety of "
          + format(the_truss.fos_total, '.2f')
          + ". ", v=verbose)
    pw(f, "\t- The limit state is " + the_truss.limit_state + ".", v=verbose)

    if the_truss.THERE_ARE_GOALS:
        success_string = []
        failure_string = []
        for key in the_truss.goals.keys():
            if key is "min_fos_total" and the_truss.goals[key] is not -1:
                if the_truss.goals[key] < the_truss.fos_total:
                    success_string.append("total FOS")
                else:
                    failure_string.append("total FOS")
            elif key is "min_fos_buckling" and the_truss.goals[key] is not -1:
                if the_truss.goals[key] < the_truss.fos_buckling:
                    success_string.append("buckling FOS")
                else:
                    failure_string.append("buckling FOS")
            elif key is "min_fos_yielding" and the_truss.goals[key] is not -1:
                if the_truss.goals[key] < the_truss.fos_yielding:
                    success_string.append("yielding FOS")
                else:
                    failure_string.append("yielding FOS")
            elif key is "max_mass" and the_truss.goals[key] is not -1:
                if the_truss.goals[key] > the_truss.mass:
                    success_string.append("mass")
                else:
                    failure_string.append("mass")
            elif key is "max_deflection" and the_truss.goals[key] is not -1:
                if the_truss.goals[key] > the_truss.fos_total:
                    success_string.append("deflection")
                else:
                    failure_string.append("deflection")

        if len(success_string) is not 0:
            if len(success_string) is 1:
                pw(f, "\t- The design goal for " + str(success_string[0])
                      + " was satisfied.", v=verbose)
            elif len(success_string) is 2:
                pw(f, "\t- The design goals for "
                      + str(success_string[0])
                      + " and "
                      + str(success_string[1])
                      + " were satisfied.", v=verbose)
            else:
                pw(f, "\t- The design goals for ", nl=False, v=verbose)
                for st in success_string[0:-1]:
                    pw(f, st+", ", nl=False, v=verbose)
                pw(f, "and "+str(success_string[-1])+" were satisfied.", v=verbose)

        if len(failure_string) is not 0:
            if len(failure_string) is 1:
                pw(f, "\t- The design goal for " + str(failure_string[0])
                      + " was not satisfied.", v=verbose)
            elif len(failure_string) is 2:
                pw(f, "\t- The design goals for "
                      + str(failure_string[0])
                      + " and "
                      + str(failure_string[1])
                      + " were not satisfied.", v=verbose)
            else:
                pw(f, "\t- The design goals for", nl=False, v=verbose)
                for st in failure_string[0:-1]:
                    pw(f, st+",", nl=False, v=verbose)
                pw(f, "and "+str(failure_string[-1])+" were not satisfied.", v=verbose)


def print_instantiation_information(f, the_truss, verbose=False):
    pw(f, "\n", v=verbose)
    pw(f, "(1) INSTANTIATION INFORMATION", v=verbose)
    pw(f, "=============================", v=verbose)

    # Print joint information
    pw(f, "\n--- JOINTS ---", v=verbose)
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_"+"{0:02d}".format(j.idx))
        data.append([str(j.coordinates[0]),
                     str(j.coordinates[1]),
                     str(j.coordinates[2]),
                     str(bool(j.translation[0][0])),
                     str(bool(j.translation[1][0])),
                     str(bool(j.translation[2][0]))])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["X",
                                    "Y",
                                    "Z",
                                    "X-Support",
                                    "Y-Support",
                                    "Z-Support"])
        .to_string(justify="left"), v=verbose)

    # Print member information
    pw(f, "\n--- MEMBERS ---", v=verbose)
    data = []
    rows = []
    for m in the_truss.members:
        rows.append("Member_"+"{0:02d}".format(m.idx))
        data.append([str(m.joints[0].idx),
                     str(m.joints[1].idx),
                     m.material,
                     m.shape,
                     m.h,
                     m.w,
                     m.r,
                     m.t])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["Joint-A",
                                    "Joint-B",
                                    "Material",
                                    "Shape",
                                    "Height(m)",
                                    "Width(m)",
                                    "Radius(m)",
                                    "Thickness(m)"])
        .to_string(justify="left"), v=verbose)

    # Print material list
    unique_materials = list({v['name']:v for v in the_truss.materials}.values())
    pw(f, "\n--- MATERIALS ---", v=verbose)
    data = []
    rows = []
    for mat in unique_materials:
        rows.append(mat["name"])
        data.append([
            str(mat["rho"]),
            str(mat["E"]/pow(10, 9)),
            str(mat["Fy"]/pow(10, 6))])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["Density(kg/m3)",
                                    "Elastic Modulus(GPa)",
                                    "Yield Strength(MPa)"])
        .to_string(justify="left"), v=verbose)


def print_stress_analysis(f, the_truss, verbose=False):
    pw(f, "\n", v=verbose)
    pw(f, "(2) STRESS ANALYSIS INFORMATION", v=verbose)
    pw(f, "===============================", v=verbose)

    # Print information about loads
    pw(f, "\n--- LOADING ---", v=verbose)
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_"+"{0:02d}".format(j.idx))
        data.append([str(j.loads[0][0]/pow(10, 3)),
                     format((j.loads[1][0]
                             - sum([m.mass/2.0*pp.g for m
                                    in j.members]))/pow(10, 3), '.2f'),
                     str(j.loads[2][0]/pow(10, 3))])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["X-Load",
                                    "Y-Load",
                                    "Z-Load"])
        .to_string(justify="left"), v=verbose)

    # Print information about reactions
    pw(f, "\n--- REACTIONS ---", v=verbose)
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_"+"{0:02d}".format(j.idx))
        data.append([format(j.reactions[0][0]/pow(10, 3), '.2f')
                     if j.translation[0][0] != 0.0 else "N/A",
                     format(j.reactions[1][0]/pow(10, 3), '.2f')
                     if j.translation[1][0] != 0.0 else "N/A",
                     format(j.reactions[2][0]/pow(10, 3), '.2f')
                     if j.translation[2][0] != 0.0 else "N/A"])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["X-Reaction(kN)",
                                    "Y-Reaction(kN)",
                                    "Z-Reaction(kN)"])
        .to_string(justify="left"), v=verbose)

    # Print information about members
    pw(f, "\n--- FORCES AND STRESSES ---", v=verbose)
    data = []
    rows = []
    for m in the_truss.members:
        rows.append("Member_"+"{0:02d}".format(m.idx))
        data.append([m.area,
                     format(m.I, '.2e'),
                     format(m.force/pow(10, 3), '.2f'),
                     m.fos_yielding,
                     m.fos_buckling if m.fos_buckling > 0 else "N/A"])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["Area(m2)",
                                    "Moment-of-Inertia(m4)",
                                    "Axial-force(kN)",
                                    "FOS-yielding",
                                    "FOS-buckling"])
        .to_string(justify="left"), v=verbose)

    # Print information about members
    pw(f, "\n--- DEFLECTIONS ---", v=verbose)
    data = []
    rows = []
    for j in the_truss.joints:
        rows.append("Joint_"+"{0:02d}".format(j.idx))
        data.append([format(j.deflections[0][0]*pow(10, 3), '.5f')
                     if j.translation[0][0] == 0.0 else "N/A",
                     format(j.deflections[1][0]*pow(10, 3), '.5f')
                     if j.translation[1][0] == 0.0 else "N/A",
                     format(j.deflections[2][0]*pow(10, 3), '.5f')
                     if j.translation[2][0] == 0.0 else "N/A"])

    pw(f, pandas.DataFrame(data,
                           index=rows,
                           columns=["X-Defl.(mm)",
                                    "Y-Defl.(mm)",
                                    "Z-Defl.(mm)"])
        .to_string(justify="left"), v=verbose)


def print_recommendations(f, the_truss, verbose=False):
    made_a_recommendation = False
    pw(f, "\n", v=verbose)
    pw(f, "(3) RECOMMENDATIONS", v=verbose)
    pw(f, "===============================", v=verbose)

    if the_truss.goals["max_mass"] is not -1:
        tm = the_truss.goals["max_mass"]
    else:
        tm = numpy.inf

    for m in the_truss.members:
        if the_truss.goals["min_fos_yielding"] is not -1:
            tyf = the_truss.goals["min_fos_yielding"]
        else:
            tyf = 1.0

        if the_truss.goals["min_fos_buckling"] is not -1:
            tbf = the_truss.goals["min_fos_buckling"]
        else:
            tbf = 1.0

        if m.fos_yielding < tyf:
            pw(f, "\t- Member_"+'{0:02d}'.format(m.idx)+" is yielding. "
                  "Try increasing the cross-sectional area.", v=verbose)
            pw(f, "\t\t- Current area: " + format(m.I, '.2e') + " m^2", v=verbose)
            pw(f, "\t\t- Recommended area: "
                  + format(m.area*the_truss.goals["min_fos_yielding"]
                           / m.fos_yielding, '.2e') + " m^2", v=verbose)
            pw(f, "\t\t- Try increasing member dimensions by a factor of "
                  "at least " + format(pow(the_truss.goals["min_fos_yielding"]
                                           / m.fos_yielding, 0.5), '.3f'), v=verbose)
            made_a_recommendation = True

        if 0 < m.fos_buckling < tbf:
            pw(f, "\t- Member_"+'{0:02d}'.format(m.idx)+" is buckling. "
                  "Try increasing the moment of inertia.", v=verbose)
            pw(f, "\t\t- Current moment of inertia: "
                  + format(m.I, '.2e') + " m^4", v=verbose)
            pw(f, "\t\t- Recommended moment of inertia: "
                  + format(m.I*the_truss.goals["min_fos_buckling"]
                           / m.fos_buckling, '.2e') + " m^4", v=verbose)
            pw(f, "\t\t- Try increasing member dimensions by a factor of "
                  "at least " + format(pow(the_truss.goals["min_fos_buckling"]
                                           / m.fos_buckling, 0.25), '.3f')
                  + ".", v=verbose)
            made_a_recommendation = True

        if m.fos_buckling > tbf \
                and m.fos_yielding > tyf \
                and the_truss.mass > tm:
            if the_truss.mass > the_truss.goals["max_mass"]:
                pw(f, "\t- Member_"+'{0:02d}'.format(m.idx)+" is strong "
                      "enough, so try decreasing the cross-sectional area "
                      "to decrease mass.", v=verbose)
            made_a_recommendation = True

    for j in the_truss.joints:
        if the_truss.goals["max_deflection"] is not -1:
            td = the_truss.goals["max_deflection"]
        else:
            td = numpy.inf

        if numpy.linalg.norm(j.deflections) > td:
            pw(f, "\t- Joint_"+'{0:02d}'.format(j.idx)+" is deflecting "
                  "excessively. Try increasing the cross-sectional area of "
                  "adjacent members. These include:", v=verbose)
            for m in j.members:
                pw(f, "\t\t- Member_"+'{0:02d}'.format(m.idx), v=verbose)

    if not made_a_recommendation:
        pw(f, "No recommendations. All design goals met.", v=verbose)


def pw(f, string, nl=True, v=False):
    if nl is False:
        if v is True:
            print(string),
        if f is not "":
            f.write(string)
    elif nl is True:
        if v is True:
            print(string)
        if f is not "":
            f.write(string+"\n")