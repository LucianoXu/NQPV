'''
 Copyright 2022 Yingte Xu
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

# ------------------------------------------------------------
# set_order.py
#
# decide the partial order of Hermitian operator sets, using SDP
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List


from .logsystem import LogSystem

# define the channel to save the witness
channel_witness = "witness"

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
            LogSystem.channels[channel_witness].append(
                "Order relation not satisfied. Density operator witnessed: \n" + str(X.value)
            )
            return False

    return True
