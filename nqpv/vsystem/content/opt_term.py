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

from ..var_scope import VVar

import numpy as np

class OperatorTerm(VVar):
    '''
    type of ordinary operators
    '''
    def __init__(self, m : np.ndarray):
        '''
        every operator must have a name
        '''

        if not isinstance(m, np.ndarray):
            raise ValueError()

        self._m : np.ndarray = m
        self._unitary : bool | None = None
        self._hermitian_predicate : bool | None = None
    

    @property
    def m(self) -> np.ndarray:
        return self._m

    @property
    def qnum(self) -> int:
        return opt_kernel.get_opt_qnum(self._m)

    def ensure_unitary(self) -> None:
        self._unitary = True
    
    def ensure_hermitian_predicate(self) -> None:
        self._hermitian_predicate = True
    
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
    
    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if isinstance(other, OperatorTerm):
            return opt_kernel.np_eps_equal(self._m, other._m)
        else:
            return False
    
    def __str__(self) -> str:
        # output according to its property
        if self.hermitian_predicate or self.unitary:
            return str(self._m.reshape((2**self.qnum, 2**self.qnum)))
        else:
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

    @property
    def str_type(self) -> str:
        return "operator " + str(self.qnum) + " qubit"


class MeasureTerm(VVar):
    '''
    The type of measurement operator sets.
    '''
    def __init__(self, m : np.ndarray):

        if not isinstance(m, np.ndarray):
            raise ValueError()

        self._m  : np.ndarray = m
        self._m0 : np.ndarray = m[0]
        self._m1 : np.ndarray = m[1]
    
    @property
    def m(self) -> np.ndarray:
        return self._m

    @property
    def m0(self) -> OperatorTerm:
        return OperatorTerm(self._m0)

    @property
    def m1(self) -> OperatorTerm:
        return OperatorTerm(self._m1)

    @property
    def qnum(self) -> int:
        return opt_kernel.get_opt_qnum(self._m0)
    
    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if isinstance(other, MeasureTerm):
            return opt_kernel.np_eps_equal(self._m, other._m)
        else:
            return False
    
    def __str__(self) -> str:
        # output according to its property
        s = "M0 : \n" + str(self._m0.reshape((2**self.qnum, 2**self.qnum)))\
            + "\nM1 : \n" + str(self._m1.reshape((2**self.qnum, 2**self.qnum))) + "\n"
        return s

    def dagger(self) -> MeasureTerm:
        '''
        return the dagger operator
        '''
        return MeasureTerm(opt_kernel.dagger(self._m))

    @property
    def str_type(self) -> str:
        return "measurement " + str(self.qnum) + " qubit"
