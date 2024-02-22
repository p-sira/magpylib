"""
Implementations of analytical expressions for the magnetic field of
a circular current loop. Computation details in function docstrings.
"""
import warnings

import numpy as np
from scipy.constants import mu_0 as MU0

from magpylib._src.fields.special_cel import cel_iter
from magpylib._src.input_checks import check_field_input
from magpylib._src.utility import cart_to_cyl_coordinates
from magpylib._src.utility import cyl_field_to_cart


# CORE
def current_circle_Hfield(
    r0: np.ndarray,
    r: np.ndarray,
    z: np.ndarray,
    i0: np.ndarray,
) -> np.ndarray:
    """B-field of a circular line-current loops in Cylindrical Coordinates.

    The loops lies in the z=0 plane with the coordinate origin at their centers.
    The output is proportional to the electrical currents i0, and independent of
    the length units chosen for observers and loop radii.

    Parameters
    ----------
    r0: ndarray, shape (n)
        Radii of loops.

    r: ndarray, shape (n)
        Radial positions of observers.

    z: ndarray, shape (n)
        Axial positions of observers.

    i0: ndarray, shape (n)
        Electrical currents.

    Returns
    -------
    B-field: ndarray, shape (n,3)
        B-field generated by Loops at observer positions.

    Notes
    -----
    Implementation based on "Numerically stable and computationally
    efficient expression for the magnetic field of a current loop.", M.Ortner et al,
    Magnetism 2023, 3(1), 11-31.
    """
    n5 = len(r)

    # express through ratios (make dimensionless, avoid large/small input values, stupid)
    r = r / r0
    z = z / r0

    # field computation from paper
    z2 = z**2
    x0 = z2 + (r + 1) ** 2
    k2 = 4 * r / x0
    q2 = (z2 + (r - 1) ** 2) / x0

    k = np.sqrt(k2)
    q = np.sqrt(q2)
    p = 1 + q
    pf = k / np.sqrt(r) / q2 / 20 / r0 * 1e-6 * i0

    # cel* part
    cc = k2 * k2
    ss = 2 * cc * q / p
    Hr = pf * z / r * cel_iter(q, p, np.ones(n5), cc, ss, p, q)

    # cel** part
    cc = k2 * (k2 - (q2 + 1) / r)
    ss = 2 * k2 * q * (k2 / p - p / r)
    Hz = -pf * cel_iter(q, p, np.ones(n5), cc, ss, p, q)

    # input is I -> output must be H-field
    return np.row_stack((Hr, np.zeros(n5), Hz)) * 795774.7154594767  # *1e7/4/np.pi


def BHJM_circle(
    field: str,
    observers: np.ndarray,
    diameter: np.ndarray,
    current: np.ndarray,
) -> np.ndarray:
    """
    translate circle fields to BHJM
    - treat special cases
    """

    # allocate
    BHJM = np.zeros_like(observers, dtype=float)

    check_field_input(field)
    if field in "MJ":
        return BHJM

    r, phi, z = cart_to_cyl_coordinates(observers)
    r0 = np.abs(diameter / 2)

    # Special cases:
    # case1: loop radius is 0 -> return (0,0,0)
    mask1 = r0 == 0
    # case2: at singularity -> return (0,0,0)
    mask2 = np.logical_and(abs(r - r0) < 1e-15 * r0, z == 0)
    # case3: r=0
    mask3 = r == 0
    if np.any(mask3):
        mask4 = mask3 * ~mask1  # only relevant if not also case1
        BHJM[mask4, 2] = (
            (r0[mask4] ** 2 / (z[mask4] ** 2 + r0[mask4] ** 2) ** (3 / 2))
            * current[mask4]
            * 0.5
        )

    # general case
    mask5 = ~np.logical_or(np.logical_or(mask1, mask2), mask3)
    if np.any(mask5):
        BHJM[mask5] = current_circle_Hfield(
            r0=r0[mask5],
            r=r[mask5],
            z=z[mask5],
            i0=current[mask5],
        ).T

    BHJM[:, 0], BHJM[:, 1] = cyl_field_to_cart(phi, BHJM[:, 0])

    if field == "H":
        return BHJM

    if field == "B":
        return BHJM * MU0

    raise ValueError(  # pragma: no cover
        "`output_field_type` must be one of ('B', 'H', 'M', 'J'), " f"got {field!r}"
    )
