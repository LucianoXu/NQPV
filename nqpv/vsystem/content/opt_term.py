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
# opt_term.py
#
# defining the operator terms, and their corresponding properties
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Tuple

from . import opt_kernel

from nqpv import dts

import numpy as np

fac = dts.TermFact()

type_operator = fac.axiom("operator", fac.sort_term(0))

class OperatorTerm(dts.Term):
    def __init__(self, m : np.ndarray):
        if not isinstance(m, np.ndarray):
            raise ValueError()

        super().__init__(type_operator, None)
        self._m : np.ndarray = m
        self._qnum : int | None = None
        self._unitary : bool | None = None
        self._hermitian_predicate : bool | None = None
        self._measurement : bool | None = None
    
    @property
    def m(self) -> np.ndarray:
        return self._m

    @property
    def qnum(self) -> int:
        if self._qnum is None:
            self._qnum = opt_kernel.get_opt_qnum(self._m)
        return self._qnum

    def ensure_unitary(self) -> None:
        self._unitary = True
    
    def ensure_hermitian_predicate(self) -> None:
        self._hermitian_predicate = True
    
    def ensure_measurement(self) -> None:
        self._measurement = True

    @property
    def unitary(self) -> bool:
        if self._unitary is None:
            self._unitary = opt_kernel.check_unity(self._m)
        return self._unitary

    @property
    def hermitian_predicate(self) -> bool:
        if self._hermitian_predicate is None:
            self._hermitian_predicate = opt_kernel.check_hermitian_predicate(self._m)
        return self._hermitian_predicate
    
    @property
    def measurement(self) -> bool:
        if self._measurement is None:
            self._measurement = opt_kernel.check_measure(self._m)
        return self._measurement
    
    def __eq__(self, other) -> bool:
        if isinstance(other, OperatorTerm):
            return opt_kernel.np_eps_equal(self._m, other._m)
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
    
    def __str__(self) -> str:
        return str(self._m)

    def dagger(self) -> OperatorTerm:
        '''
        return the dagger operator
        '''
        r = OperatorTerm(opt_kernel.dagger(self._m))
        if self.unitary:
            r.ensure_unitary()
        if self.hermitian_predicate:
            r.ensure_hermitian_predicate()
        return r

    def opt_mea0(self) -> OperatorTerm:
        '''
        return the operator for measurement result 0
        '''
        if not self.measurement:
            raise ValueError()
        return OperatorTerm(self._m[0])
    
    def opt_mea1(self) -> OperatorTerm:
        '''
        return the operator for measurement result 1
        '''
        if not self.measurement:
            raise ValueError()
        return OperatorTerm(self._m[1])

    def __add__(self, other : OperatorTerm) -> OperatorTerm:
        '''
        return the addition result
        (cannot automatically ensure any property)
        '''
        if not isinstance(other, OperatorTerm):
            raise ValueError()
        r = OperatorTerm(self._m + other._m)
        '''
        # check whether it is hermitian predicate
        if self.hermitian_predicate and other.hermitian_predicate:
            r.ensure_hermitian_predicate()
        '''
        return r

def val_opt(term : dts.Term) -> OperatorTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_operator:
        raise ValueError()

    val = term.eval()
    if not isinstance(val, OperatorTerm):
        raise Exception()
    return val