import nqpv
import numpy as np

# create the required operators
W1 = np.array([[1., 1., 0., -1.],
                [1., -1., 1., 0.],
                [0., 1., 1., 1.],
                [1., 0., -1., 1.]]) / np.sqrt(3)
W2 = np.array([[1., 1., 0., 1.],
                [-1., 1., -1., 0.],
                [0., 1., 1., -1.],
                [1., 0., -1., -1.]]) / np.sqrt(3)
np.save("W1", W1.reshape((2,2,2,2)))
np.save("W2", W2.reshape((2,2,2,2)))

P0 = np.array([[0., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 1., 0.],
                    [0., 0., 0., 0.]])
P1 = np.array([[1., 0., 0., 0.],
                    [0., 1., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 1.]])
                    
MQWalk = np.stack((P0,P1), axis = 0)
np.save("MQWalk", MQWalk.reshape((2,2,2,2,2)))

# the invariant N
invN = np.array([[1., 0., 0., 0.],
                [0., 0.5, 0., 0.5],
                [0., 0., 0., 0.],
                [0., 0.5, 0., 0.5]])
np.save("invN", invN.reshape((2,2,2,2)))

# verify
nqpv.verify("prog.nqpv")