"""
Implementations of analytical expressions for the magnetic field of homogeneously
magnetized Cuboids. Computation details in function docstrings.
"""
import numpy as np
from scipy.constants import mu_0 as MU0

from magpylib._src.input_checks import check_field_input

# pylint: disable=too-many-statements


# CORE
def magnet_cuboid_Bfield(
    observers: np.ndarray,
    dimensions: np.ndarray,
    polarizations: np.ndarray,
):
    """B-field of homogeneously magnetized cuboids in Cartesian Coordinates.

    The cuboids sides are parallel to the coordinate axes. The geometric centers of the
    cuboids lie in the origin. The output is proportional to the polarization magnitude
    and independent of the length units chosen for observers and dimensions.

    Parameters
    ----------
    observers: ndarray, shape (n,3)
        Observer positions (x,y,z) in Cartesian coordinates.

    dimensions: ndarray, shape (n,3)
        Length of cuboids sides.

    polarizations: ndarray, shape (n,3)
        Magnetic polarization vectors.

    Returns
    -------
    B-Field: ndarray, shape (n,3)
        B-field generated by Cuboids at observer positions.

    Notes
    -----
    Field computations via magnetic surface charge density. Published
    several times with similar expressions:

    Yang: Superconductor Science and Technology 3(12):591 (1999)

    Engel-Herbert: Journal of Applied Physics 97(7):074504 - 074504-4 (2005)

    Camacho: Revista Mexicana de Fisica E 59 (2013) 8-17

    Avoiding indeterminate forms:

    In the above implementations there are several indeterminate forms
    where the limit must be taken. These forms appear at positions
    that are extensions of the edges in all xyz-octants except bottQ4.
    In the vicinity of these indeterminate forms the formula becomes
    numerically instable.

    Chosen solution: use symmetries of the problem to change all
    positions to their bottQ4 counterparts. see also

    Cichon: IEEE Sensors Journal, vol. 19, no. 7, April 1, 2019, p.2509
    """
    pol_x, pol_y, pol_z = polarizations.T
    a, b, c = dimensions.T / 2
    x, y, z = np.copy(observers).T

    # avoid indeterminate forms by evaluating in bottQ4 only --------
    # basic masks
    maskx = x < 0
    masky = y > 0
    maskz = z > 0

    # change all positions to their bottQ4 counterparts
    x[maskx] = x[maskx] * -1
    y[masky] = y[masky] * -1
    z[maskz] = z[maskz] * -1

    # create sign flips for position changes
    qsigns = np.ones((len(pol_x), 3, 3))
    qs_flipx = np.array([[1, -1, -1], [-1, 1, 1], [-1, 1, 1]])
    qs_flipy = np.array([[1, -1, 1], [-1, 1, -1], [1, -1, 1]])
    qs_flipz = np.array([[1, 1, -1], [1, 1, -1], [-1, -1, 1]])
    # signs flips can be applied subsequently
    qsigns[maskx] = qsigns[maskx] * qs_flipx
    qsigns[masky] = qsigns[masky] * qs_flipy
    qsigns[maskz] = qsigns[maskz] * qs_flipz

    # field computations --------------------------------------------
    # Note: in principle the computation for all three polarization-components can be
    #   vectorized itself using symmetries. However, tiling the three
    #   components will cost more than is gained by the vectorized evaluation

    # Note: making the following computation steps is not necessary
    #   as mkl will cache such small computations
    xma, xpa = x - a, x + a
    ymb, ypb = y - b, y + b
    zmc, zpc = z - c, z + c

    xma2, xpa2 = xma**2, xpa**2
    ymb2, ypb2 = ymb**2, ypb**2
    zmc2, zpc2 = zmc**2, zpc**2

    mmm = np.sqrt(xma2 + ymb2 + zmc2)
    pmp = np.sqrt(xpa2 + ymb2 + zpc2)
    pmm = np.sqrt(xpa2 + ymb2 + zmc2)
    mmp = np.sqrt(xma2 + ymb2 + zpc2)
    mpm = np.sqrt(xma2 + ypb2 + zmc2)
    ppp = np.sqrt(xpa2 + ypb2 + zpc2)
    ppm = np.sqrt(xpa2 + ypb2 + zmc2)
    mpp = np.sqrt(xma2 + ypb2 + zpc2)

    with np.errstate(divide="ignore", invalid="ignore"):
        ff2x = np.log((xma + mmm) * (xpa + ppm) * (xpa + pmp) * (xma + mpp)) - np.log(
            (xpa + pmm) * (xma + mpm) * (xma + mmp) * (xpa + ppp)
        )

        ff2y = np.log(
            (-ymb + mmm) * (-ypb + ppm) * (-ymb + pmp) * (-ypb + mpp)
        ) - np.log((-ymb + pmm) * (-ypb + mpm) * (ymb - mmp) * (ypb - ppp))

        ff2z = np.log(
            (-zmc + mmm) * (-zmc + ppm) * (-zpc + pmp) * (-zpc + mpp)
        ) - np.log((-zmc + pmm) * (zmc - mpm) * (-zpc + mmp) * (zpc - ppp))

    ff1x = (
        np.arctan2((ymb * zmc), (xma * mmm))
        - np.arctan2((ymb * zmc), (xpa * pmm))
        - np.arctan2((ypb * zmc), (xma * mpm))
        + np.arctan2((ypb * zmc), (xpa * ppm))
        - np.arctan2((ymb * zpc), (xma * mmp))
        + np.arctan2((ymb * zpc), (xpa * pmp))
        + np.arctan2((ypb * zpc), (xma * mpp))
        - np.arctan2((ypb * zpc), (xpa * ppp))
    )

    ff1y = (
        np.arctan2((xma * zmc), (ymb * mmm))
        - np.arctan2((xpa * zmc), (ymb * pmm))
        - np.arctan2((xma * zmc), (ypb * mpm))
        + np.arctan2((xpa * zmc), (ypb * ppm))
        - np.arctan2((xma * zpc), (ymb * mmp))
        + np.arctan2((xpa * zpc), (ymb * pmp))
        + np.arctan2((xma * zpc), (ypb * mpp))
        - np.arctan2((xpa * zpc), (ypb * ppp))
    )

    ff1z = (
        np.arctan2((xma * ymb), (zmc * mmm))
        - np.arctan2((xpa * ymb), (zmc * pmm))
        - np.arctan2((xma * ypb), (zmc * mpm))
        + np.arctan2((xpa * ypb), (zmc * ppm))
        - np.arctan2((xma * ymb), (zpc * mmp))
        + np.arctan2((xpa * ymb), (zpc * pmp))
        + np.arctan2((xma * ypb), (zpc * mpp))
        - np.arctan2((xpa * ypb), (zpc * ppp))
    )

    # contributions from x-polarization
    #    the 'missing' third sign is hidden in ff1x
    bx_pol_x = pol_x * ff1x * qsigns[:, 0, 0]
    by_pol_x = pol_x * ff2z * qsigns[:, 0, 1]
    bz_pol_x = pol_x * ff2y * qsigns[:, 0, 2]
    # contributions from y-polarization
    bx_pol_y = pol_y * ff2z * qsigns[:, 1, 0]
    by_pol_y = pol_y * ff1y * qsigns[:, 1, 1]
    bz_pol_y = -pol_y * ff2x * qsigns[:, 1, 2]
    # contributions from z-polarization
    bx_pol_z = pol_z * ff2y * qsigns[:, 2, 0]
    by_pol_z = -pol_z * ff2x * qsigns[:, 2, 1]
    bz_pol_z = pol_z * ff1z * qsigns[:, 2, 2]

    # summing all contributions
    bx_tot = bx_pol_x + bx_pol_y + bx_pol_z
    by_tot = by_pol_x + by_pol_y + by_pol_z
    bz_tot = bz_pol_x + bz_pol_y + bz_pol_z

    # B = np.c_[bx_tot, by_tot, bz_tot]      # faster for 10^5 and more evaluations
    B = np.concatenate(((bx_tot,), (by_tot,), (bz_tot,)), axis=0).T

    B /= 4 * np.pi
    return B


def BHJM_magnet_cuboid(
    field: str,
    observers: np.ndarray,
    dimension: np.ndarray,
    polarization: np.ndarray,
) -> np.ndarray:
    """
    translate cuboid field to BHJM
    - treat special cases
    - inside-outside checks
    """

    RTOL_SURFACE = 1e-15  # relative distance tolerance to be considered on surface

    check_field_input(field)

    pol_x, pol_y, pol_z = polarization.T
    a, b, c = np.abs(dimension.T) / 2
    x, y, z = observers.T

    # allocate for output
    BHJM = polarization.astype(float)

    # SPECIAL CASE 1: polarization = (0,0,0)
    mask_pol_not_null = ~(
        (pol_x == 0) * (pol_y == 0) * (pol_z == 0)
    )  # 2x faster than np.all()

    # SPECIAL CASE 2: 0 in dimension
    mask_dim_not_null = (a * b * c).astype(bool)

    # SPECIAL CASE 3: observer lies on-edge/corner
    #   EPSILON to account for numerical imprecision when e.g. rotating
    #   /a /b /c to account for the missing scaling (EPSILON is large when
    #    a is e.g. EPSILON itself)

    # on-surface is not a special case
    mask_surf_x = abs(x_dist := abs(x) - a) < RTOL_SURFACE * a  # on surface
    mask_surf_y = abs(y_dist := abs(y) - b) < RTOL_SURFACE * b  # on surface
    mask_surf_z = abs(z_dist := abs(z) - c) < RTOL_SURFACE * c  # on surface

    # inside-outside
    mask_inside_x = x_dist < RTOL_SURFACE * a
    mask_inside_y = y_dist < RTOL_SURFACE * b
    mask_inside_z = z_dist < RTOL_SURFACE * c
    mask_inside = mask_inside_x & mask_inside_y & mask_inside_z

    # on edge (requires on-surface and inside-outside)
    mask_xedge = mask_surf_y & mask_surf_z & mask_inside_x
    mask_yedge = mask_surf_x & mask_surf_z & mask_inside_y
    mask_zedge = mask_surf_x & mask_surf_y & mask_inside_z
    mask_not_edge = ~(mask_xedge | mask_yedge | mask_zedge)

    mask_gen = mask_pol_not_null & mask_dim_not_null & mask_not_edge

    if field == "J":
        BHJM[~mask_inside] = 0
        return BHJM

    if field == "M":
        BHJM[~mask_inside] = 0
        return BHJM / MU0

    BHJM *= 0  # return (0,0,0) for all special cases
    BHJM[mask_gen] = magnet_cuboid_Bfield(
        observers=observers[mask_gen],
        dimensions=dimension[mask_gen],
        polarizations=polarization[mask_gen],
    )
    if field == "B":
        return BHJM

    if field == "H":
        BHJM[mask_inside] -= polarization[mask_inside]
        return BHJM / MU0

    raise ValueError(  # pragma: no cover
        "`output_field_type` must be one of ('B', 'H', 'M', 'J'), " f"got {field!r}"
    )
