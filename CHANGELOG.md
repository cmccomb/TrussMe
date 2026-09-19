# Changelog

## 0.2.0 — 2026-09-19

TrussMe now shares trussx 0.3's explicit directional buckling and configurable
self-weight model, with reciprocal correctness fixes in reactions and optimization.

- Two transverse Euler capacities per member, global deflection directions,
  section orientation, independent effective length factors, and governing mode.
- Lower directional capacity governs by default. `set_buckling_axis("strong")`
  retains the legacy scalar convention; reports and goals always check both modes.
- Self-weight stays enabled by default. Finite gravity vectors are configurable,
  including zero for applied-load-only models. `nodal_loads` exposes total loads.
- Support reactions include support-applied loads and self-weight (`K u - f`).
- Native JSON/TRS preserve gravity and buckling metadata shared with trussx 0.3;
  explicit custom area/principal-inertia sections round-trip in both libraries.
- TRS preserves nonzero loads whose components sum to zero. Optimization excludes
  these loaded joints from coordinate variables.
- Optimization enforces maximum mass, removes the hidden deflection cap, corrects
  box thickness bounds, preserves source snapshots, and rejects invalid trials.
  Its base constraint vector changes from three raw residuals to four normalized
  residuals; full sizing retains appended wall geometry constraints.
- Analysis validates section dimensions, positive material properties, finite
  loads and geometry, and directional assumptions.
- Reports include both modes, K, effective lengths, critical loads, directions,
  and gravity. Plots support XY/XZ/YZ and governing capacity direction marks.
- Analytical regression tests and frozen cross-language fixtures cover mechanics,
  seven legacy models, directional buckling, exchange, and optimization.

This release supersedes the previously prepared, unpublished 0.1.1 version bump.
Python 3.10+ remains supported. See README migration notes before upgrading.

## 0.1.0

Previous PyPI release with truss construction, linear analysis, self-weight,
scalar safety checks, reports, file exchange, and SciPy optimization helpers.
