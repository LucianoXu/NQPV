import nqpv
import numpy as np

# create a Hermitian on a random ket
theta = np.random.rand() * np.pi
phi = np.random.rand() * np.pi * 2

ket = np.array([np.cos(theta), np.sin(theta)*np.exp(phi*1j)])

Hrand = np.outer(ket, np.conj(ket))

np.save("Hrand", Hrand)

# verify
nqpv.verify("./prog.nqpv")