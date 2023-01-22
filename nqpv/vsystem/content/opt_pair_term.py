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

from nqpv.vsystem.var_scope import VVar
from nqpv.vsystem.log_system import RuntimeErrorWithLog
from nqpv.vsystem import opt_kernel

from .qvarls_term import QvarlsTerm
from .opt_term import OperatorTerm, MeasureTerm



class OptPairTerm(VVar):
    def __init__(self, opt : VVar, qvarls : QvarlsTerm):
        super().__init__()

        if not isinstance(opt, OperatorTerm):
            raise RuntimeErrorWithLog("The term '" + opt.name + "' is not an operator.")
        
        if not isinstance(qvarls, QvarlsTerm):
            raise RuntimeErrorWithLog("The term '" + str(qvarls) + "' is not a quantum variable list")
        
        try:
            opt.qnum
        except ValueError:
            raise RuntimeErrorWithLog("The operator '" + opt.name + "' can not be used here. All indices must be 2 valued.")


        # check the qubit number
        if opt.qnum != qvarls.qnum:
            raise RuntimeErrorWithLog("The operator '" + opt.name + "' and the quantum variable list '" + 
                str(qvarls) + "' does not match on qubit numbers.")
        
        self._opt : OperatorTerm = opt
        self._qvarls : QvarlsTerm = qvarls
    
    @property
    def str_type(self) -> str:
        return "opt_pair " + str(self.qvarls.qnum) + " qubit"

    @property
    def opt(self) -> OperatorTerm:
        return self._opt
    
    @property
    def qvarls(self) -> QvarlsTerm:
        return self._qvarls

    @property
    def unitary_pair(self) -> bool:
        return self.opt.unitary
    
    @property
    def hermitian_predicate_pair(self) -> bool:
        return self.opt.hermitian_predicate
    
    def __eq__(self, other) -> bool:
            if isinstance(other, OptPairTerm):
                return self.opt == other.opt and self.qvarls == other.qvarls
            else:
                return False    

    def __str__(self) -> str:
        return self.opt.name + str(self.qvarls)

    def dagger(self) -> OptPairTerm:
        '''
        return the dagger operator
        '''
        return OptPairTerm(self.opt.dagger(), self._qvarls)
    
    def __add__(self, other : OptPairTerm) -> OptPairTerm:
        '''
        <automatic extension> for hermitian pairs
        '''
        if not isinstance(other, OptPairTerm):
            raise ValueError()
        if self.qvarls != other.qvarls:
            # automatic extension for hermitian pairs
            if self.hermitian_predicate_pair and other.hermitian_predicate_pair:
                all_qvarls = self.qvarls.join(other.qvarls)
                new_self = hermitian_extend(self, all_qvarls)
                new_other = hermitian_extend(other, all_qvarls)
                return OptPairTerm(new_self.opt + new_other.opt, all_qvarls)
            else:
                raise ValueError()
        else:
            return OptPairTerm(self.opt + other.opt, self.qvarls)

    def qvar_substitute(self, correspondence : Dict[str, str]) -> OptPairTerm:
        return OptPairTerm(self._opt, self.qvarls.qvar_substitute(correspondence))

class MeaPairTerm(VVar):
    def __init__(self, mea : VVar, qvarls : QvarlsTerm):
        super().__init__()

        if not isinstance(mea, MeasureTerm):
            raise RuntimeErrorWithLog("The term '" + str(mea) + "' is not a measurement.")
        
        if not isinstance(qvarls, QvarlsTerm):
            raise RuntimeErrorWithLog("The term '" + str(qvarls) + "' is not a quantum variable list")

        try:
            mea.qnum
        except ValueError:
            raise RuntimeErrorWithLog("The operator '" + str(mea) + "' can not be used here. All indices must be 2 valued.")


        # check the qubit number
        if mea.qnum != qvarls.qnum:
            raise RuntimeErrorWithLog("The operator '" + str(mea) + "' and the quantum variable list '" + 
                str(qvarls) + "' does not match on qubit numbers.")
        
        self._mea : MeasureTerm = mea
        self._qvarls : QvarlsTerm = qvarls

    @property
    def str_type(self) -> str:
        return "opt_pair " + str(self.qvarls.qnum) + " qubit"

    @property
    def mea(self) -> MeasureTerm:
        return self._mea

    @property
    def mea0(self) -> OptPairTerm:
        return OptPairTerm(self.mea.m0, self.qvarls)

    @property
    def mea1(self) -> OptPairTerm:
        return OptPairTerm(self.mea.m1, self.qvarls)
    
    @property
    def qvarls(self) -> QvarlsTerm:
        return self._qvarls

    def __eq__(self, other) -> bool:
        raise NotImplemented
    
    def __str__(self) -> str:
        return self.mea.name + str(self.qvarls)

    def dagger(self) -> MeaPairTerm:
        '''
        return the dagger operator
        '''
        return MeaPairTerm(self.mea.dagger(), self._qvarls)


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
    if not H.qvarls.cover(M.qvarls):
        extended_qvarls = H.qvarls.join(M.qvarls)
        H = hermitian_extend(H, extended_qvarls)

    new_m = opt_kernel.hermitian_contract(H.qvarls.vls, H.opt.m, M.qvarls.vls, M.opt.m)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, H.qvarls)

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
    if not H.qvarls.cover(qvarls):
        extended_qvarls = H.qvarls.join(qvarls)
        H = hermitian_extend(H, extended_qvarls)

    new_m = opt_kernel.hermitian_init(H.qvarls.vls, H.opt.m, qvarls.vls)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, H.qvarls)

def hermitian_extend(H : OptPairTerm, all_qvarls : QvarlsTerm) -> OptPairTerm:
    '''
    scope : the scope to preserve the newly created operators
    '''
    if not isinstance(H, OptPairTerm) or not isinstance(all_qvarls, QvarlsTerm):
        raise ValueError()
    if not H.hermitian_predicate_pair:
        raise RuntimeErrorWithLog("The operator variable pair '" + str(H) + "' is not a hermitian predicate pair.")
    
    if not all_qvarls.cover(H.qvarls):
        raise RuntimeErrorWithLog("The variable list of '" + str(H) + "' must be covered by the quantum variable list '" + str(all_qvarls) + "' to expand to.")

    # check whether extend is unnecessary
    if all_qvarls == H.qvarls:
        return H

    new_m = opt_kernel.hermitian_extend(all_qvarls.vls,  H.opt.m, H.qvarls.vls)
    new_opt = OperatorTerm(new_m)
    new_opt.ensure_hermitian_predicate()

    return OptPairTerm(new_opt, all_qvarls)