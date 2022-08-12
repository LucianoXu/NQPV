# ------------------------------------------------------------
# operator_create.py
#
# create the commonly used unitary gates and measurements
# ------------------------------------------------------------



import numpy as np
import os

def lib_create(lib_path):
    if lib_path[-1] == '/' or lib_path[-1] == '\\':
        lib_path = lib_path[:-1]
    
    try:
        # create the library
        folder = os.path.exists(lib_path)
        if not folder:
            os.makedirs(lib_path)

        # create unitary gates
        folder = os.path.exists(lib_path + "/unitary")
        if not folder:
            os.makedirs(lib_path + "/unitary")

        I = np.array(
            [[1., 0.],
            [0., 1.]]
        )
        np.save(lib_path + '/unitary/I.npy', I)

        X = np.array(
            [[0., 1.],
            [1., 0.]]
        )
        np.save(lib_path + '//unitary/X.npy', X)

        Y = np.array(
            [[0., -1.j],
            [1.j, 0.]]
        )
        np.save(lib_path + '/unitary/Y.npy', Y)

        Z = np.array(
            [[1., 0.],
            [0., -1.]]
        )
        np.save(lib_path + '/unitary/Z.npy', Z)

        H = np.array(
            [[1., 1.],
            [1., -1.]]
        )/np.sqrt(2)
        np.save(lib_path + '/unitary/H.npy', H)

        CX = np.array(
            [[1., 0., 0., 0.],
            [0., 1., 0., 0.],
            [0., 0., 0., 1.],
            [0., 0., 1., 0.]]
        ).reshape((2,2,2,2))
        np.save(lib_path + '/unitary/CX.npy', CX)


        # create measurements
        folder = os.path.exists(lib_path + "/measure")
        if not folder:
            os.makedirs(lib_path + '/measure')

        M01 = np.array(
            [[[1., 0.],
            [0., 0.]],

            [[0., 0.],
            [0., 1.]]]
        )
        np.save(lib_path + '/measure/M01.npy', M01)

        M10 = np.array(
            [[[0., 0.],
            [0., 1.]],

            [[1., 0.],
            [0., 0.]]]
        )
        np.save(lib_path + '/measure/M10.npy', M10)

        Mpm = np.array(
            [[[0.5, 0.5],
            [0.5, 0.5]],

            [[0.5, -0.5],
            [-0.5, 0.5]]]
        )
        np.save(lib_path + '/measure/Mpm.npy', Mpm)

        Mmp = np.array(
            [[[0.5, -0.5],
            [-0.5, 0.5]],

            [[0.5, 0.5],
            [0.5, 0.5]]]
        )
        np.save(lib_path + '/measure/Mmp.npy', Mmp)

        # create hermitian operators
        folder = os.path.exists(lib_path + "/herm")
        if not folder:
            os.makedirs(lib_path + '/herm')

        np.save(lib_path + '/herm/I.npy', I)

        zero = np.zeros((2,2))
        np.save(lib_path + '/herm/Zero.npy', zero)

        P0 = np.array([[1., 0.],
                        [0., 0.]])
        np.save(lib_path + '/herm/P0.npy', P0)

        P1 = np.array([[0., 0.],
                        [0., 1.]])
        np.save(lib_path + '/herm/P1.npy', P1)

        Pp = np.array([[0.5, 0.5],
                        [0.5, 0.5]])
        np.save(lib_path + '/herm/Pp.npy', Pp)

        Pm = np.array([[0.5, -0.5],
                        [-0.5, 0.5]])
        np.save(lib_path + '/herm/Pm.npy', Pm)

    except:
        print("library creation failed")


