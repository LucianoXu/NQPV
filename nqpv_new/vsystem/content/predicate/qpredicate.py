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
# qpredicate.py
#
# define the predicates and the sqsubseteq partial order
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from nqpv_new.vsystem.var_env import VType, Value

from ...log_system import RuntimeErrorWithLog
from ...syntax.pos_info import PosInfo

from ...venv import VEnv
from ..opt import opt_kernel
from ..opt.opt_kernel import Precision

import numpy as np
import cvxpy as cp


class QPredicate:
    def __init__(self, pos : PosInfo, pairs : List[Tuple[str, List[str]]]):
        self.pos : PosInfo = pos
        self.pairs : List[Tuple[str, List[str]]] = pairs
    
    def full_extension(self, venv : VEnv, qvar_seq : Tuple[str,...]) -> QPredicate:
        '''
        return the full_extension qpredicate
        qvar_seq specifies the qubit order
        '''
        new_pairs = []
        for pair in self.pairs:
            ext = opt_kernel.hermitian_extend(
                qvar_seq, venv.get_var(pair[0]).data, tuple(pair[1])
            )
            ext_name = venv.var_env.auto_name()
            venv.var_env.assign_var(
                ext_name, 
                VType("operator", (len(qvar_seq),)), 
                Value(VType("operator", ()), ext)
            )
            new_pairs.append((ext_name, list(qvar_seq)))
            
        return QPredicate(self.pos, new_pairs)



    
def sqsubseteq(preA : QPredicate, preB : QPredicate, venv : VEnv) -> None:
    '''
    decide whether self sqsubseteq_inf other
    '''
    if not isinstance(preA, QPredicate) or not isinstance(preB, QPredicate):
        raise Exception("unexpected situation")
        

    #print("begin SDP ...")

    # transform all the hermitian operators into matrices
    dim = 2**len(preA.pairs[0][1])
    msetA = [opt_kernel.tensor_to_matrix(venv.get_var(pre[0]).data) for pre in preA.pairs]

    for pairB in preB.pairs:
        mB = opt_kernel.tensor_to_matrix(venv.get_var(pairB[0]).data)

        X = cp.Variable((dim, dim), hermitian=True) # type: ignore
        constraints = [X >> 0]  # type: ignore
        constraints += [
            cp.real(cp.trace((mB - mA) @ X)) <= -Precision.EPS() for mA in msetA  # type: ignore
        ]
        prob = cp.Problem(cp.Minimize(0), constraints)  # type: ignore

        prob.solve(eps = Precision.SDP_precision())

        # Print result. debug purpose.
        '''
        print(constraints[-1])
        print("The optimal value is", prob.value)
        print("A solution X is")
        print(X.value)
        '''

        # if a solution has been found, register the result
        if X.value is not None:

            # rescale to satisfy trace(rho) = 1
            sol = X.value / np.trace(X.value)

            raise RuntimeErrorWithLog("Partial order not satisfied.")
            '''
            sol_name = OptEnv.append(sol, "", False)
            # require this opt
            OptEnv.use_opt(sol_name, None)

            LogSystem.channels["witness"].append(
                "\nOrder relation not satisfied: \n\t" + 
                str(preA) + " <= " + str(preB) + "\n"+
                "The operator '" + str(opt_b) + "' can be violated.\n"+
                "Density operator witnessed: '" + sol_name + "'.\n"
                + PosInfo.str(preA.pos) + PosInfo.str(preB.pos)
            )
            '''
    
