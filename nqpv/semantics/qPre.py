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
# qpre.py
#
# quantum predicates
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple

import numpy as np
import cvxpy as cp

from .qLA import Precision, hermitian_extend
from .optEnv import Operator, OptEnv
from .qVar import QvarLs
from .optQvarPair import OptQvarPair

from ..logsystem import LogSystem

# channel of semantic analysis
channel : str = "semantics"
# define the channel to save the witness
channel_witness = "witness"

class QPredicate:

    def __new__(cls, data : OptQvarPair | QPredicate | None | List):

        if data is None:
            LogSystem.channels[channel].append("The operator - variable pair provided here is invalid.")
            return None

        if isinstance(data, QPredicate):
            instance = super().__new__(cls)
            instance.opts = data.opts
            return instance

        elif isinstance(data, OptQvarPair):
            if not data.check_property("hermitian predicate"):
                LogSystem.channels[channel].append("The provided operator qvls pair is not 'hermitian predicate'.")
                return None

            instance = super().__new__(cls)
            instance.opts = (data,)
            return instance
        elif data == []:
            instance = super().__new__(cls)
            instance.opts = ()
            return instance
        else:
            raise Exception("unexpected situation")

    def __init__(self, data : OptQvarPair | QPredicate | None | List):
        '''
        <may return None if construction failes>
        '''
        self.opts : Tuple[OptQvarPair,...] 

    @staticmethod
    def append(obj : QPredicate | None, pair: OptQvarPair | None) -> QPredicate | None:
        if pair is None or obj is None:
            LogSystem.channels[channel].append("The components provided here are invalid.")
            return None


        if not pair.check_property("hermitian predicate"):
            LogSystem.channels[channel].append("The provided operator qvls pair is not 'hermitian predicate'.")
            return None

        result = QPredicate(obj)
        result.opts = obj.opts + (pair,)
        return result

    def __str__(self) -> str:
        r = "{ " + str(self.opts[0])
        for i in range(1, len(self.opts)):
            r += " " + str(self.opts[i])
        r += " }"
        return r

    def full_extension(self) -> QPredicate:
        '''
        return a quantum predicate with all hermitian operators fully extended
        '''
        r = QPredicate([])
        for i in range(len(self.opts)):
            m = hermitian_extend(tuple(QvarLs.qvar), self.opts[i].opt.data, self.opts[i].qvls.data)
            name = OptEnv.append(m)
            opt = OptQvarPair(
                OptEnv.lib[name],
                QvarLs("qvar")
            )
            r = QPredicate.append(
                r, 
                opt
            )
        if r is None:
            raise Exception("unexpected situation")

        return r


    @staticmethod
    def sqsubseteq(preA: QPredicate, preB: QPredicate) -> bool:
        '''
        decide the partial order of Hermitian operator sets, using SDP
        preA, preB: list of hermitian operators, in numpy array form, with shape of (2,2,2,2,...)
            These hermitian operators should have been examinated already.
        return: True if preA 'sqsubseteq' preB, else False.
        '''
        # for now we only allow operator variable pairs of full extension
        for pre in preA.opts:
            if not pre.qvls.isfull():
                raise Exception("not full quantum variable list.")
        for pre in preB.opts:
            if not pre.qvls.isfull():
                raise Exception("not full quantum variable list.")

        # transform all the hermitian operators into matrices
        qubitn = len(QvarLs.qvar)
        dim = 2**qubitn
        msetA = [pre.opt.data.reshape((dim, dim)) for pre in preA.opts]
        msetB = [pre.opt.data.reshape((dim, dim)) for pre in preB.opts]

        for mB in msetB:
            X = cp.Variable((dim, dim), hermitian=True) # type: ignore
            constraints = [X >> 0]  # type: ignore
            constraints += [
                cp.real(cp.trace((mB - mA) @ X)) <= -Precision.EPS() for mA in msetA  # type: ignore
            ]
            prob = cp.Problem(cp.Minimize(0), constraints)  # type: ignore
            prob.solve(eps = Precision.EPS()/10)

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

                sol_name = OptEnv.append(sol, "", False)

                LogSystem.channels[channel_witness].append(
                    "Order relation not satisfied. Density operator witnessed: " + sol_name + ".\n"
                )
                return False

        return True
            

