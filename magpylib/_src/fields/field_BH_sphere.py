"""
Implementations of analytical expressions for the magnetic field of homogeneously
magnetized Spheres. Computation details in function docstrings.
"""
import numpy as np

from magpylib._src.input_checks import check_field_input
from magpylib._src.utility import MU0


def magnet_sphere_Bfield(
    *,
    observers: np.ndarray,
    diameters: np.ndarray,
    polarizations: np.ndarray,
) -> np.ndarray:
    """Magnetic field of homogeneously magnetized spheres.

    The center of the sphere lies in the origin of the coordinate system. The output
    is proportional to the polarization magnitude, and independent of the length
    units chosen for observers and diameters

    Parameters
    ----------
    observers: ndarray, shape (n,3)
        Observer positions (x,y,z) in Cartesian coordinates.

    diameters: ndarray, shape (n,)
        Sphere diameters.

    polarizations: ndarray, shape (n,3)
        Magnetic polarization vectors.

    Returns
    -------
    B-field or H-field: ndarray, shape (n,3)
        B-field generated by Spheres at observer positions.

    Notes
    -----
    The field corresponds to a dipole field on the outside and is 2/3*mag
    in the inside (see e.g. "Theoretical Physics, Bertelmann").
    """
    return BHJM_magnet_sphere(
        field="B",
        observers=observers,
        diameter=diameters,
        polarization=polarizations,
    )


def BHJM_magnet_sphere(
    *,
    field: str,
    observers: np.ndarray,
    diameter: np.ndarray,
    polarization: np.ndarray,
    in_out="auto",
) -> np.ndarray:
    """
    magnet sphere field, cannot be moved to core function, because
    core computation requires inside-outside check, but BHJM translation also.
    Would require 2 checks, or forwarding the masks ... both not ideal
    """
    check_field_input(field)

    x, y, z = np.copy(observers.T)
    r = np.sqrt(x**2 + y**2 + z**2)  # faster than np.linalg.norm
    r_sphere = abs(diameter) / 2

    # inside field & allocate
    BHJM = polarization.astype(float) * 2 / 3
    out = r > r_sphere

    if field == "J":
        BHJM[out] = 0.0
        return BHJM

    if field == "M":
        BHJM[out] = 0.0
        return BHJM / MU0

    BHJM[out] = (
        (
            3 * np.sum(polarization[out] * observers[out], axis=1) * observers[out].T
            - polarization[out].T * r[out] ** 2
        )
        / r[out] ** 5
        * r_sphere**3
        / 3
    ).T

    if field == "B":
        return BHJM

    if field == "H":
        BHJM[~out] -= polarization[~out]
        return BHJM / MU0

    raise ValueError(  # pragma: no cover
        "`output_field_type` must be one of ('B', 'H', 'M', 'J'), " f"got {field!r}"
    )
