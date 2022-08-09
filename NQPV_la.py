# ------------------------------------------------------------
# NQPV_la.py
#
# linear algebra tools needed in this verifier
# ------------------------------------------------------------

import numpy as np

EPS = 1e-12

def complex_norm(c):
    return np.sqrt(c * np.conj(c)).real

def check_unity(m, m_id):
    '''
    check whether tensor m is unitary
    m: tensor of shape (2,2,...,2), with the row indices in front of the column indices
    '''
    if len(m.shape) % 2 == 1:
        print("The dimension of '" + m_id + "' is invalid for an unitary.")
        return False

    for dim in m.shape:
        if dim != 2:
            print("The dimension of '" + m_id + "' is invalid for an unitary.")
            return False
    
    # calculate the dim for matrix
    dim_m = 2**(len(m.shape)//2)
    matrix = m.reshape((dim_m, dim_m))

    # check the maximum of U^dagger @ U - I
    zero_check = (matrix @ np.transpose(np.conj(matrix))) - np.eye(dim_m)
    diff = np.sqrt(complex_norm(np.max(zero_check)))
    if diff > EPS:
        print("'" + m_id + "' is not an unitary matrix." )
        return False
    return True

def check_measure(m, m_id):
    '''
    check whether tensor m is a valid measurement
    m: tensor of shape (2,2,...,2), with the row indices in front of the column indices. 
        The first index of m corresponds to measurement result 0 or 1.
    '''
    if len(m.shape) % 2 == 0:
        print("The dimension of '" + m_id + "' is invalid for a measurement.")
        return False

    for dim in m.shape:
        if dim != 2:
            print("The dimension of '" + m_id + "' is invalid for a measurement.")
            return False
    
    # calculate the dim for matrix
    dim_m = 2**((len(m.shape)-1)//2)

    # pick out M0 and M1
    m0 = m[0].reshape((dim_m, dim_m))
    m1 = m[1].reshape((dim_m, dim_m))

    # check the maximum of U^dagger @ U - I
    zero_check = (m0.conj().transpose() @ m0 + m1.conj().transpose() @ m1) - np.eye(dim_m)
    diff = np.sqrt(complex_norm(np.max(zero_check)))
    if diff > EPS:
        print("'" + m_id + "' does not satisfy the normalization requirement of a measurement." )
        return False
    return True