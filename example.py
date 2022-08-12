import nqpv
import numpy as np


nqpv.lib_create("./lib")


# example_ErrCorr
theta = np.random.rand() * np.pi
phi = np.random.rand() * np.pi * 2

ket = np.array([np.cos(theta), np.sin(theta)*np.exp(phi*1j)])

Hrand = np.outer(ket, np.conj(ket))

nqpv.save_hermitian("./example_ErrCorr", "Hrand", Hrand)

nqpv.verify("./example_ErrCorr", "./lib", opt_in_output = True, preserve_pre = True)