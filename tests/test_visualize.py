import warnings

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure

from tests.helpers import build_triangle_truss
from trussme.visualize import plot_truss


def test_plot_truss_returns_figure_for_default_shape() -> None:
    truss = build_triangle_truss()
    truss.analyze()

    figure = plot_truss(truss, starting_shape="k", deflected_shape=None)

    assert isinstance(figure, Figure)
    assert figure.axes


def test_plot_truss_supports_factor_of_safety_colors() -> None:
    truss = build_triangle_truss()
    truss.analyze()

    figure = plot_truss(truss, starting_shape="fos", deflected_shape="fos")

    assert isinstance(figure, Figure)
    assert figure.axes


def test_plot_truss_supports_force_coloring() -> None:
    truss = build_triangle_truss()
    truss.analyze()

    figure = plot_truss(truss, starting_shape="force", deflected_shape="force")

    assert isinstance(figure, Figure)
    assert figure.axes


def test_plot_truss_supports_force_coloring_with_zero_forces() -> None:
    truss = build_triangle_truss()

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        figure = plot_truss(truss, starting_shape="force", deflected_shape="force")

    runtime_warnings = [
        warning for warning in captured if issubclass(warning.category, RuntimeWarning)
    ]

    assert isinstance(figure, Figure)
    assert figure.axes
    assert not runtime_warnings


def test_plot_truss_allows_hidden_shapes() -> None:
    truss = build_triangle_truss()
    truss.analyze()

    figure = plot_truss(truss, starting_shape=None, deflected_shape=None)

    assert isinstance(figure, Figure)
    assert figure.axes
