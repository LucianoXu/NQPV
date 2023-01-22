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

from nqpv.vsystem.log_system import RuntimeErrorWithLog
from nqpv.vsystem.var_scope import VVar

from .qvarls_term import QvarlsTerm
from .opt_pair_term import OptPairTerm, MeaPairTerm
from .qpre_term import QPreTerm



class ProofHintTerm(VVar):
    def __init__(self, all_qvarls : QvarlsTerm, label : str):
        super().__init__()

        self._all_qvarls : QvarlsTerm = all_qvarls
        self._label : str = label

    @property
    def str_type(self) -> str:
        return "proof_hint"

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls
    
    @property
    def label(self) -> str:
        return self._label
    
    def prog_consistent(self, other : ProofHintTerm) -> bool:
        '''
        check whether the two proof hints are about the same program (syntactically)
        '''
        raise NotImplementedError()

    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"
    
class SkipHintTerm(ProofHintTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()), "skip hint")

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        return isinstance(other, SkipHintTerm)

    def str_content(self, prefix: str) -> str:
        return prefix + "skip"

class AbortHintTerm(ProofHintTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()), "abort hint")

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        return isinstance(other, AbortHintTerm)

    def str_content(self, prefix: str) -> str:
        return prefix + "abort"

class InitHintTerm(ProofHintTerm):
    def __init__(self, qvarls : QvarlsTerm):
        if not isinstance(qvarls, QvarlsTerm):
            raise RuntimeErrorWithLog("The term '" + str(qvarls) + "' is not a quantum variable list.")


        super().__init__(qvarls, "initialization hint")
        self._qvarls : QvarlsTerm = qvarls

    @property
    def qvarls(self) -> QvarlsTerm:
        return self._qvarls

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, InitHintTerm):
            return self._qvarls == other._qvarls
        else:
            return False

    def str_content(self, prefix: str) -> str:
        return prefix + str(self._qvarls) + " :=0"

class UnitaryHintTerm(ProofHintTerm):
    def __init__(self, opt_pair : OptPairTerm):
        if not isinstance(opt_pair, OptPairTerm):
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a operator variable pair.")

        if not opt_pair.unitary_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not an unitary pair.")
        
        all_qvarls = opt_pair.qvarls
        super().__init__(all_qvarls, "unitary hint")
        self._opt_pair : OptPairTerm = opt_pair

    @property
    def opt_pair(self) -> OptPairTerm:
        return self._opt_pair

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, UnitaryHintTerm):
            return self._opt_pair == other._opt_pair
        else:
            return False

    def str_content(self, prefix: str) -> str:
        return prefix + str(self.opt_pair._qvarls) + " *= " + self.opt_pair.opt.name

class IfHintTerm(ProofHintTerm):
    def __init__(self, opt_pair : MeaPairTerm, P0 : ProofHintTerm, P1 : ProofHintTerm):
        if not isinstance(opt_pair, MeaPairTerm):
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a measurement.")
        
        if not isinstance(P0, ProofHintTerm):
            raise RuntimeErrorWithLog("The term '" + str(P0) + "' is not a proof hint.")
        if not isinstance(P1, ProofHintTerm):
            raise RuntimeErrorWithLog("The term '" + str(P1) + "' is not a proof hint.")
            
        
        all_qvarls = opt_pair.qvarls
        all_qvarls = all_qvarls.join(P0.all_qvarls)
        all_qvarls = all_qvarls.join(P1.all_qvarls)
        super().__init__(all_qvarls, "if hint")
        self._opt_pair : MeaPairTerm = opt_pair
        self._P0 : ProofHintTerm = P0
        self._P1 : ProofHintTerm = P1

    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair
    
    @property
    def P0_val(self) -> ProofHintTerm:
        return self._P0
    
    @property
    def P1_val(self) -> ProofHintTerm:
        return self._P1

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
    def __init__(self, inv : QPreTerm, opt_pair : MeaPairTerm, P : ProofHintTerm):
        if not isinstance(opt_pair, MeaPairTerm):
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a measurement.")
      
        # check loop invariant
        if not isinstance(inv, QPreTerm):
            raise RuntimeErrorWithLog("The term '" + str(opt_pair) + "' is not a predicate, while a loop invariant is needed.")

        if not isinstance(P, ProofHintTerm):
            raise RuntimeErrorWithLog("The term '" + str(P) + "' is not a proof hint.")
        
        all_qvarls = opt_pair.qvarls
        all_qvarls = all_qvarls.join(P.all_qvarls)
        super().__init__(all_qvarls, "while hint")
        self._inv : QPreTerm = inv
        self._opt_pair : MeaPairTerm = opt_pair
        self._P : ProofHintTerm = P

    @property
    def inv(self) -> QPreTerm:
        return self._inv

    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair
    
    @property
    def P(self) -> ProofHintTerm:
        return self._P

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        if isinstance(other, WhileHintTerm):
            return self._opt_pair == other._opt_pair\
                and self.P.prog_consistent(other.P)
        else:
            return False
    
    def str_content(self, prefix: str) -> str:
        r = prefix + "{ inv: " + self.inv.str_content() + "};\n"
        r += prefix + "while " + str(self._opt_pair) + " do\n"
        r += self.P.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class NondetHintTerm(ProofHintTerm):
    def __init__(self, proof_hints : Tuple[ProofHintTerm, ...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, ProofHintTerm):
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            all_qvarls = all_qvarls.join(item.all_qvarls)
        
        super().__init__(all_qvarls, "nondeterministic hint")
        self._proof_hints : Tuple[ProofHintTerm,...] = proof_hints
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return self._proof_hints[i]

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

class QPreHintTerm(ProofHintTerm):
    def __init__(self, qpre : QPreTerm):
        if not isinstance(qpre, QPreTerm):
            raise ValueError()

        super().__init__(qpre.all_qvarls,"predicate hint")
        self._qpre : QPreTerm = qpre

    @property
    def qpre(self) -> QPreTerm:
        return self._qpre

    def prog_consistent(self, other: ProofHintTerm) -> bool:
        '''
        not meant for qpre
        '''
        raise Exception()
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.qpre)


class UnionHintTerm(ProofHintTerm):
    def __init__(self, proof_hints : Tuple[ProofHintTerm,...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, ProofHintTerm):
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            all_qvarls = all_qvarls.join(item.all_qvarls)
        
        # check whether the program of all proofs are the same
        example_proof_hint = proof_hints[0]
        for i in range(1, len(proof_hints)):
            item = proof_hints[i]
            if not example_proof_hint.prog_consistent(item):
                raise RuntimeErrorWithLog(
                    "The (Union) rule requires that all the proofs are about the same program, but proof '" +\
                        str(proof_hints[0]) + "' and proof '" + str(proof_hints[i]) + "' are not."
                )


        super().__init__(all_qvarls, "union hint")
        self._proof_hints : Tuple[ProofHintTerm,...] = proof_hints
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return self._proof_hints[i]

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
    def __init__(self, proof_hints : Tuple[ProofHintTerm,...]):
        if not isinstance(proof_hints, tuple):
            raise ValueError()
        
        all_qvarls = QvarlsTerm(())
        for item in proof_hints:
            if not isinstance(item, ProofHintTerm):
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a proof hint.")
            # the individual subprogram can be "None" here
            all_qvarls = all_qvarls.join(item.all_qvarls)
        
        super().__init__(all_qvarls, "sequential hint")
        # flatten the sequential composition
        flattened = ()
        for item in proof_hints:
            if isinstance(item, ProofSeqHintTerm):
                flattened = flattened + item._proof_hints
            else:
                flattened = flattened + (item,)
        self._proof_hints : Tuple[ProofHintTerm,...] = flattened

    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return self._proof_hints[i]

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


