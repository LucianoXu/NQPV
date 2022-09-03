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
from typing import Any, List, Tuple, Dict

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

from . import opt_kernel
from .qvarls_term import QvarlsTerm, type_qvarls, val_qvarls
from .opt_term import OperatorTerm, type_operator, val_opt
from .scope_term import ScopeTerm

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
        
        opt_val : OperatorTerm = val_opt(opt)
        qvarls_val : QvarlsTerm = val_qvarls(qvarls)

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
        return val_opt(self._opt)
    
    @property
    def qvarls(self) -> dts.Term:
        return self._qvarls

    @property
    def qvarls_val(self) -> QvarlsTerm:
        return val_qvarls(self._qvarls)

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

    def dagger(self) -> OptPairTerm:
        '''
        return the dagger operator
        '''
        return OptPairTerm(self.opt_val.dagger(), self._qvarls)

    def opt_mea0(self) -> OptPairTerm:
        '''
        return the operator for measurement result 0
        '''
        return OptPairTerm(self.opt_val.opt_mea0(), self._qvarls)
    
    def opt_mea1(self) -> OptPairTerm:
        '''
        return the operator for measurement result 1
        '''
        return OptPairTerm(self.opt_val.opt_mea1(), self._qvarls)
    
    def __add__(self, other : OptPairTerm) -> OptPairTerm:
        '''
        <automatic extension> for hermitian pairs
        '''
        if not isinstance(other, OptPairTerm):
            raise ValueError()
        if self.qvarls != other.qvarls:
            # automatic extension for hermitian pairs
            if self.hermitian_predicate_pair and other.hermitian_predicate_pair:
                all_qvarls = self.qvarls_val.join(other.qvarls_val)
                new_self = hermitian_extend(self, all_qvarls)
                new_other = hermitian_extend(other, all_qvarls)
                return OptPairTerm(new_self.opt_val + new_other.opt_val, all_qvarls)
            else:
                raise ValueError()
        else:
            return OptPairTerm(self.opt_val + other.opt_val, self.qvarls)

    def qvar_substitute(self, correspondence : Dict[str, str]) -> OptPairTerm:
        return OptPairTerm(self._opt, self.qvarls_val.qvar_substitute(correspondence))

def val_opt_pair(term : dts.Term) -> OptPairTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_opt_pair:
        raise ValueError()

    if isinstance(term, OptPairTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, OptPairTerm):
            raise Exception()
        return val
    else:
        raise Exception()

def hermitian_I(all_qvarls : QvarlsTerm) -> OptPairTerm:
    if not isinstance(all_qvarls, QvarlsTerm):
        raise ValueError()
    # produce the I operator
    m = opt_kernel.eye_tensor(len(all_qvarls))
    opt = OperatorTerm(m)
    opt.ensure_hermitian_predicate()
    opt.ensure_unitary()
    return OptPairTerm(opt, all_qvarls)


def hermitian_contract(H : OptPairTerm, M : OptPairTerm) -> OptPairTerm:
    '''
    scope : the scope to preserve the newly created operators
    <automatic extension>
    '''
    if not isinstance(H, OptPairTerm) or not isinstance(M, OptPairTerm):
        raise ValueError()
    if not H.hermitian_predicate_pair:
        raise RuntimeErrorWithLog("The operator variable pair '" + str(H) + "' is not a hermitian predicate pair.")
    
    # automatic extension
    if not H.qvarls_val.cover(M.qvarls_val):
        extended_qvarls = H.qvarls_val.join(M.qvarls_val)
        H = hermitian_extend(H, extended_qvarls)

    new_m = opt_kernel.hermitian_contract(H.qvarls_val.vls, H.opt_val.m, M.qvarls_val.vls, M.opt_val.m)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, H.qvarls_val)

def hermitian_init(H : OptPairTerm, qvarls : QvarlsTerm) -> OptPairTerm:
    '''
    scope : the scope to preserve the newly created operators
    <automatic extension>
    '''
    if not isinstance(H, OptPairTerm) or not isinstance(qvarls, QvarlsTerm):
        raise ValueError()
    if not H.hermitian_predicate_pair:
        raise RuntimeErrorWithLog("The operator variable pair '" + str(H) + "' is not a hermitian predicate pair.")
    
    # automatic extension
    if not H.qvarls_val.cover(qvarls):
        extended_qvarls = H.qvarls_val.join(qvarls)
        H = hermitian_extend(H, extended_qvarls)

    new_m = opt_kernel.hermitian_init(H.qvarls_val.vls, H.opt_val.m, qvarls.vls)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, H.qvarls_val)

def hermitian_extend(H : OptPairTerm, all_qvarls : QvarlsTerm) -> OptPairTerm:
    '''
    scope : the scope to preserve the newly created operators
    '''
    if not isinstance(H, OptPairTerm) or not isinstance(all_qvarls, QvarlsTerm):
        raise ValueError()
    if not H.hermitian_predicate_pair:
        raise RuntimeErrorWithLog("The operator variable pair '" + str(H) + "' is not a hermitian predicate pair.")
    
    if not all_qvarls.cover(H.qvarls_val):
        raise RuntimeErrorWithLog("The variable list of '" + str(H) + "' must be covered by the quantum variable list '" + str(all_qvarls) + "' to expand to.")

    new_m = opt_kernel.hermitian_extend(all_qvarls.vls,  H.opt_val.m, H.qvarls_val.vls)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, all_qvarls)