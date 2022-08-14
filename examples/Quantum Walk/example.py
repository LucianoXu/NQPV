import nqpv
import numpy as np

# create the operator library
nqpv.lib_create("./lib")

# create the required operators
W1 = np.array([[1., 1., 0., -1.],
                [1., -1., 1., 0.],
                [0., 1., 1., 1.],
                [1., 0., -1., 1.]]) / np.sqrt(3)
W2 = np.array([[1., 1., 0., 1.],
                [-1., 1., -1., 0.],
                [0., 1., 1., -1.],
                [1., 0., -1., -1.]]) / np.sqrt(3)
nqpv.save_unitary("./example_QWalk", "W1", W1)
nqpv.save_unitary("./example_QWalk", "W2", W2)

P0 = np.array([[0., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 1., 0.],
                    [0., 0., 0., 0.]])
P1 = np.array([[1., 0., 0., 0.],
                    [0., 1., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 1.]])
                    
MQWalk = np.stack((P0,P1), axis = 0)
nqpv.save_measurement("./example_QWalk", "MQWalk", MQWalk)

# the invariant N
invN = np.array([[1., 0., 0., 0.],
                [0., 0.5, 0., 0.5],
                [0., 0., 0., 0.],
                [0., 0.5, 0., 0.5]])
nqpv.save_hermitian("./example_QWalk", "invN", invN)

# verify
nqpv.verify("./example_QWalk", "./lib", opt_in_output = True, preserve_pre = True)