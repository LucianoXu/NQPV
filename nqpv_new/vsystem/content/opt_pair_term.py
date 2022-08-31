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
# opt_pair_term.py
#
# defining the operator-variable pair terms
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Tuple

from nqpv_new import dts

from nqpv_new.vsystem.log_system import RuntimeErrorWithLog

from .opt_term import OperatorTerm, type_operator
from .qvarls_term import QvarlsTerm, type_qvarls

fac = dts.TermFact()

type_opt_pair = fac.axiom("opt_pair", fac.sort_term(0))

class OptPairTerm(dts.Term):
    def __init__(self, opt : dts.Term, qvarls : dts.Term):

        if not isinstance(opt, dts.Term) or not isinstance(qvarls, dts.Term):
            raise ValueError()

        # check the terms
        if opt.type != type_operator:
            raise RuntimeErrorWithLog("The term '" + str(opt) + "' is not an operator.")
        if qvarls.type != type_qvarls:
            raise RuntimeErrorWithLog("The term '" + str(qvarls) + "' is not a quantum variable list")
        
        opt_val : OperatorTerm = opt.eval()  # type: ignore
        qvarls_val : QvarlsTerm = qvarls.eval() # type: ignore 

        # check the qubit number
        if opt_val.qnum != qvarls_val.qnum:
            raise RuntimeErrorWithLog("The operator '" + str(opt) + "' and the quantum variable list '" + 
                str(qvarls) + "' does not match on qubit numbers.")
        
        super().__init__(type_opt_pair, None)
        self._opt : dts.Term = opt
        self._qvarls : dts.Term = qvarls
    
    @property
    def opt(self) -> dts.Term:
        return self._opt
    
    @property
    def opt_val(self) -> OperatorTerm:
        temp = self._opt.eval()
        if not isinstance(temp, OperatorTerm):
            raise Exception("unexpected situation")
        return temp
    
    @property
    def qvarls(self) -> dts.Term:
        return self._qvarls

    @property
    def qvarls_val(self) -> QvarlsTerm:
        temp = self._qvarls.eval()
        if not isinstance(temp, QvarlsTerm):
            raise Exception("unexpected situation")
        return temp

    def eval(self) -> dts.Term:
        return OptPairTerm(self.opt.eval(), self.qvarls.eval())

    @property
    def unitary_pair(self) -> bool:
        return self._opt.eval().unitary # type: ignore
    
    @property
    def hermitian_predicate_pair(self) -> bool:
        return self._opt.eval().hermitian_predicate # type: ignore
    
    @property
    def measurement_pair(self) -> bool:
        return self._opt.eval().measurement # type: ignore

    def __eq__(self, other) -> bool:
        if isinstance(other, OptPairTerm):
            return self.opt == other.opt and self.qvarls == other.qvarls
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
    
    def __str__(self) -> str:
        return str(self.opt) + str(self.qvarls)