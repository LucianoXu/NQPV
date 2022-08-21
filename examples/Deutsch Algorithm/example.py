import nqpv
import numpy as np

# create the required operators
Hpost = np.array([[1., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 1.]])
nqpv.save_hermitian("./example_Deutsch", "Hpost", Hpost)

# verify
nqpv.verify("./example_Deutsch", opt_in_output = True)