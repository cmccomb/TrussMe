# trussme

`trussme` is a Python library for building, analyzing, and optimizing truss structures.

## Installation

`trussme` supports Python 3.10 and newer.

```bash
pip install trussme
```

The package depends on `numpy`, `scipy`, `pandas`, `matplotlib`, and `tabulate` at runtime.

## Quick Start

```python
import trussme

truss = trussme.Truss()
pin = truss.add_pinned_joint([0.0, 0.0, 0.0])
free = truss.add_free_joint([2.5, 2.5, 0.0])
roller = truss.add_roller_joint([5.0, 0.0, 0.0])

truss.add_member(pin, free)
truss.add_member(pin, roller)
truss.add_member(roller, free)

truss.add_out_of_plane_support("z")
truss.set_load(free, [0.0, -10000.0, 0.0])

truss.analyze()

print(truss.fos)
print(truss.mass)
```

## Built-in Materials

Trussme ships with a small library of common engineering materials. Each record
includes a `source` URL citing where the mechanical properties originate.

- A36_Steel - https://en.wikipedia.org/wiki/A36_steel
- A992_Steel - https://en.wikipedia.org/wiki/ASTM_A992
- 304_Stainless_Steel - https://en.wikipedia.org/wiki/SAE_304_stainless_steel
- 2024_T3_Aluminum - https://en.wikipedia.org/wiki/2024_aluminium_alloy
- 6061_T6_Aluminum - https://en.wikipedia.org/wiki/6061_aluminium_alloy
- 7075_T6_Aluminum - https://en.wikipedia.org/wiki/7075_aluminium_alloy
- Ti_6Al_4V_Titanium - https://en.wikipedia.org/wiki/Ti-6Al-4V

Custom materials must also provide a provenance `source` when added to a truss.

## Project Links

- Source: [GitHub](https://github.com/cmccomb/TrussMe)
- Issues: [GitHub Issues](https://github.com/cmccomb/TrussMe/issues)
- Release Guide: [RELEASING.md](RELEASING.md)

## License

This project is released under the MIT License.

## Directional buckling and self-weight (0.2)

Self-weight remains **enabled by default**. Each member contributes half its
mass times gravity to each endpoint. `truss.set_gravity((0, 0, 0))` disables it;
any finite acceleration vector is supported. The default is `(0, -9.80665, 0)`
m/s². `truss.nodal_loads` includes external loads and member weight, and reactions
now use `K u - f`, including loads at supports.

Buckling now checks **both transverse directions**. The lower Euler capacity
governs by default, including for rectangular sections. Configure orientation
and effective lengths explicitly when they matter:

```python
truss.set_member_buckling(0, trussme.BucklingSettings(
    transverse_reference=(0, 0, 1),
    effective_length_factors=(1.0, 0.4),
))
truss.analyze()
for mode in truss.members[0].buckling_modes:
    print(mode.direction, mode.effective_length, mode.critical_load,
          mode.factor_of_safety)
print(truss.members[0].governing_buckling)
```

The first direction is the reference projected perpendicular to the member. For
a rectangle it corresponds to the height, with inertia `w*h**3/12`; the second is
the member direction crossed with the first. An omitted reference uses the
least-aligned global axis. Each mode uses `Pcr = pi**2*E*I/(K*L)**2`. Equal
capacities have no unique governing direction; the first is returned consistently.
Planar joint restraints do not suppress out-of-plane member buckling.

K factors represent caller-supplied bracing or end conditions. They add no actual
brace, mass, or stiffness. These are linear axial analyses and Euler member
capacity checks; they do not solve eigenmodes, nonlinear/post-buckling behavior,
or local/torsional buckling. Reports include both directions and assumptions.
`plot_truss(truss, projection="xz", buckling_directions=True)` displays governing
capacity directions; a circle with a dot indicates a direction normal to the view.

Model objects remain mutable: call `analyze()` again after edits before reading
forces, reactions, deflections, or safety factors. Geometry, material properties,
and buckling assumptions are validated before analysis.

## Migration and exchange with trussx

Version 0.2 changes rectangular-section buckling results and optimization
constraint values. `set_buckling_axis("strong")` explicitly reproduces the 0.1
scalar convention when both K values are 1. `Shape.moi()` retains the legacy
scalar inertia; `Shape.principal_inertias()` exposes both. Reports and design
goals always use the physical lower capacity, even in strong compatibility mode.
Existing shape subclasses that only implement `moi()` are treated as isotropic;
override `principal_inertias()` for asymmetric sections.

Native JSON and TRS now preserve gravity, orientation, K factors, and the scalar
convention using the same `trussx` metadata as
[trussx 0.3](https://crates.io/crates/trussx/0.3.0). Both libraries can exchange
pipe, bar, rectangle, box, and `Custom(area, i1, i2)` sections. Arbitrary Python
shape subclasses require caller-defined serialization and sizing logic.

Original files without metadata use the new weak convention in TrussMe 0.2;
trussx imports original files in legacy strong mode. Explicitly select the desired
convention when comparing old files. Native files emitted by either new version
carry that choice. TrussMe 0.1 ignores the metadata and cannot preserve custom
gravity or directional assumptions; trussx's `to_trussme_json()` is the checked
export specifically for that older format.

Optimization helpers now enforce maximum mass and recognize applied loads
componentwise, including `[100, -100, 0]`. Generators own a snapshot of the source
model. The first four constraint residuals are dimensionless, feasible at `<= 0`:
buckling, yielding, deflection, and mass. Minimum safety uses `goal/actual - 1`;
upper limits use `(actual-limit)/max(limit, 1)` in SI units. Infinite upper limits
are disabled (`-1`), with no artificial deflection cap. Full sizing appends `t-r`
for pipes or `2*t-w`, `2*t-h` for boxes, in metres. Invalid or singular trial
models return finite positive design penalties so an optimizer can reject them;
malformed/nonfinite design vectors raise `ValueError`. Custom sections require
caller-defined sizing logic.
