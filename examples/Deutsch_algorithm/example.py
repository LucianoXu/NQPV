import nqpv
import numpy as np

# create the required operators
Hpost = np.array([[1., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 1.]])
np.save("./Hpost", Hpost.reshape((2,2,2,2)))

# verify
nqpv.verify("./prog.nqpv")