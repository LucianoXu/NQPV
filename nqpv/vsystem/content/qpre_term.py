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
from typing import Any, List, Tuple, Dict

from nqpv import dts

from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm
from . import opt_kernel
from .opt_kernel import Precision
from . import opt_pair_term
from .opt_pair_term import OptPairTerm, type_opt_pair
from .scope_term import ScopeTerm

import numpy as np
import cvxpy as cp

fac = dts.TermFact()

type_qpre = fac.axiom("qpre", fac.sort_term(0))

class QPreTerm(dts.Term):
    def __init__(self, opt_pairs : Tuple[dts.Term,...]):
        # check the terms
        if not isinstance(opt_pairs, tuple):
            raise ValueError()
        
        # remove the repeated pairs
        unique_pairs = []
        for pair in opt_pairs:
            if not isinstance(pair, dts.Term):
                raise ValueError()
            if pair.type != type_opt_pair:
                raise RuntimeErrorWithLog("The term '" + str(pair) + "' is not an operator variable pair.")
            
            # check for hermitian predicate pair
            pair_val : OptPairTerm = pair.eval() # type: ignore
            if not pair_val.hermitian_predicate_pair:
                raise RuntimeErrorWithLog("The pair '" + str(pair) + "' is not a hermitian predicate pair.")
            
            if pair not in unique_pairs:
                unique_pairs.append(pair)
        
        super().__init__(type_qpre, None)
        self._opt_pairs : Tuple[dts.Term,...] = tuple(unique_pairs)
    
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
    
    @property
    def all_qvarls(self) -> QvarlsTerm:
        '''
        return all the quantum variables used in the predicate
        '''
        result = QvarlsTerm(())
        for i in range(len(self)):
            result = result.join(self.get_pair(i).qvarls_val)
        return result

    def __str__(self) -> str:
        if len(self) == 0:
            return "{}"
        r = "{ " + str(self._opt_pairs[0])
        for i in range(1, len(self)):
            r += " " + str(self._opt_pairs[i])
        r += " }"
        return r
    
    def union(self, other : dts.Term) -> QPreTerm:
        '''
        union the two predicates to form a new predicate
        '''
        other_val = val_qpre(other)
        return QPreTerm(self._opt_pairs + other_val._opt_pairs)

    def qvar_subsitute(self, correspondence : Dict[str, str]) -> QPreTerm:
        new_pairs = []
        for i in range(len(self)):
            new_pairs.append(self.get_pair(i).qvar_substitute(correspondence))
        return QPreTerm(tuple(new_pairs))

    @staticmethod
    def sqsubseteq(qpreA : dts.Term, qpreB : dts.Term, scope : ScopeTerm) -> None:
        '''
        checks the requirement of qpreA sqsubseteq_inf qpreB
        <automatic extension>
        '''
        if not isinstance(qpreA, dts.Term) or not isinstance(qpreB, dts.Term) or not isinstance(scope, ScopeTerm):
            raise ValueError()
        
        # evaluate the expressions
        qpreA_val : QPreTerm = val_qpre(qpreA)
        qpreB_val : QPreTerm = val_qpre(qpreB)
        
        # auto extension
        all_qvarls = qpreA_val.all_qvarls.join(qpreB_val.all_qvarls)
        qpreA_val = qpre_extend(qpreA_val, all_qvarls, scope)
        qpreB_val = qpre_extend(qpreB_val, all_qvarls, scope)
        
        #print("begin SDP ...")

        # transform all the hermitian operators into matrices
        dim = 2**all_qvarls.qnum
        msetA = [opt_kernel.tensor_to_matrix(qpreA_val.get_pair(i).opt_val.m) for i in range(len(qpreA_val))]

        for j in range(len(qpreB_val)):
            mB = opt_kernel.tensor_to_matrix(qpreB_val.get_pair(j).opt_val.m)

            X = cp.Variable((dim, dim), hermitian=True) # type: ignore
            constraints = [X >> 0]  # type: ignore
            constraints += [
                cp.real(cp.trace((mB - mA) @ X)) <= -Precision.EPS() for mA in msetA    # type: ignore
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

def val_qpre(term : dts.Term) -> QPreTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_qpre:
        raise ValueError()
        
    val = term.eval()
    if not isinstance(val, QPreTerm):
        raise Exception()
    return val



def qpre_I(all_qvarls : QvarlsTerm, scope : ScopeTerm) -> QPreTerm:
    if not isinstance(all_qvarls, QvarlsTerm) or not isinstance(scope, ScopeTerm):
        raise ValueError()
    new_pair = opt_pair_term.hermitian_I(all_qvarls)
    new_name = scope.append(new_pair.opt)
    new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
    return QPreTerm((new_pair,))


def qpre_contract(qpre : QPreTerm, M : OptPairTerm, scope : ScopeTerm) -> QPreTerm:
    if not isinstance(qpre, QPreTerm) or not isinstance(M, OptPairTerm) or not isinstance(scope,ScopeTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_contract(qpre.get_pair(i), M)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))

def qpre_init(qpre : QPreTerm, qvarls : QvarlsTerm, scope : ScopeTerm) -> QPreTerm:
    if not isinstance(qpre, QPreTerm) or not isinstance(qvarls, QvarlsTerm) or not isinstance(scope, ScopeTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_init(qpre.get_pair(i), qvarls)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))

def qpre_mea_proj_sum(qpre0 : QPreTerm, qpre1 : QPreTerm, M : OptPairTerm, scope : ScopeTerm) -> QPreTerm:
    '''
    M should be the measurement operators
    '''
    if not isinstance(qpre0, QPreTerm) or not isinstance(qpre1, QPreTerm)\
        or not isinstance(M, OptPairTerm) or not isinstance(scope, ScopeTerm):
        raise ValueError()

    if not M.measurement_pair:
        raise ValueError()
    
    M0 = M.opt_mea0()
    M1 = M.opt_mea1()
    pairs = []
    for i in range(len(qpre0)):
        for j in range(len(qpre1)):
            new_pair = opt_pair_term.hermitian_contract(
                qpre0.get_pair(i), M0
            ) + opt_pair_term.hermitian_contract(
                qpre1.get_pair(j), M1
            )
            new_pair.opt_val.ensure_hermitian_predicate()
            new_name = scope.append(new_pair.opt)
            new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
            pairs.append(new_pair)

    return QPreTerm(tuple(pairs))
    


def qpre_extend(qpre : QPreTerm, all_qvarls : QvarlsTerm, scope : ScopeTerm) -> QPreTerm:
    if not isinstance(qpre, QPreTerm) or not isinstance(all_qvarls, QvarlsTerm) or not isinstance(scope, ScopeTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_extend(qpre.get_pair(i), all_qvarls)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))


    
