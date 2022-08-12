# ------------------------------------------------------------
# set_order.py
#
# decide the partial order of Hermitian operator sets, using SDP
# ------------------------------------------------------------

from .NQPV_la import EPS

import numpy as np
import cvxpy as cp

def sqsubseteq(setA : list, setB : list) -> bool:
    '''
    decide the partial order of Hermitian operator sets, using SDP
    setA, setB: list of hermitian operators, in numpy array form, with shape of (2,2,2,2,...)
        These hermitian operators should have been examinated already.
    return: True if setA sqsubseteq setB, else False.
    '''
    
    # transform all the hermitian operators into matrices
    qubitn = len(setA[0].shape)//2
    dim = 2**qubitn
    msetA = [m.reshape((dim, dim)) for m in setA]
    msetB = [m.reshape((dim, dim)) for m in setB]

    #print(msetA)
    #print(msetB)

    for mB in msetB:
        X = cp.Variable((dim, dim), hermitian=True)
        constraints = [X >> 0]
        constraints += [
            cp.real(cp.trace((mB - mA) @ X)) <= -EPS for mA in msetA
        ]
        prob = cp.Problem(cp.Minimize(0),
                  constraints)
        prob.solve(eps = EPS/10)

        # Print result. debug purpose.
        '''
        print(constraints[-1])
        print("The optimal value is", prob.value)
        print("A solution X is")
        print(X.value)
        '''

        # if a solution has been found
        if X.value is not None:
            return False

    return True
