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
# proof_hint_term.py
#
# define the proof hint terms
# ------------------------------------------------------------

from __future__ import annotations
from typing import List, Tuple

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm, type_qvarls, val_qvarls
from .opt_pair_term import OptPairTerm, type_opt_pair, val_opt_pair
from . import qpre_term
from .qpre_term import QPreTerm, type_qpre, val_qpre
from .scope_term import ScopeTerm

from .proof_term import type_proof, ProofDefinedTerm, val_proof

fac = dts.TermFact()
type_proof_hint = fac.axiom("proof_hint", fac.sort_term(0))

class ProofHintTerm(dts.Term):
    def __init__(self, all_qvarls : QvarlsTerm):
        val_qvarls(all_qvarls)

        super().__init__(type_proof_hint, None)
        self._all_qvarls : QvarlsTerm = all_qvarls

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls
    
    def prog_consistent(self, other : ProofHintTerm) -> bool:
        '''
        check whether the two proof hints are about the same program (syntactically)
        '''
        raise NotImplementedError()

    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"
    
def val_proof_hint(term : dts.Term) -> ProofHintTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_proof_hint:
        raise ValueError()
        
    if isinstance(term, ProofHintTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProofHintTerm):
            raise Exception()
        return val
    else:
        raise Exception()

class SkipHintTerm(ProofHintTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        return isinstance(other, SkipHintTerm)

    def str_content(self, prefix: str) -> str:
        return prefix + "skip"

class AbortHintTerm(ProofHintTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        return isinstance(other, AbortHintTerm)

    def str_content(self, prefix: str) -> str:
        return prefix + "abort"

class InitHintTerm(ProofHintTerm):
    def __init__(self, qvarls : dts.Term):
        if not isinstance(qvarls, dts.Term):
            raise ValueError()
        if qvarls.type != type_qvarls:
            raise RuntimeErrorWithLog("The term '" + str(qvarls) + "' is not a quantum variable list.")
        
        qvarls_val = val_qvarls(qvarls)

        super().__init__(qvarls_val)
        self._qvarls : dts.Term = qvarls

    @property
    def qvarls_val(self) -> QvarlsTerm:
        return val_qvarls(self._qvarls)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, InitHintTerm):
            return self._qvarls == other._qvarls
        else:
            return False

    def str_content(self, prefix: str) -> str:
        return prefix + str(self._qvarls) + " :=0"

class UnitaryHintTerm(ProofHintTerm):
    def __init__(self, opt_pair : dts.Term):
        if not isinstance(opt_pair, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a operator variable pair.")
        opt_pair_val = val_opt_pair(opt_pair)
        if not opt_pair_val.unitary_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not an unitary pair.")
        
        all_qvarls = opt_pair_val.qvarls_val
        super().__init__(all_qvarls)
        self._opt_pair : dts.Term = opt_pair

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, UnitaryHintTerm):
            return self._opt_pair == other._opt_pair
        else:
            return False

    def str_content(self, prefix: str) -> str:
        return prefix + str(self.opt_pair_val._qvarls) + " *= " + str(self.opt_pair_val._opt)

class IfHintTerm(ProofHintTerm):
    def __init__(self, opt_pair : dts.Term, P1 : dts.Term, P0 : dts.Term):
        if not isinstance(opt_pair, dts.Term) or not isinstance(P0, dts.Term) or not isinstance(P1, dts.Term):
            raise ValueError()
        # check the measurement
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a operator variable pair.")
        opt_pair_val = val_opt_pair(opt_pair)
        if not opt_pair_val.measurement_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not a measurement set pair.")

        if P0.type != type_proof_hint:
            raise RuntimeErrorWithLog("The term '" + str(P0) + "' is not a proof hint.")
        if P1.type != type_proof_hint:
            raise RuntimeErrorWithLog("The term '" + str(P1) + "' is not a proof hint.")
        
        P0_val = val_proof_hint(P0)
        P1_val = val_proof_hint(P1)
        
        all_qvarls = opt_pair_val.qvarls_val
        all_qvarls = all_qvarls.join(P0_val.all_qvarls)
        all_qvarls = all_qvarls.join(P1_val.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : dts.Term = opt_pair
        self._P0 : dts.Term = P0
        self._P1 : dts.Term = P1

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P0_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P0)
    
    @property
    def P1_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P1)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, IfHintTerm):
            return self._opt_pair == other._opt_pair\
                and self.P1_val.prog_consistent(other.P1_val)\
                and self.P0_val.prog_consistent(other.P0_val)
        else:
            return False

    def str_content(self, prefix: str) -> str:
        r = prefix + "if " + str(self._opt_pair) + " then\n"
        r += self.P1_val.str_content(prefix + "\t") + "\n"
        r += prefix + "else\n"
        r += self.P0_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class WhileHintTerm(ProofHintTerm):
    def __init__(self, inv : dts.Term, opt_pair : dts.Term, P : dts.Term):
        if not isinstance(inv, dts.Term) or not isinstance(opt_pair, dts.Term) or not isinstance(P, dts.Term):
            raise ValueError()
        # check the measurement
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a operator variable pair.")
        opt_pair_val = val_opt_pair(opt_pair)
        if not opt_pair_val.measurement_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not a measurement set pair.")
        
        # check loop invariant
        if inv.type != type_qpre:
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a predicate, while a loop invariant is needed.")

        if P.type != type_proof_hint:
            raise RuntimeErrorWithLog("The term '" + str(P) + "' is not a proof hint.")

        P_val = val_proof_hint(P)
        
        all_qvarls = opt_pair_val.qvarls_val
        all_qvarls = all_qvarls.join(P_val.all_qvarls)
        super().__init__(all_qvarls)
        self._inv : dts.Term = inv
        self._opt_pair : dts.Term = opt_pair
        self._P : dts.Term = P

    @property
    def inv_val(self) -> QPreTerm:
        return val_qpre(self._inv)

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, WhileHintTerm):
            return self._opt_pair == other._opt_pair\
                and self.P_val.prog_consistent(other.P_val)
        else:
            return False
    
    def str_content(self, prefix: str) -> str:
        r = prefix + "{ inv: " + self.inv_val.str_content() + "};\n"
        r += prefix + "while " + str(self._opt_pair) + " do\n"
        r += self.P_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class NondetHintTerm(ProofHintTerm):
    def __init__(self, proof_hints : Tuple[dts.Term, ...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, dts.Term):
                raise ValueError()
            if item.type != type_proof_hint:
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            item_val = val_proof_hint(item)
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        super().__init__(all_qvarls)
        self._proof_hints : Tuple[dts.Term,...] = proof_hints
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, NondetHintTerm):
            if len(self._proof_hints) != len(other._proof_hints):
                return False
            for i in range(len(self._proof_hints)):
                if not self.get_proof_hint(i).prog_consistent(other.get_proof_hint(i)):
                    return False
            return True
        else:
            return False

    def str_content(self, prefix: str) -> str:
        r = prefix + "(\n"
        r += self.get_proof_hint(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._proof_hints)):
            r += prefix + "#\n"
            r += self.get_proof_hint(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r

class SubproofHintTerm(ProofHintTerm):
    def __init__(self, subproof : dts.Term, arg_ls : dts.Term):
        # note: we need subproof to be a dts.Var
        if not isinstance(subproof, dts.Var) or not isinstance(arg_ls, dts.Term):
            raise ValueError()
        
        if subproof.type != type_proof:
            raise RuntimeErrorWithLog("The term '" + str(subproof) + "' is not a subproof.")
        
        arg_ls_val = val_qvarls(arg_ls)
        super().__init__(arg_ls_val)
        self._subproof : dts.Var = subproof
        self._arg_ls : dts.Term = arg_ls

    @property
    def subproof_val(self) -> ProofDefinedTerm:
        return val_proof(self._subproof)
    
    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, SubproofHintTerm):
            subproof_self = val_proof(self._subproof)
            subproof_other = val_proof(other._subproof)
            hint_self = val_proof_hint(subproof_self._proof_hint)
            hint_other = val_proof_hint(subproof_other._proof_hint)

            subprog_consistent = hint_self.prog_consistent(hint_other)\
                and subproof_self._arg_ls == subproof_other._arg_ls

            return subprog_consistent and self._arg_ls == other._arg_ls
        else:
            return False
    
    def str_content(self, prefix: str) -> str:
        # we need to reserve the variable name
        return prefix + str(self._subproof) + " " + str(self.arg_ls_val)
    
class QPreHintTerm(ProofHintTerm):
    def __init__(self, qpre : dts.Term):
        if not isinstance(qpre, dts.Term):
            raise ValueError()
        if qpre.type != type_qpre:
            raise ValueError()
        
        qpre_val = val_qpre(qpre)

        super().__init__(qpre_val.all_qvarls)
        self._qpre : dts.Term = qpre_val

    @property
    def qpre_val(self) -> QPreTerm:
        return val_qpre(self._qpre)

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        '''
        not meant for qpre
        '''
        raise Exception()
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.qpre_val)


class UnionHintTerm(ProofHintTerm):
    def __init__(self, proof_hints : Tuple[dts.Term,...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, dts.Term):
                raise ValueError()
            if item.type != type_proof_hint:
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            item_val = val_proof_hint(item)
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        # check whether the program of all proofs are the same
        example_proof_hint = val_proof_hint(proof_hints[0])
        for i in range(1, len(proof_hints)):
            item_val = val_proof_hint(proof_hints[i])
            if not example_proof_hint.prog_consistent(item_val):
                raise RuntimeErrorWithLog(
                    "The (Union) rule requires that all the proofs are about the same program, but proof '" +\
                        str(proof_hints[0]) + "' and proof '" + str(proof_hints[i]) + "' are not."
                )


        super().__init__(all_qvarls)
        self._proof_hints : Tuple[dts.Term,...] = proof_hints
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, UnionHintTerm):
            return self.get_proof_hint(0) == other.get_proof_hint(0)
        else:
            return False

    def str_content(self, prefix: str) -> str:
        r = prefix + "(\n"
        r += self.get_proof_hint(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._proof_hints)):
            r += prefix + ",\n"
            r += self.get_proof_hint(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r

class ProofSeqHintTerm(ProofHintTerm):
    def __init__(self, proof_hints : Tuple[dts.Term,...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, dts.Term):
                raise ValueError()
            if item.type != type_proof_hint:
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            # the individual subprogram can be "None" here
            item_val = val_proof_hint(item)
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        super().__init__(all_qvarls)
        # flatten the sequential composition
        flattened = ()
        for item in proof_hints:
            if isinstance(item, ProofSeqHintTerm):
                flattened = flattened + item._proof_hints
            else:
                flattened = flattened + (item,)
        self._proof_hints : Tuple[dts.Term,...] = flattened

    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, ProofSeqHintTerm):
            # get the list without qpredicate
            ls_self : List[ProofHintTerm] = []
            for i in range(len(self._proof_hints)):
                temp = self.get_proof_hint(i)
                if not isinstance(temp, QPreHintTerm):
                    ls_self.append(temp)
            ls_other : List[ProofHintTerm] = []
            for i in range(len(other._proof_hints)):
                temp = other.get_proof_hint(i)
                if not isinstance(temp, QPreHintTerm):
                    ls_other.append(temp)
            if len(ls_self) != len(ls_other):
                return False
            # begin comparing
            for i in range(len(ls_self)):
                if not ls_self[i].prog_consistent(ls_other[i]):
                    return False
            return True
        else:
            return False

    def str_content(self, prefix: str) -> str:
        if len(self._proof_hints) == 1:
            return self.get_proof_hint(0).str_content(prefix)
        elif len(self._proof_hints) > 1:
            r = ""
            for i in range(len(self._proof_hints)-1):
                r += self.get_proof_hint(i).str_content(prefix) + ";\n"
            r += self.get_proof_hint(len(self._proof_hints)-1).str_content(prefix)
            return r
        else:
            raise Exception()


