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
# qpre_term.py
#
# define the quantum predicate terms, and the sqsubseteq decider (base on the SDP solver)
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Tuple

from nqpv_new import dts

from nqpv_new.vsystem.log_system import RuntimeErrorWithLog

from . import opt_kernel
from .opt_pair_term import OptPairTerm, type_opt_pair

import numpy as np
import cvxpy as cp

fac = dts.TermFact()

type_qpre = fac.axiom("qpre", fac.sort_term(0))

class QPreTerm(dts.Term):
    def __init__(self, opt_pairs : Tuple[dts.Term,...]):
        # check the terms
        if not isinstance(opt_pairs, tuple):
            raise ValueError()
        
        for pair in opt_pairs:
            if not isinstance(pair, dts.Term):
                raise ValueError()
            if pair.type != type_opt_pair:
                raise RuntimeErrorWithLog("The term '" + str(pair) + "' is not an operator variable pair.")
            
            # check for hermitian predicate pair
            pair_val : OptPairTerm = pair.eval() # type: ignore
            if not pair_val.hermitian_predicate_pair:
                raise RuntimeErrorWithLog("The pair '" + str(pair) + "' is not a hermitian predicate pair.")
        
        super().__init__(type_qpre, None)
        self._opt_pairs : Tuple[dts.Term,...] = opt_pairs
    
    @property
    def opt_pairs(self) -> Tuple[dts.Term,...]:
        return self._opt_pairs

    def __len__(self) -> int:
        return len(self._opt_pairs)

    def get_pair(self, i : int) -> OptPairTerm:
        temp = self._opt_pairs[i].eval()
        if not isinstance(temp, OptPairTerm):
            raise Exception("unexpected situation")
        return temp

    def eval(self) -> dts.Term:
        evaluated = []
        for pair in self._opt_pairs:
            evaluated.append(pair.eval())
        return QPreTerm(tuple(evaluated))
    
    def __str__(self) -> str:
        if len(self) == 0:
            return "{}"
        r = "{ " + str(self._opt_pairs[0])
        for i in range(1, len(self)):
            r += " " + str(self._opt_pairs[i])
        r += " }"
        return r

    @staticmethod
    def sqsubseteq(qpreA : dts.Term, qpreB : dts.Term) -> None:
        '''
        checks the requirement of qpreA sqsubseteq_inf qpreB
        '''
        if not isinstance(qpreA, dts.Term) or not isinstance(qpreB, dts.Term):
            raise ValueError()
        
        # evaluate the expressions
        qpreA = qpreA.eval()    # type: ignore
        qpreB = qpreB.eval()    # type: ignore
        
        # compare the variable list first
        if not isinstance(qpreA, QPreTerm):
            raise Exception("invalid usage")
        if not isinstance(qpreB, QPreTerm):
            raise Exception("invalid usage")
        example_pair = qpreA.opt_pairs[0]
        if not isinstance(example_pair, OptPairTerm):
            raise Exception("unexpected situation")
        
        for pair in qpreA.opt_pairs:
            if not isinstance(pair, OptPairTerm):
                raise Exception("unexpected situation")
            if example_pair.qvarls != pair.qvarls:
                raise Exception("invalid usage, qpreA and qpreB must have hermitian predicates of the same shape")
        for pair in qpreB.opt_pairs:
            if not isinstance(pair, OptPairTerm):
                raise Exception("unexpected situation")
            if example_pair.qvarls != pair.qvarls:
                raise Exception("invalid usage, qpreA and qpreB must have hermitian predicates of the same shape")
            
        
        #print("begin SDP ...")

        # transform all the hermitian operators into matrices
        dim = 2**example_pair.qvarls_val.qnum
        msetA = [opt_kernel.tensor_to_matrix(qpreA.get_pair(i).opt_val.m) for i in range(len(qpreA))]

        for j in range(len(qpreB)):
            mB = opt_kernel.tensor_to_matrix(qpreB.get_pair(j).opt_val.m)

            X = cp.Variable((dim, dim), hermitian=True) # type: ignore
            constraints = [X >> 0]  # type: ignore
            constraints += [
                cp.real(cp.trace((mB - mA) @ X)) <= -Precision.EPS() for mA in msetA  # type: ignore
            ]
            prob = cp.Problem(cp.Minimize(0), constraints)  # type: ignore

            prob.solve(eps = opt_kernel.Precision.SDP_precision())

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



    
