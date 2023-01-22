import nqpv
import numpy as np
# create the required operators
sol = np.array([1., 0., 0., 0.])
Psol = np.tensordot(sol, sol, 0)
np.save("./Psol", Psol.reshape((2, 2, 2, 2)))
O = np.eye(4) - 2*Psol
np.save("./O", O.reshape(2, 2, 2, 2))
CP = np.diag(np.array([1., -1., -1., -1.]))
np.save("./CP", CP.reshape(2, 2, 2, 2))
# verify
nqpv.verify("./prog.nqpv")