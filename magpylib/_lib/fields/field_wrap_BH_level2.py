import sys
import numpy as np
from scipy.spatial.transform import Rotation as R
import magpylib as mag3
from magpylib._lib.math_utility import format_src_input, get_good_path_length, all_same
from magpylib._lib.config import Config
from magpylib._lib.fields.field_wrap_BH_level1 import getBH_level1


def scr_dict_homo_mag(group: list, poso: np.ndarray) -> dict:
    """ Helper funtion that generates getBH_level1 input dict for homogeneous magnets.

    Parameters
    ----------
    - group: list of sources
    - posov: ndarray, shape (m,sum(ni),3), pos_obs flattened

    Returns
    -------
    dict for getBH_level1 input
    """
    # pylint: disable=protected-access

    l_group = len(group)    # sources in group
    m = len(group[0]._pos)  # path length
    mn = len(poso)          # path length * no.pixel
    n = int(mn/m)             # no.pixel
    len_dim = len(group[0].dim) # source type dim shape

    # prepare and fill arrays, shape: (l_group, m, n)
    magv = np.empty((l_group*mn,3))         # source magnetization
    dimv = np.empty((l_group*mn,len_dim))   # source dimension
    posv = np.empty((l_group*mn,3))         # source position
    rotv = np.empty((l_group*mn,4))         # source rotation
    for i,src in enumerate(group):
        magv[i*mn:(i+1)*mn] = np.tile(src.mag, (mn,1))
        dimv[i*mn:(i+1)*mn] = np.tile(src.dim, (mn,1))
        posv[i*mn:(i+1)*mn] = np.tile(src._pos,n).reshape(mn,3)
        rotv[i*mn:(i+1)*mn] = np.tile(src._rot.as_quat(),n).reshape(mn,4)
    posov = np.tile(poso, (l_group,1))

    rotobj = R.from_quat(rotv)
    src_dict = {'mag':magv, 'dim':dimv, 'pos':posv, 'pos_obs': posov, 'rot':rotobj}
    return src_dict


def getBH_level2(bh, sources, observers, sumup, **kwargs) -> np.ndarray:
    """...

    Parameters
    ----------
    - bh (bool): True=getB, False=getH
    - sources (src_obj or list): source object or 1D list of L sources/collections with similar
        pathlength M and/or 1.
    - observers (sens_obj or list or pos_obs): pos_obs or sensor object or 1D list of K sensors with
        similar pathlength M and/or 1 and sensor pos_pix of shape (N1,N2,...,3).
    - sumup (bool): default=False returns [B1,B2,...] for every source, True returns sum(Bi)
        for all sources.
    - niter (int): default=50, for Cylinder sources diametral iteration

    Returns
    -------
    field: ndarray, shape squeeze((L,M,K,N1,N2,...,3)), field of L sources, M path
    positions, K sensors and N1xN2x.. observer positions and 3 field components.

    Info:
    -----
    - generates a 1D list of sources (collections flattened) and a 1D list of sensors from input
    - tile all paths of static (path_length=1) objects
    - combine all sensor pixel positions for joint evaluation
    - group similar source types for joint evaluation
    - compute field and store in allocated array
    - rearrange the array in the shape squeeze((L, M, K, N1, N2, ...,3))
    """
    # pylint: disable=protected-access
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    # format input -------------------------------------------------------------
    if not isinstance(sources, list):
        sources = [sources]
    src_list = format_src_input(sources) # flatten Collections

    if isinstance(observers, mag3.Sensor):               # input = 1 sensor
        sensors = [observers]
    elif isinstance(observers, list):                    # input = list (sensors or positions)
        if isinstance(observers[0],mag3.Sensor):
            sensors = observers
        else:
            sensors = [mag3.Sensor(pos_pix=observers)]
    else:                                                # input = pos_obs
        sensors = [mag3.Sensor(pos_pix=observers)]

    obj_list = src_list + sensors
    l0 = len(sources)
    l = len(src_list)
    k = len(sensors)

    # input path check + tile up static objects --------------------------------
    # tile up length 1 paths
    #    sys.exit if any path format is bad
    #    sys.exit if any path length is not m or 1
    m = get_good_path_length(obj_list)
    # store pointers to objects that are tiled up
    reset_objects = []
    if m>1:
        for obj in obj_list: # can have same obj several times in obj_list through a collection
            if len(obj._pos) == 1:
                reset_objects += [obj]
                obj.pos = np.tile(obj.pos, (m,1))
                rotq = np.tile(obj._rot.as_quat(), (m,1))
                obj.rot = R.from_quat(rotq)

    # combine information form all sensors to generate pos_obs with-------------
    #   shape (m * concat all sens flat pos_pix, 3)
    #   allows sensors with different pos_pix shapes
    poso =[[r.apply(sens.pos_pix.reshape(-1,3)) + p
            for r,p in zip(sens._rot, sens._pos)]
           for sens in sensors] # shape (k, nk, 3)
    poso = np.concatenate(poso,axis=1).reshape(-1,3)
    mn = len(poso)
    n = int(mn/m)

    # group similar source types----------------------------------------------
    src_sorted = [[],[]]   # store groups here
    order = [[],[]]        # keep track of the source order
    for i,src in enumerate(src_list):
        if isinstance(src, mag3.magnet.Box):
            src_sorted[0] += [src]
            order[0] += [i]
        elif isinstance(src, mag3.magnet.Cylinder):
            src_sorted[1] += [src]
            order[1] += [i]
        else:
            sys.exit('ERROR (getBH_level2): bad source input !')

    # evaluate each non-empty group in one go -------------------------------
    B = np.empty((l,m,n,3)) # store B-values here

    # Box group
    group = src_sorted[0]
    if group:
        lg = len(group)
        src_dict = scr_dict_homo_mag(group, poso)             # compute array dict for level1
        B_group = getBH_level1(bh=bh, src_type='Box', **src_dict) # compute field
        B_group = B_group.reshape((lg,m,n,3))         # reshape
        for i in range(lg):                           # put at dedicated positions in B
            B[order[0][i]] = B_group[i]

    # Cylinder group
    group = src_sorted[1]
    if group:
        lg = len(group)
        niter = kwargs.get('niter', Config.ITER_CYLINDER)
        src_dict = scr_dict_homo_mag(group, poso)
        B_group = getBH_level1(bh=bh, src_type='Cylinder', niter=niter, **src_dict)
        B_group = B_group.reshape((lg,m,n,3))
        for i in range(lg):
            B[order[1][i]] = B_group[i]

    # reshape output ----------------------------------------------------------------
    # rearrange B when there is at least one Collection with more than one source
    if l > l0:
        for i,src in enumerate(sources):
            if isinstance(src, mag3.Collection):
                col_len = len(src.sources)
                B[i] = np.sum(B[i:i+col_len],axis=0)    # set B[i] to sum of slice
                B = np.delete(B,np.s_[i+1:i+col_len],0) # delete remaining part of slice

    # rearrange sensor-pixel shape
    pix_shapes = [sens.pos_pix.shape for sens in sensors]
    if all_same(pix_shapes):
        sens_px_shape = (k,) + pix_shapes[0]
        B = B.reshape((l0,m)+sens_px_shape)
    else:
        print('WARNING(getBH_level2): sensors with different pixle shape - merging all sensors')

    if sumup:
        B = np.sum(B, axis=0)

    # reduce all size-1 levels
    B = np.squeeze(B)

    # reset tiled objects
    for obj in reset_objects:
        obj.pos = obj.pos[0]
        obj.rot = obj.rot[0]

    return B
