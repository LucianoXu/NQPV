import nqpv
import numpy as np

# create the operator library
nqpv.lib_create("./lib")

# create the required operators
Hpost = np.array([[1., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 0.],
                    [0., 0., 0., 1.]])
nqpv.save_hermitian("./example_Deutsch", "Hpost", Hpost)

# verify
nqpv.verify("./example_Deutsch", "./lib", opt_in_output = True, preserve_pre = True)