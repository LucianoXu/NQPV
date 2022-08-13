import nqpv
import numpy as np




def example_ErrCorr():
    # example_ErrCorr
    theta = np.random.rand() * np.pi
    phi = np.random.rand() * np.pi * 2

    ket = np.array([np.cos(theta), np.sin(theta)*np.exp(phi*1j)])

    Hrand = np.outer(ket, np.conj(ket))

    nqpv.save_hermitian("./example_ErrCorr", "Hrand", Hrand)

    nqpv.verify("./example_ErrCorr", "./lib", opt_in_output = True, preserve_pre = True)

def example_QWalk():
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

    nqpv.verify("./example_QWalk", "./lib", opt_in_output = True, preserve_pre = True)

def example_Deutsch():
    Hpost = np.array([[1., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 1.]])
    nqpv.save_hermitian("./example_Deutsch", "Hpost", Hpost)

    nqpv.verify("./example_Deutsch", "./lib", opt_in_output = True, preserve_pre = True)

if __name__ == "__main__":

    #nqpv.lib_create("./lib")

    example_Deutsch()
