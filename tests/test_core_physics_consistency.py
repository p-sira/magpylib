import numpy as np

import magpylib as magpy
from magpylib._src.fields.field_BH_circle import BHJM_circle
from magpylib._src.fields.field_BH_cuboid import BHJM_magnet_cuboid
from magpylib._src.fields.field_BH_cylinder import BHJM_magnet_cylinder
from magpylib._src.fields.field_BH_cylinder_segment import BHJM_cylinder_segment
from magpylib._src.fields.field_BH_dipole import BHJM_dipole
from magpylib._src.fields.field_BH_polyline import BHJM_polyline
from magpylib._src.fields.field_BH_sphere import magnet_sphere_field
from magpylib._src.fields.field_BH_tetrahedron import magnet_tetrahedron_field
from magpylib._src.fields.field_BH_triangle import triangle_field
from magpylib._src.utility import MU0


# PHYSICS CONSISTENCY TESTING
#
# Magnetic moment of a current loop with current I and surface A:
#   mom = I * A
#
# Magnetic moment of a homogeneous magnet with magnetization mag and volume vol
#   mom = vol * mag
#
# Current replacement picture: A magnet generates a similar field as a current sheet
#   on its surface with current density j = M = J/MU0. Such a current generates
#   the same B-field. The H-field generated by is H-M!
#
# Geometric approximation testing should give similar results for different
# implementations when one geometry is constructed from another
#
# Scaling invariance of solutions
#
# ----------> Circle          # webpage numbers
# Circle   <> Dipole          # mom = I*A (far field approx)
# Polyline <> Dipole          # mom = I*A (far field approx)
# Dipole   <> Sphere          # mom = vol*mag (similar outside of sphere)
# Dipole   <> all Magnets     # mom = vol*mag (far field approx)
# Circle   <> Cylinder        # j = I*N/L == J/MU0 current replacement picture
# Polyline <> Cuboid          # j = I*N/L == J/MU0 current replacement picture
# Circle   <> Polyline        # geometric approx
# Cylinder <> CylinderSegment # geometric approx
# Triangle <> Cuboid          # geometric approx
# Triangle <> Triangle        # geometric approx
# Cuboid   <> Tetrahedron     # geometric approx


# Circle<>Dipole
def test_core_phys_moment_of_current_circle():
    """
    test dipole vs circular current loop
    moment = current * surface
    far field test
    """
    obs = np.array([(10, 20, 30), (-10, -20, 30)])
    dia = np.array([2, 2])
    curr = np.array([1e3, 1e3])
    mom = ((dia / 2) ** 2 * np.pi * curr * np.array([(0, 0, 1)] * 2).T).T

    B1 = BHJM_circle(
        field="B",
        observers=obs,
        diameter=dia,
        current=curr,
    )
    B2 = BHJM_dipole(
        field="B",
        observers=obs,
        moment=mom,
    )
    np.testing.assert_allclose(B1, B2, rtol=1e-02)

    H1 = BHJM_circle(
        field="H",
        observers=obs,
        diameter=dia,
        current=curr,
    )
    H2 = BHJM_dipole(
        field="H",
        observers=obs,
        moment=mom,
    )
    np.testing.assert_allclose(H1, H2, rtol=1e-02)


# Polyline <> Dipole
def test_core_phys_moment_of_current_square():
    """
    test dipole VS square current loop
    moment = I x A, far field test
    """
    obs1 = np.array([(10, 20, 30)])
    obs4 = np.array([(10, 20, 30)] * 4)
    vert = np.array([(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0), (1, 1, 0)])
    curr1 = 1e3
    curr4 = np.array([curr1] * 4)
    mom = (4 * curr1 * np.array([(0, 0, 1)]).T).T

    B1 = BHJM_polyline(
        field="B",
        observers=obs4,
        segment_start=vert[:-1],
        segment_end=vert[1:],
        current=curr4,
    )
    B1 = np.sum(B1, axis=0)
    B2 = BHJM_dipole(
        field="B",
        observers=obs1,
        moment=mom,
    )[0]
    np.testing.assert_allclose(B1, -B2, rtol=1e-03)

    H1 = BHJM_polyline(
        field="H",
        observers=obs4,
        segment_start=vert[:-1],
        segment_end=vert[1:],
        current=curr4,
    )
    H1 = np.sum(H1, axis=0)
    H2 = BHJM_dipole(
        field="H",
        observers=obs1,
        moment=mom,
    )[0]
    np.testing.assert_allclose(H1, -H2, rtol=1e-03)


# Circle <> Polyline
def test_core_phys_circle_polyline():
    """approximate circle with polyline"""
    ts = np.linspace(0, 2 * np.pi, 300)
    vert = np.array([(np.sin(t), np.cos(t), 0) for t in ts])
    curr = np.array([1])
    curr99 = np.array([1] * 299)
    obs = np.array([(1, 2, 3)])
    obs99 = np.array([(1, 2, 3)] * 299)
    dia = np.array([2])

    H1 = BHJM_circle(
        field="H",
        observers=obs,
        diameter=dia,
        current=curr,
    )[0]
    H2 = BHJM_polyline(
        field="H",
        observers=obs99,
        segment_start=vert[:-1],
        segment_end=vert[1:],
        current=curr99,
    )
    H2 = np.sum(H2, axis=0)
    np.testing.assert_allclose(H1, -H2, rtol=1e-4)

    B1 = BHJM_circle(
        field="B",
        observers=obs,
        diameter=dia,
        current=curr,
    )[0]
    B2 = BHJM_polyline(
        field="B",
        observers=obs99,
        segment_start=vert[:-1],
        segment_end=vert[1:],
        current=curr99,
    )
    B2 = np.sum(B2, axis=0)
    np.testing.assert_allclose(B1, -B2, rtol=1e-4)


# Dipole <> Sphere
def test_core_physics_dipole_sphere():
    """
    dipole and sphere field must be similar outside of sphere
    moment = magnetization * volume
    near field tests
    """
    obs = np.array([(1, 2, 3), (-2, -2, -2), (3, 5, -4), (5, 4, 0.1)])
    dia = np.array([2, 3, 0.1, 3.3])
    pol = np.array([(1, 2, 3), (0, 0, 1), (-1, -2, 0), (1, -1, 0.1)])
    mom = np.array([4 * (d / 2) ** 3 * np.pi / 3 * p / MU0 for d, p in zip(dia, pol)])

    B1 = magnet_sphere_field(
        field="B",
        observers=obs,
        diameter=dia,
        polarization=pol,
    )
    B2 = BHJM_dipole(
        field="B",
        observers=obs,
        moment=mom,
    )
    np.testing.assert_allclose(B1, B2, rtol=0, atol=1e-16)

    H1 = magnet_sphere_field(
        field="H",
        observers=obs,
        diameter=dia,
        polarization=pol,
    )
    H2 = BHJM_dipole(
        field="H",
        observers=obs,
        moment=mom,
    )
    np.testing.assert_allclose(H1, H2, rtol=0, atol=1e-10)


# -> Circle, Cylinder
def test_core_physics_long_solenoid():
    """
    Test if field from solenoid converges to long-solenoid field in the center
        Bz_long = MU0*I*N/L
        Hz_long = I*N/L
    I = current, N=windings, L=length, holds true if L >> radius R

    This can also be tested with magnets using the current replacement picture
        where Jz = MU0 * I * N / L, and holds for B and for H-M.
    """

    I = 134
    N = 5000
    R = 1.543
    L = 1234

    for field in ["B", "H"]:
        BHz_long = N * I / L
        if field == "B":
            BHz_long *= MU0

        # SOLENOID TEST constructed from circle fields
        BH = BHJM_circle(
            field=field,
            observers=np.linspace((0, 0, -L / 2), (0, 0, L / 2), N),
            diameter=np.array([2 * R] * N),
            current=np.array([I] * N),
        )
        BH_sol = np.sum(BH, axis=0)[2]

        np.testing.assert_allclose(BHz_long, BH_sol, rtol=1e-3)

        # MAGNET TEST using the current replacement picture
        Mz = I * N / L
        Jz = Mz * MU0
        pol = np.array([(0, 0, Jz)])
        obs = np.array([(0, 0, 0)])

        # cylinder
        BHz_cyl = BHJM_magnet_cylinder(
            field=field,
            observers=obs,
            dimension=np.array([(2 * R, L)]),
            polarization=pol,
        )[0, 2]
        if field == "H":
            BHz_cyl += Mz
        np.testing.assert_allclose(BHz_long, BHz_cyl, rtol=1e-5)

        # cuboid
        BHz_cub = BHJM_magnet_cuboid(
            field=field,
            observers=obs,
            dimension=np.array([(2 * R, 2 * R, L)]),
            polarization=pol,
        )[0, 2]
        if field == "H":
            BHz_cub += Mz
        np.testing.assert_allclose(BHz_long, BHz_cub, rtol=1e-5)


# Circle<>Cylinder
def test_core_physics_current_replacement():
    """
    test if the Cylinder field is given by a replacement current sheet
    that carries a current density of j=magnetization
    It follows:
        j = I*N/L == J/MU0
          -> I = J/MU0/N*L
    near-field test
    """
    L = 0.5
    R = 0.987
    obs = np.array([(1.5, -2, -1.123)])

    Jz = 1
    Hz_cyl = BHJM_magnet_cylinder(
        field="H",
        observers=obs,
        dimension=np.array([(2 * R, L)]),
        polarization=np.array([(0, 0, Jz)]),
    )[0, 2]

    N = 1000  # current discretization
    I = Jz / MU0 / N * L
    H = BHJM_circle(
        field="H",
        observers=np.linspace((0, 0, -L / 2), (0, 0, L / 2), N) + obs,
        diameter=np.array([2 * R] * N),
        current=np.array([I] * N),
    )
    Hz_curr = np.sum(H, axis=0)[2]

    np.testing.assert_allclose(Hz_curr, Hz_cyl, rtol=1e-4)


# Cylinder<>CylinderSegment
def test_core_physics_geometry_cylinder_from_segments():
    """test if multiple Cylinder segments create the same field as fully cylinder"""
    r = 1.23
    h = 3
    obs = np.array([(1, 2, 3), (0.23, 0.132, 0.123)])
    pol = np.array([(2, 0.123, 3), (-0.23, -1, 0.434)])

    B_cyl = BHJM_magnet_cylinder(
        field="B",
        observers=obs,
        dimension=np.array([(2 * r, h)] * 2),
        polarization=pol,
    )
    sections = np.array([-12, 65, 123, 180, 245, 348])

    Bseg = np.zeros((2, 3))
    for phi1, phi2 in zip(sections[:-1], sections[1:]):
        B_part = BHJM_cylinder_segment(
            field="B",
            observers=obs,
            dimension=np.array([(0, r, h, phi1, phi2)] * 2),
            polarization=pol,
        )
        Bseg[0] += B_part[0]
        Bseg[1] += B_part[1]
    np.testing.assert_allclose(B_cyl, Bseg)


# Dipole<>Cuboid, Cylinder, CylinderSegment, Tetrahedron
def test_core_physics_dipole_approximation_magnet_far_field():
    """test if all magnets satisfy the dipole approximation"""
    obs = np.array([(100, 200, 300), (-200, -200, -200)])

    mom = np.array([(1e6, 2e6, 3e6)] * 2)
    Bdip = BHJM_dipole(
        field="H",
        observers=obs,
        moment=mom,
    )

    dim = np.array([(2, 2, 2)] * 2)
    vol = 8
    pol = mom / vol * MU0
    Bcub = BHJM_magnet_cuboid(
        field="H",
        observers=obs,
        dimension=dim,
        polarization=pol,
    )
    np.testing.assert_allclose(Bdip, Bcub)

    dim = np.array([(0.5, 0.5)] * 2)
    vol = 0.25**2 * np.pi * 0.5
    pol = mom / vol * MU0
    Bcyl = BHJM_magnet_cylinder(
        field="H",
        observers=obs,
        dimension=dim,
        polarization=pol,
    )
    np.testing.assert_allclose(Bdip, Bcyl)

    vert = np.array([[(0, 0, 0), (0, 0, 0.1), (0.1, 0, 0), (0, 0.1, 0)]] * 2)
    vol = 1 / 6 * 1e-3
    pol = mom / vol * MU0
    Btetra = magnet_tetrahedron_field(
        field="H",
        observers=obs,
        vertices=vert,
        polarization=pol,
    )
    np.testing.assert_allclose(Bdip, Btetra, rtol=1e-3)

    dim = np.array([(0.1, 0.2, 0.1, -25, 25)] * 2)
    vol = 3 * np.pi * (50 / 360) * 1e-3
    pol = mom / vol * MU0
    Bcys = BHJM_cylinder_segment(
        field="H",
        observers=obs + np.array((0.15, 0, 0)),
        dimension=dim,
        polarization=pol,
    )
    np.testing.assert_allclose(Bdip, Bcys, rtol=1e-4)


# --> Circle
def test_core_physics_circle_VS_webpage_numbers():
    """
    Compare Circle on-axis field vs e-magnetica & hyperphysics
    """
    dia = np.array([2] * 4)
    curr = np.array([1e3] * 4)  # A
    zs = [0, 1, 2, 3]
    obs = np.array([(0, 0, z) for z in zs])

    # values from e-magnetica
    Hz = [500, 176.8, 44.72, 15.81]
    Htest = [(0, 0, hz) for hz in Hz]

    H = BHJM_circle(
        field="H",
        observers=obs,
        diameter=dia,
        current=curr,
    )
    np.testing.assert_allclose(H, Htest, rtol=1e-3)

    # values from hyperphysics
    Bz = [
        0.6283185307179586e-3,
        2.2214414690791835e-4,
        5.619851784832581e-5,
        1.9869176531592205e-5,
    ]
    Btest = [(0, 0, bz) for bz in Bz]

    B = BHJM_circle(
        field="B",
        observers=obs,
        diameter=dia,
        current=curr,
    )
    np.testing.assert_allclose(B, Btest, rtol=1e-7)


# Cuboid <> Polyline
def test_core_physics_cube_current_replacement():
    """compare cuboid field with current replacement"""
    obs = np.array([(2, 2, 3.13), (-2.123, -4, 2)])
    h = 1
    Jz = 1.23
    dim = np.array([(2, 2, h)] * 2)
    pol = np.array([(0, 0, Jz)] * 2)
    Hcub = BHJM_magnet_cuboid(
        field="H",
        observers=obs,
        dimension=dim,
        polarization=pol,
    )

    # construct from polylines
    n = 1000
    vert = np.array([(1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0), (1, 1, 0)])
    curr = h / n * Jz / MU0
    hs = np.linspace(-h / 2, h / 2, n)
    hpos = np.array([(0, 0, h) for h in hs])

    obs1 = np.array([obs[0] + hp for hp in hpos] * 4)
    obs2 = np.array([obs[1] + hp for hp in hpos] * 4)

    start = np.repeat(vert[:-1], n, axis=0)
    end = np.repeat(vert[1:], n, axis=0)

    Hcurr = np.zeros((2, 3))
    for i, obss in enumerate([obs1, obs2]):
        h = BHJM_polyline(
            field="H",
            observers=obss,
            segment_start=start,
            segment_end=end,
            current=np.array([curr] * 4 * n),
        )
        Hcurr[i] = np.sum(h, axis=0)

    np.testing.assert_allclose(Hcub, -Hcurr, rtol=1e-4)


def test_core_physics_triangle_cube_geometry():
    """test core triangle VS cube"""
    obs = np.array([(3, 4, 5)] * 4)
    mag = np.array([(0, 0, 333)] * 4)
    fac = np.array(
        [
            [(-1, -1, 1), (1, -1, 1), (-1, 1, 1)],  # top1
            [(1, -1, -1), (-1, -1, -1), (-1, 1, -1)],  # bott1
            [(1, -1, 1), (1, 1, 1), (-1, 1, 1)],  # top2
            [(1, 1, -1), (1, -1, -1), (-1, 1, -1)],  # bott2
        ]
    )
    b = triangle_field(
        field="B",
        observers=obs,
        vertices=fac,
        polarization=mag,
    )
    b = np.sum(b, axis=0)

    obs = np.array([(3, 4, 5)])
    mag = np.array([(0, 0, 333)])
    dim = np.array([(2, 2, 2)])
    bb = BHJM_magnet_cuboid(
        field="B",
        observers=obs,
        dimension=dim,
        polarization=mag,
    )[0]

    np.testing.assert_allclose(b, bb)


def test_core_physics_triangle_VS_itself():
    """test core single triangle vs same surface split up into 4 triangular faces"""
    obs = np.array([(3, 4, 5)])
    mag = np.array([(111, 222, 333)])
    fac = np.array(
        [
            [(0, 0, 0), (10, 0, 0), (0, 10, 0)],
        ]
    )
    b = triangle_field(
        field="B",
        observers=obs,
        polarization=mag,
        vertices=fac,
    )
    b = np.sum(b, axis=0)

    obs = np.array([(3, 4, 5)] * 4)
    mag = np.array([(111, 222, 333)] * 4)
    fac = np.array(
        [
            [(0, 0, 0), (3, 0, 0), (0, 10, 0)],
            [(3, 0, 0), (5, 0, 0), (0, 10, 0)],
            [(5, 0, 0), (6, 0, 0), (0, 10, 0)],
            [(6, 0, 0), (10, 0, 0), (0, 10, 0)],
        ]
    )
    bb = triangle_field(
        field="B",
        observers=obs,
        polarization=mag,
        vertices=fac,
    )
    bb = np.sum(bb, axis=0)

    np.testing.assert_allclose(b, bb)


def test_core_physics_Tetrahedron_VS_Cuboid():
    """test core tetrahedron vs cube"""
    ver = np.array(
        [
            [(1, 1, -1), (1, 1, 1), (-1, 1, 1), (1, -1, 1)],
            [(-1, -1, 1), (-1, 1, 1), (1, -1, 1), (1, -1, -1)],
            [(-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1)],
            [(-1, 1, -1), (1, -1, -1), (-1, -1, 1), (-1, 1, 1)],
            [(1, -1, -1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)],
            [(-1, 1, -1), (-1, 1, 1), (1, 1, -1), (1, -1, -1)],
        ]
    )

    mags = [
        [1.03595366, 0.42840487, 0.10797529],
        [0.33513152, 1.61629547, 0.15959791],
        [0.29904441, 1.32185041, 1.81218046],
        [0.82665456, 1.86827489, 1.67338911],
        [0.97619806, 1.52323106, 1.63628455],
        [1.70290645, 1.49610608, 0.13878711],
        [1.49886747, 1.55633919, 1.41351862],
        [0.9959534, 0.62059942, 1.28616663],
        [0.60114354, 0.96120344, 0.32009221],
        [0.83133901, 0.7925518, 0.64574592],
    ]

    obss = [
        [0.82811352, 1.77818627, 0.19819379],
        [0.84147235, 1.10200857, 1.51687527],
        [0.30751474, 0.89773196, 0.56468564],
        [1.87437889, 1.55908581, 1.10579983],
        [0.64810548, 1.38123846, 1.90576802],
        [0.48981034, 0.09376294, 0.53717129],
        [1.42826412, 0.30246674, 0.57649909],
        [1.58376758, 1.70420478, 0.22894022],
        [0.26791832, 0.36839769, 0.67934335],
        [1.15140149, 0.10549875, 0.98304184],
    ]

    for mag in mags:
        for obs in obss:
            obs6 = np.tile(obs, (6, 1))
            mag6 = np.tile(mag, (6, 1))
            b = magnet_tetrahedron_field(
                field="B",
                observers=obs6,
                polarization=mag6,
                vertices=ver,
            )
            h = magnet_tetrahedron_field(
                field="H",
                observers=obs6,
                polarization=mag6,
                vertices=ver,
            )
            b = np.sum(b, axis=0)
            h = np.sum(h, axis=0)

            obs1 = np.reshape(obs, (1, 3))
            mag1 = np.reshape(mag, (1, 3))
            dim = np.array([(2, 2, 2)])
            bb = BHJM_magnet_cuboid(
                field="B",
                observers=obs1,
                polarization=mag1,
                dimension=dim,
            )[0]
            hh = BHJM_magnet_cuboid(
                field="H",
                observers=obs1,
                polarization=mag1,
                dimension=dim,
            )[0]
            np.testing.assert_allclose(b, bb)
            np.testing.assert_allclose(h, hh)
