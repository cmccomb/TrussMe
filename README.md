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
