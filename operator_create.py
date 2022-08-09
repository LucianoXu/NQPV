# ------------------------------------------------------------
# operator_create.py
#
# create the commonly used unitary gates and measurements
# ------------------------------------------------------------



import numpy as np
import os


# create unitary gates
folder = os.path.exists("./unitary")
if not folder:
    os.makedirs('./unitary')

I = np.array(
    [[1., 0.],
    [0., 1.]]
)
np.save('./unitary/I.npy', I)

X = np.array(
    [[0., 1.],
    [1., 0.]]
)
np.save('./unitary/X.npy', X)

Y = np.array(
    [[0., -1.j],
    [1.j, 0.]]
)
np.save('./unitary/Y.npy', Y)

Z = np.array(
    [[1., 0.],
    [0., -1.]]
)
np.save('./unitary/Z.npy', Z)

H = np.array(
    [[1., 1.],
    [1., 1.]]
)/np.sqrt(2)
np.save('./unitary/H.npy', H)

CX = np.array(
    [[1., 0., 0., 0.],
    [0., 1., 0., 0.],
    [0., 0., 0., 1.],
    [0., 0., 1., 0.]]
).reshape((2,2,2,2))
np.save('./unitary/CX.npy', CX)


# create measurements
folder = os.path.exists("./measure")
if not folder:
    os.makedirs('./measure')

M01 = np.array(
    [[[1., 0.],
    [0., 0.]],

    [[0., 0.],
    [0., 1.]]]
)
np.save('./measure/M01.npy', M01)

M10 = np.array(
    [[[0., 0.],
    [0., 1.]],

    [[1., 0.],
    [0., 0.]]]
)
np.save('./measure/M10.npy', M10)

Mpm = np.array(
    [[[0.5, 0.5],
    [0.5, 0.5]],

    [[0.5, -0.5],
    [-0.5, 0.5]]]
)
np.save('./measure/Mpm.npy', Mpm)

Mmp = np.array(
    [[[0.5, -0.5],
    [-0.5, 0.5]],

    [[0.5, 0.5],
    [0.5, 0.5]]]
)
np.save('./measure/Mmp.npy', Mmp)

