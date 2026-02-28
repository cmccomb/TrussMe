import trussme

from tests.helpers import build_triangle_truss, default_goals


def test_report_to_md_writes_file(tmp_path) -> None:
    truss = build_triangle_truss()
    output_path = tmp_path / "report.md"

    trussme.report_to_md(str(output_path), truss, default_goals())

    assert output_path.exists()
    assert "# SUMMARY OF ANALYSIS" in output_path.read_text()


def test_print_report_writes_summary(capsys) -> None:
    truss = build_triangle_truss()

    trussme.print_report(truss, default_goals())

    captured = capsys.readouterr()
    assert "# SUMMARY OF ANALYSIS" in captured.out
    assert "The truss has a mass of" in captured.out


def test_report_to_str_without_figures_omits_svg() -> None:
    truss = build_triangle_truss()

    report = trussme.report_to_str(truss, default_goals(), with_figures=False)

    assert "# SUMMARY OF ANALYSIS" in report
    assert "<svg" not in report


def test_report_summary_single_success_and_multi_failure_wording() -> None:
    truss = build_triangle_truss()
    truss.analyze()
    goals = trussme.Goals(
        minimum_fos_buckling=truss.fos_buckling + 1.0,
        minimum_fos_yielding=truss.fos_yielding + 1.0,
        maximum_mass=truss.mass + 1.0,
        maximum_deflection=max(truss.deflection - 1e-6, 0.0),
    )

    report = trussme.report_to_str(truss, goals, with_figures=False)

    assert "The design goal for mass was satisfied." in report
    assert "buckling FOS,yielding FOS,and deflection were not satisfied." in report


def test_report_summary_multi_success_wording() -> None:
    truss = build_triangle_truss()
    truss.analyze()
    goals = trussme.Goals(
        minimum_fos_buckling=truss.fos_buckling - 0.1,
        minimum_fos_yielding=truss.fos_yielding - 0.1,
        maximum_mass=truss.mass + 1.0,
        maximum_deflection=truss.deflection + 1.0,
    )

    report = trussme.report_to_str(truss, goals, with_figures=False)

    assert "buckling FOS, yielding FOS, mass, and deflection were satisfied." in report
