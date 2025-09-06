# trussme
A simple truss solver written in Python.

Add joints and members, and vary the material and cross-section of specific members in the truss. There is also an option to create truss from .trs file

Calculate mass, forces, and the factor of safety (FOS) against buckling and yielding. Create a truss analysis report that provides approximate design recommendations

## Built-in materials

Trussme ships with a small library of common engineering materials. Each record
includes a `source` URL citing where the mechanical properties originate.

- A36_Steel – https://en.wikipedia.org/wiki/A36_steel
- A992_Steel – https://en.wikipedia.org/wiki/ASTM_A992
- 304_Stainless_Steel – https://en.wikipedia.org/wiki/SAE_304_stainless_steel
- 2024_T3_Aluminum – https://en.wikipedia.org/wiki/2024_aluminium_alloy
- 6061_T6_Aluminum – https://en.wikipedia.org/wiki/6061_aluminium_alloy
- 7075_T6_Aluminum – https://en.wikipedia.org/wiki/7075_aluminium_alloy
- Ti_6Al_4V_Titanium – https://en.wikipedia.org/wiki/Ti-6Al-4V

Custom materials must also provide a provenance `source` when added to a truss.
