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
from .opt_env import Operator, OptEnv
from .qVar import QvarLs
from .opt_qvar_pair import OptQvarPair

from ..logsystem import LogSystem
from ..syntaxes.pos_info import PosInfo

class QPredicate:

    def __new__(cls, data : OptQvarPair | QPredicate | None | List):

        if data is None:
            LogSystem.channels["error"].append("The operator variable pair for the predicate is invalid.")
            return None

        if isinstance(data, QPredicate):
            instance = super().__new__(cls)
            instance.opts = data.opts
            instance.pos = data.pos
            return instance

        elif isinstance(data, OptQvarPair):
            if not data.check_property("hermitian predicate"):
                LogSystem.channels["error"].append("The provided operator variable pair is not 'hermitian predicate'." + PosInfo.str(data.pos))
                return None

            instance = super().__new__(cls)
            instance.opts = (data,)
            instance.pos = data.pos
            return instance
        elif data == []:
            instance = super().__new__(cls)
            instance.opts = ()
            instance.pos = None
            return instance
        else:
            raise Exception("unexpected situation")

    def __init__(self, data : OptQvarPair | QPredicate | None | List):
        '''
        <may return None if construction failes>
        '''
        self.opts : Tuple[OptQvarPair,...] 
        self.pos : PosInfo | None

    @staticmethod
    def append(obj : QPredicate | None, pair: OptQvarPair | None) -> QPredicate | None:
        if obj is None:
            LogSystem.channels["error"].append("The quantum predicate provided here is invalid.")
            return None
        if pair is None:
            LogSystem.channels["error"].append("The next hermitian predicate provided here is invalid." + PosInfo.str(obj.pos))
            return None


        if not pair.check_property("hermitian predicate"):
            LogSystem.channels["error"].append("The operator variable pair for the quantum predicate is not 'hermitian predicate'." + PosInfo.str(obj.pos))
            return None

        result = QPredicate(obj)

        # check whether this pair has been in the list
        if pair in obj.opts:
            return result
        else:
            result.opts = obj.opts + (pair,)
            if result.pos is None:
                result.pos = pair.pos
            return result

    def __str__(self) -> str:
        r = "{ " + str(self.opts[0])
        for i in range(1, len(self.opts)):
            r += " " + str(self.opts[i])
        r += " }"
        return r

    @property
    def inv_str(self) -> str:
        '''
        return the string as a loop invariant
        '''
        r = "{ inv: " + str(self.opts[0])
        for i in range(1, len(self.opts)):
            r += " " + str(self.opts[i])
        r += " }"
        return r

    def full_extension(self) -> QPredicate:
        '''
        return a quantum predicate with all hermitian operators fully extended
        '''
        r = QPredicate([])
        for herm_pair in self.opts:
            m = hermitian_extend(tuple(QvarLs.qvar), herm_pair.opt.data.data, herm_pair.qvls.data)
            name = OptEnv.append(m)
            opt = OptQvarPair(
                Operator(OptEnv.lib[name], None),
                QvarLs("qvar", None),
                "",
                herm_pair
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
        msetA = [pre.opt.data.data.reshape((dim, dim)) for pre in preA.opts]

        for opt_b in preB.opts:
            mB = opt_b.opt.data.data.reshape((dim, dim))
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
                # require this opt
                OptEnv.use_opt(sol_name, None)

                LogSystem.channels["witness"].append(
                    "\nOrder relation not satisfied: \n\t" + 
                    str(preA) + " <= " + str(preB) + "\n"+
                    "The operator '" + str(opt_b) + "' can be violated.\n"+
                    "Density operator witnessed: '" + sol_name + "'.\n"
                    + PosInfo.str(preA.pos) + PosInfo.str(preB.pos)
                )
                return False

        return True
            

