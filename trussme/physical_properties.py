from typing import TypedDict


# Gravitational constant for computing weight from mass
g: float = 9.80665


Material = TypedDict("Material", {
        "name": str,
        "rho": float,
        "E": float,
        "Fy": float,
})


# Material properties
MATERIALS: list[Material] = [
    {
        "name": "A36_Steel",
        "rho": 7800.0,
        "E":   200*pow(10, 9),
        "Fy":  250*pow(10, 6)
    },
    {
        "name": "A992_Steel",
        "rho": 7800.0,
        "E":   200*pow(10, 9),
        "Fy":  345*pow(10, 6)
    },
    {
        "name": "6061_T6_Aluminum",
        "rho": 2700.0,
        "E":   68.9*pow(10, 9),
        "Fy":  276*pow(10, 6)
    }
]