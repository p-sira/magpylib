"""
Welcome to Magpylib !
---------------------

Magpylib provides static 3D magnetic field computation for permanent magnets,
currents and other sources using (semi-) analytical formulas from the literature.

Resources
---------

Documentation on Read-the-docs:

https://magpylib.readthedocs.io/en/latest/

Github repository:

https://github.com/magpylib/magpylib

Original software publication (version 2):

https://www.sciencedirect.com/science/article/pii/S2352711020300170

Introduction
------------
Magpylib uses units of

    - [mT]: for the B-field and the magnetization (mu0*M).
    - [kA/m]: for the H-field.
    - [mm]: for all position inputs.
    - [deg]: for angle inputs by default.
    - [A]: for current inputs.

Magpylib objects represent magnetic field sources and sensors with various
attributes

>>> import magpylib as mag3
>>>
>>> # magnets
>>> src1 = mag3.magnet.Cuboid(magnetization=(0,0,1000), dimension=(1,2,3))
>>> src2 = mag3.magnet.Cylinder(magnetization=(0,1000,0), dimension=(1,2))
>>> src3 = mag3.magnet.Sphere(magnetization=(1000,0,0), diameter=1)
>>>
>>> # currents
>>> src4 = mag3.current.Circular(current=15, diameter=3)
>>> src5 = mag3.current.Line(current=15, vertices=[(0,0,0), (1,2,3)])
>>>
>>> # misc
>>> src6 = mag3.misc.Dipole(moment=(100,200,300))
>>>
>>> # sensor
>>> sens = mag3.Sensor()
>>>
>>> for obj in [src1, src2, src3, src4, src5, src6, sens]:
>>>     print(obj)
Cuboid(id=1792490441024)
Cylinder(id=1792490439680)
Sphere(id=1792491053792)
Circular(id=1792491053456)
Line(id=1792492457312)
Dipole(id=1792492479728)
Sensor(id=1792492480784)

All Magpylib objects are endowed with ``position`` and ``orientation`` attributes
that describe their state in a global coordinate system. By default they are set to
zero and unit-rotation respectively.

>>> import magpylib as mag3
>>> sens = mag3.Sensor()
>>> print(sens.position)
>>> print(sens.orientation.as_quat())
[0. 0. 0.]
[0. 0. 0. 1.]

Manipulate position and orientation attributes directly through source attributes,
or by using built-in ``move`` and ``rotate`` methods.

>>> import magpylib as mag3
>>> sens = mag3.Sensor(position=(1,1,1))
>>> print(sens.position)
>>> sens.move((1,1,1))
>>> print(sens.position)
[1. 1. 1.]
[2. 2. 2.]

>>> import magpylib as mag3
>>> from scipy.spatial.transform import Rotation as R
>>> sens = mag3.Sensor(orientation=R.from_rotvec((.1,.1,.1)))
>>> print(sens.orientation.as_rotvec())
>>> sens.rotate(R.from_rotvec((.1,.1,.1)))
>>> print(sens.orientation.as_rotvec())
>>> sens.rotate_from_angax(angle=.1, axis=(1,1,1), degree=False)
>>> print(sens.orientation.as_rotvec())
[0.1 0.1 0.1]
[0.2 0.2 0.2]
[0.25773503 0.25773503 0.25773503]

Source position and rotation attributes can also represent complete source paths in the
global coordinate system. Such paths can be generated conveniently using the ``move`` and
``rotate`` methods.

>>> import magpylib as mag3
>>> src = mag3.magnet.Cuboid(magnetization=(1,2,3), dimension=(1,2,3))
>>> src.move([(1,1,1),(2,2,2),(3,3,3),(4,4,4)], start='append')
>>> print(src.position)
[[0. 0. 0.]  [1. 1. 1.]  [2. 2. 2.]  [3. 3. 3.]  [4. 4. 4.]]


Grouping objects
----------------

Use the Collection class to group objects for common manipulation. All object methods can
also be applied to complete Collections.

>>> import magpylib as mag3
>>> src1 = mag3.magnet.Cuboid(magnetization=(0,0,1000), dimension=(1,2,3))
>>> src2 = mag3.magnet.Cylinder(magnetization=(0,1000,0), dimension=(1,2))
>>> col = src1 + src2
>>> col.move((1,2,3))
>>> for src in col:
>>>     print(src.pos)
[1. 2. 3.]
[1. 2. 3.]

Field computation
-----------------

The magnetic field generated by ``sources`` at ``observers`` can be computed
through the top level functions ``getB`` and ``getH``. Sources are magpylib
source objects like Circular or Dipole. Observers are magpylib Sensor
objects or simply sets (list, tuple, ndarray) of positions. The result will be an array of
all possible source-observer-path combinations

>>> import magpylib as mag3
>>> src1 = mag3.current.Circular(current=15, diameter=2)
>>> src2 = mag3.misc.Dipole(moment=(100,100,100))
>>> sens = mag3.Sensor(position=(1,1,1))
>>> obs_pos = (1,2,3)
>>> B = mag3.getB(sources=[src1,src2], observers=[sens,obs_pos])
>>> print(B)
[[[0.93539608 0.93539608 0.40046672]
  [0.05387784 0.10775569 0.0872515 ]]
 [[3.06293831 3.06293831 3.06293831]
  [0.04340403 0.23872216 0.43404028]]]

Field computation is also directly accessible in the form of object methods:

>>> import magpylib as mag3
>>> src = mag3.misc.Dipole(moment=(100,100,100))
>>> sens = mag3.Sensor(position=(1,1,1))
>>> pos_obs = (1,2,3)
>>> print(src.getB(sens, pos_obs))
[[3.06293831 3.06293831 3.06293831]
 [0.04340403 0.23872216 0.43404028]]

Finally there is a direct (very fast) interface to the field computation formulas
that avoids the object oriented Magpylib interface:

>>> import magpylib as mag3
>>> B = mag3.getBv(
>>>     source_type='Dipole',
>>>     moment=(100,100,100),
>>>     observer=[(1,1,1), (1,2,3)])
>>> print(B)
[[3.06293831 3.06293831 3.06293831]
 [0.04340403 0.23872216 0.43404028]]

Graphic output
--------------
Display sources, collections, paths and sensors using Matplotlib from top level
functions,

>>> import magpylib as mag3
>>> src1 = mag3.magnet.Sphere(magnetization=(1000,0,0), diameter=1)
>>> src2 = mag3.current.Circular(current=15, diameter=3)
>>> mag3.display(src1, src2)
--> graphic output

or directly through object methods

>>> import magpylib as mag3
>>> src = mag3.current.Circular(current=15, diameter=3)
>>> src.display()
--> graphic output

"""

# module level dunders
__version__ = '3.0.0'
__author__ =  'Michael Ortner & friends'
__credits__ = 'Silicon Austria Labs - Sensor Systems'
__all__ = ['magnet', 'current', 'misc',
           'getB', 'getH', 'getBv', 'getHv','Sensor',
           'Collection', 'display', 'Config']

# create interface to outside of package
from magpylib import magnet
from magpylib import current
from magpylib import misc
from magpylib._lib.config import Config
from magpylib._lib.fields import getB, getH, getBv, getHv
from magpylib._lib.obj_classes import Collection, Sensor
from magpylib._lib.display import display
