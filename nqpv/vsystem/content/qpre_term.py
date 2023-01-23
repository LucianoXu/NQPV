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

from nqpv.vsystem.content.opt_term import OperatorTerm

from nqpv.vsystem.log_system import RuntimeErrorWithLog
from nqpv.vsystem.var_scope import VVar, VarScope
from nqpv.vsystem.opt_kernel import tensor_to_matrix

from .qvarls_term import QvarlsTerm
from . import opt_pair_term
from .opt_pair_term import OptPairTerm, MeaPairTerm

import numpy as np
import cvxpy as cp

class QPreTerm(VVar):
    def __init__(self, opt_pairs : Tuple[VVar,...]):
        super().__init__()

        # check the terms
        if not isinstance(opt_pairs, tuple):
            raise ValueError()
        
        # remove the repeated pairs
        unique_pairs = []
        for pair in opt_pairs:
            if not isinstance(pair, OptPairTerm):
                raise RuntimeErrorWithLog("The term '" + str(pair) + "' is not an operator variable pair.")
            
            # check for hermitian predicate pair
            pair_val : OptPairTerm = pair
            if not pair_val.hermitian_predicate_pair:
                raise RuntimeErrorWithLog("The pair '" + str(pair) + "' is not a hermitian predicate pair.")
            
            if VarScope.cur_settings().IDENTICAL_VAR_CHECK:
                if pair not in unique_pairs:
                    unique_pairs.append(pair)
            else:
                unique_pairs.append(pair)
        
        self._opt_pairs : Tuple[OptPairTerm,...] = tuple(unique_pairs)
    
    @property
    def opt_pairs(self) -> Tuple[OptPairTerm,...]:
        return self._opt_pairs

    def __len__(self) -> int:
        return len(self._opt_pairs)

    def get_pair(self, i : int) -> OptPairTerm:
        return self._opt_pairs[i]

    @property
    def all_qvarls(self) -> QvarlsTerm:
        '''
        return all the quantum variables used in the predicate
        '''
        result = QvarlsTerm(())
        for i in range(len(self)):
            result = result.join(self.get_pair(i).qvarls)
        return result
    
    def str_content(self) -> str:
        '''
        get the string for the content only (for str(inv), for example)
        '''
        if len(self) == 0:
            return ""
        else:
            r = str(self._opt_pairs[0])
            for i in range(1, len(self)):
                r += " " + str(self._opt_pairs[i])
            return r

    def __str__(self) -> str:
        if len(self) == 0:
            return "{}"
        r = "{ " + self.str_content() +  " }"
        return r
    
    def union(self, other : QPreTerm) -> QPreTerm:
        '''
        union the two predicates to form a new predicate
        '''
        return QPreTerm(self._opt_pairs + other._opt_pairs)

    def qvar_subsitute(self, correspondence : Dict[str, str]) -> QPreTerm:
        new_pairs = []
        for i in range(len(self)):
            new_pairs.append(self.get_pair(i).qvar_substitute(correspondence))
        return QPreTerm(tuple(new_pairs))

    @staticmethod
    def sqsubseteq(qpreA : QPreTerm, qpreB : QPreTerm) -> None:
        '''
        checks the requirement of qpreA sqsubseteq_inf qpreB
        <automatic extension>
        '''
        if not isinstance(qpreA, QPreTerm) or not isinstance(qpreB, QPreTerm):
            raise ValueError()
        
        scope = VarScope.get_cur_scope()

        # auto extension
        all_qvarls = qpreA.all_qvarls.join(qpreB.all_qvarls)
        qpreA_val = qpre_extend(qpreA, all_qvarls)
        qpreB_val = qpre_extend(qpreB, all_qvarls)
        
        scope.report("Determining : ")
        scope.report(str(qpreA) + " <= " + str(qpreB) + "\n")

        # transform all the hermitian operators into matrices
        dim = 2**all_qvarls.qnum
        msetA = [tensor_to_matrix(qpreA_val.get_pair(i).opt.m) for i in range(len(qpreA_val))]

        for j in range(len(qpreB_val)):
            mB = tensor_to_matrix(qpreB_val.get_pair(j).opt.m)

            if len(msetA) == 1:
                # use eigen solver
                e_vals = np.linalg.eigvals(mB - msetA[0])   # type: ignore
                if np.any(e_vals < 0 - VarScope.cur_settings().EPS):
                    raise RuntimeErrorWithLog(
                        "\nOrder relation not satisfied: \n\t" + 
                        str(qpreA) + " <= " + str(qpreB) + "\n" +
                        "The operator '" + str(qpreB_val.get_pair(j)) + "' can be violated.\n" +
                        "This conclusion may be incorrect due to the precision settings:\n"+
                        "\t EPS : " + str(VarScope.cur_settings().EPS ) + "\n" +
                        "This relation may still hold with a trial of lower equivalence requirement.\n\n"
                    )
            else:
                # use SDP solver
                X = cp.Variable((dim, dim), hermitian=True) # type: ignore
                constraints = [X >> 0]  # type: ignore
                constraints += [
                    cp.real(cp.trace((mB - mA) @ X)) <= -VarScope.cur_settings().EPS for mA in msetA    # type: ignore
                ]
                prob = cp.Problem(cp.Minimize(0), constraints)  # type: ignore

                prob.solve(eps = VarScope.cur_settings().SDP_precision)

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
                    
                    sol_name = scope.append(OperatorTerm(sol))

                    raise RuntimeErrorWithLog(
                        "\nOrder relation not satisfied: \n\t" + 
                        str(qpreA) + " <= " + str(qpreB) + "\n" +
                        "The operator '" + str(qpreB_val.get_pair(j)) + "' can be violated.\n" +
                        "Density operator witnessed: '" + sol_name + "'.\n" +
                        "This conclusion may be incorrect due to the precision settings:\n"+
                        "\t EPS : " + str(VarScope.cur_settings().EPS ) + "\n" +
                        "\t SDP_PRECISION :" + str(VarScope.cur_settings().SDP_precision) + "\n" + 
                        "This relation may still hold with a trial of better SDP solver precision or lower equivalence requirement.\n\n"
                    )
                


def qpre_I(all_qvarls : QvarlsTerm) -> QPreTerm:
    scope = VarScope.get_cur_scope()

    if not isinstance(all_qvarls, QvarlsTerm):
        raise ValueError()
    new_pair = opt_pair_term.hermitian_I(all_qvarls)
    new_name = scope.append(new_pair.opt)
    new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
    return QPreTerm((new_pair,))


def qpre_contract(qpre : QPreTerm, M : OptPairTerm) -> QPreTerm:
    scope = VarScope.get_cur_scope()

    if not isinstance(qpre, QPreTerm) or not isinstance(M, OptPairTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_contract(qpre.get_pair(i), M)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))

def qpre_init(qpre : QPreTerm, qvarls : QvarlsTerm) -> QPreTerm:
    scope = VarScope.get_cur_scope()

    if not isinstance(qpre, QPreTerm) or not isinstance(qvarls, QvarlsTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_init(qpre.get_pair(i), qvarls)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))


def qpre_mea_proj_sum(qpre0 : QPreTerm, qpre1 : QPreTerm, 
        M : MeaPairTerm) -> QPreTerm:
    '''
    M should be the measurement operators
    '''
    scope = VarScope.get_cur_scope()

    if not isinstance(qpre0, QPreTerm) or not isinstance(qpre1, QPreTerm)\
        or not isinstance(M, MeaPairTerm):
        raise ValueError()
    
    M0 = M.mea0
    M1 = M.mea1
    pairs = []
    for i in range(len(qpre0)):
        for j in range(len(qpre1)):
            new_pair = opt_pair_term.hermitian_contract(
                qpre0.get_pair(i), M0
            ) + opt_pair_term.hermitian_contract(
                qpre1.get_pair(j), M1
            )
            new_pair.opt.ensure_hermitian_predicate()
            new_name = scope.append(new_pair.opt)
            new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
            pairs.append(new_pair)

    return QPreTerm(tuple(pairs))
    


def qpre_extend(qpre : QPreTerm, all_qvarls : QvarlsTerm) -> QPreTerm:
    scope = VarScope.get_cur_scope()

    if not isinstance(qpre, QPreTerm) or not isinstance(all_qvarls, QvarlsTerm):
        raise ValueError()
    pairs = []
    for i in range(len(qpre)):
        new_pair = opt_pair_term.hermitian_extend(qpre.get_pair(i), all_qvarls)
        new_name = scope.append(new_pair.opt)
        new_pair = OptPairTerm(scope[new_name], new_pair.qvarls)
        pairs.append(new_pair)
    
    return QPreTerm(tuple(pairs))


    
