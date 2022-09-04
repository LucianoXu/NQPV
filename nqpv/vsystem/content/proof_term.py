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
# proof_term.py
#
# define the proof terms
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm, type_qvarls, val_qvarls
from .opt_term import OperatorTerm
from .opt_pair_term import OptPairTerm, type_opt_pair, val_opt_pair
from . import qpre_term
from .qpre_term import QPreTerm, type_qpre, val_qpre
from .prog_term import AbortTerm, IfTerm, InitTerm, NondetTerm, ProgSttSeqTerm, ProgSttTerm, SkipTerm, UnitaryTerm, WhileTerm
from .scope_term import ScopeTerm

fac = dts.TermFact()
type_proof_hint = fac.axiom("proof_hint", fac.sort_term(0))
type_proof_stt = fac.axiom("proof_statement", fac.sort_term(0))
type_proof = fac.axiom("proof", fac.sort_term(0))


class ProofHintTerm(dts.Term):
    def __init__(self, all_qvarls : QvarlsTerm):
        val_qvarls(all_qvarls)

        super().__init__(type_proof_hint, None)
        self._all_qvarls : QvarlsTerm = all_qvarls
        # this item should be set by its concrete class objects
        self._prog : ProgSttTerm | None = None

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls
    
    @property
    def prog(self) -> ProgSttTerm:
        if self._prog is None:
            raise RuntimeErrorWithLog("The proof '" + str(self) + "' is not about any program.")
        else:
            return self._prog
    
    def _get_prog(self) -> ProgSttTerm | None:
        '''
        return the program that this proof is about
        (return None if this proof is not about a program)
        '''
        raise NotImplementedError()

    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        raise NotImplementedError()

    def wp_statement(self, post : dts.Term, scope : ScopeTerm) -> ProofSttTerm:
        '''
        form a proof statement, with the specific postcondition
        '''
        raise NotImplementedError()

    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"
    
    def construct_proof(self, pre : dts.Term, post : dts.Term, arg_ls : dts.Term, scope : ScopeTerm) -> ProofTerm:
        '''
        construct a proof term from this hint
        '''
        if not isinstance(pre, dts.Term) or not isinstance(post, dts.Term)\
             or not isinstance(arg_ls, dts.Term) or not isinstance(scope, ScopeTerm):
            raise ValueError()
        pre_val = val_qpre(pre)
        post_val = val_qpre(post)

        # need to check whether arg_ls covers the pre and the post
        arg_ls_val = val_qvarls(arg_ls)
        if not arg_ls_val.cover(pre_val.all_qvarls) or \
                not arg_ls_val.cover(post_val.all_qvarls):
            raise RuntimeErrorWithLog("The argument list '" + str(arg_ls) + "' must cover that of the precondition and the postcondition.")

        # calculate the proof statements
        proof_stts = self.wp_statement(post, scope)

        try:
            QPreTerm.sqsubseteq(pre_val, proof_stts.pre_val, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The precondition of this proof does not hold.")

        return ProofDefinedTerm(pre, self, proof_stts, post, arg_ls)

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
        self._prog : ProgSttTerm | None = self._get_prog()
    def _get_prog(self) -> ProgSttTerm | None:
        return SkipTerm()
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return SkipHintTerm()
    def wp_statement(self, post: dts.Term, scope : ScopeTerm) -> ProofSttTerm:
        return SkipProofTerm(post, post)
    def str_content(self, prefix: str) -> str:
        return prefix + "skip"

class AbortHintTerm(ProofHintTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))
        self._prog : ProgSttTerm | None = self._get_prog()
    def _get_prog(self) -> ProgSttTerm | None:
        return AbortTerm()
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return AbortHintTerm()
    def wp_statement(self, post: dts.Term, scope : ScopeTerm) -> ProofSttTerm:
        post_val = val_qpre(post)
        pre = qpre_term.qpre_I(post_val.all_qvarls, scope)
        return AbortProofTerm(pre, post)
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
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def qvarls_val(self) -> QvarlsTerm:
        return val_qvarls(self._qvarls)

    def _get_prog(self) -> ProgSttTerm | None:
        return InitTerm(self._qvarls)
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return InitHintTerm(self.qvarls_val.qvar_substitute(correspondence))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        post_val = val_qpre(post)
        pre = qpre_term.qpre_init(post_val, self.qvarls_val, scope)
        return InitProofTerm(pre, post, self._qvarls)
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.qvarls_val) + " :=0"

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
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)

    def _get_prog(self) -> ProgSttTerm | None:
        return UnitaryTerm(self._opt_pair)
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return UnitaryHintTerm(self.opt_pair_val.qvar_substitute(correspondence))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        post_val = val_qpre(post)        
        pre = qpre_term.qpre_contract(post_val, self.opt_pair_val.dagger(), scope)
        return UnitaryProofTerm(pre, post, self._opt_pair)
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.opt_pair_val.qvarls_val) + " *= " + str(self.opt_pair_val.opt_val)

class IfHintTerm(ProofHintTerm):
    def __init__(self, opt_pair : dts.Term, P0 : dts.Term, P1 : dts.Term):
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
        
        # check the subprograms

        P0_val = val_proof_hint(P0)
        P1_val = val_proof_hint(P1)
        check = P0_val.prog
        check = P1_val.prog
        
        all_qvarls = opt_pair_val.qvarls_val
        all_qvarls = all_qvarls.join(P0_val.all_qvarls)
        all_qvarls = all_qvarls.join(P1_val.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : dts.Term = opt_pair
        self._P0 : dts.Term = P0
        self._P1 : dts.Term = P1
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P0_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P0)
    
    @property
    def P1_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P1)

    def _get_prog(self) -> ProgSttTerm | None:
        return IfTerm(self._opt_pair, self.P1_val.prog, self.P0_val.prog)
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return IfHintTerm(
            self.opt_pair_val.qvar_substitute(correspondence),
            self.P0_val.arg_apply(correspondence),
            self.P1_val.arg_apply(correspondence)
        )
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        P1 = self.P1_val.wp_statement(post, scope)
        P0 = self.P0_val.wp_statement(post, scope)

        pre = qpre_term.qpre_mea_proj_sum(P0.pre_val, P1.pre_val, self.opt_pair_val, scope)
        return IfProofTerm(pre, post, self._opt_pair, P1, P0)
    def str_content(self, prefix: str) -> str:
        r = prefix + "if " + str(self.opt_pair_val) + " then\n"
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

        # check the subprogram
        P_val = val_proof_hint(P)
        check = P_val.prog
        
        all_qvarls = opt_pair_val.qvarls_val
        all_qvarls = all_qvarls.join(P_val.all_qvarls)
        super().__init__(all_qvarls)
        self._inv : dts.Term = inv
        self._opt_pair : dts.Term = opt_pair
        self._P : dts.Term = P
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def inv_val(self) -> QPreTerm:
        return val_qpre(self._inv)

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P_val(self) -> ProofHintTerm:
        return val_proof_hint(self._P)

    def _get_prog(self) -> ProgSttTerm | None:
        return WhileTerm(self._opt_pair, self.P_val.prog)
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return WhileHintTerm(
            self.inv_val.qvar_subsitute(correspondence),
            self.opt_pair_val.qvar_substitute(correspondence),
            self.P_val.arg_apply(correspondence)
        )
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        post_val = val_qpre(post)
        proposed_pre = qpre_term.qpre_mea_proj_sum(post_val, self.inv_val, self.opt_pair_val, scope)
        P = self.P_val.wp_statement(proposed_pre, scope)
        try:
            QPreTerm.sqsubseteq(self.inv_val, P.pre_val, scope)
        except:
            raise RuntimeErrorWithLog("The predicate '" + str(self._inv) + "' is not a valid loop invariant.")  

        return WhileProofTerm(proposed_pre, post, self._inv, self._opt_pair, P)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + "{ inv: " + self.inv_val.str_content() + "};\n"
        r += prefix + "while " + str(self.opt_pair_val) + " do\n"
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
            # check the program
            item_val = val_proof_hint(item)
            check = item_val.prog
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        super().__init__(all_qvarls)
        self._proof_hints : Tuple[dts.Term,...] = proof_hints
        self._prog : ProgSttTerm | None = self._get_prog()
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def _get_prog(self) -> ProgSttTerm | None:
        prog_ls = []
        for item in self._proof_hints:
            item_val = val_proof_hint(item)
            prog_ls.append(item_val.prog)
        return NondetTerm(tuple(prog_ls))
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        new_hints = []
        for item in self._proof_hints:
            item_val = val_proof_hint(item)
            new_hints.append(item_val.arg_apply(correspondence))
        return NondetHintTerm(tuple(new_hints))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        proof_stts = []
        pre = QPreTerm(())
        for item in self._proof_hints:
            item_val = val_proof_hint(item)
            new_proof_stt = item_val.wp_statement(post, scope)
            proof_stts.append(new_proof_stt)
            pre = pre.union(new_proof_stt.pre_val)
        
        return NondetProofTerm(pre, post, tuple(proof_stts))
    
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
        self._subproof : dts.Term = subproof
        self._arg_ls : dts.Term = arg_ls
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def subproof_val(self) -> ProofDefinedTerm:
        return val_proof(self._subproof)
    
    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)
    
    def _get_prog(self) -> ProgSttTerm | None:
        '''
        this method will expand the subproof
        '''
        return self.subproof_val.apply_hint(self.arg_ls_val).prog
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return SubproofHintTerm(self._subproof, self.arg_ls_val.qvar_substitute(correspondence))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        cor = self.subproof_val.arg_ls_val.get_sub_correspond(self.arg_ls_val)
        pre_sub = self.subproof_val.pre_val.qvar_subsitute(cor)
        post_sub = self.subproof_val.post_val.qvar_subsitute(cor)

        try:
            QPreTerm.sqsubseteq(post_sub, post, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The subproof statement '" + str(self._subproof) + "' cannot be put here.")
        
        return SubproofTerm(pre_sub, post, self._subproof, self._arg_ls)
    
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
        self._prog : ProgSttTerm | None = self._get_prog()

    @property
    def qpre_val(self) -> QPreTerm:
        return val_qpre(self._qpre)
    def _get_prog(self) -> ProgSttTerm | None:
        return None
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return QPreHintTerm(self.qpre_val.qvar_subsitute(correspondence))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        try:
            QPreTerm.sqsubseteq(self._qpre, post, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The condition hint '" + str(post) + "' does not hold.")
        
        return QPreProofTerm(self._qpre, post, self._qpre)
    
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
            # check the programas
            item_val = val_proof_hint(item)
            check = item_val.prog
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        # check whether the program of all proofs are the same
        example_prog = val_proof_hint(proof_hints[0]).prog
        for i in range(1, len(proof_hints)):
            item_val = val_proof_hint(proof_hints[i])
            if example_prog != item_val.prog:
                raise RuntimeErrorWithLog(
                    "The (Union) rule requires that all the proofs are about the same program, but proof '" +\
                        str(proof_hints[0]) + "' and proof '" + str(proof_hints[i]) + "' are not."
                )


        super().__init__(all_qvarls)
        self._proof_hints : Tuple[dts.Term,...] = proof_hints
        self._prog : ProgSttTerm | None = self._get_prog()
    
    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def _get_prog(self) -> ProgSttTerm | None:
        return self.get_proof_hint(0)._get_prog()
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        return self.get_proof_hint(0).arg_apply(correspondence)
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
            proof_stts = []
            pre = QPreTerm(())
            for item in self._proof_hints:
                try:
                    item_val = val_proof_hint(item)
                    new_proof_stt = item_val.wp_statement(post, scope)
                    proof_stts.append(new_proof_stt)
                    pre = pre.union(new_proof_stt.pre_val)
                except RuntimeErrorWithLog:
                    raise RuntimeErrorWithLog("The proof '" + str(item) + "' in the union proof does not hold.")
            return UnionProofTerm(pre, post, tuple(proof_stts))
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
        self._prog : ProgSttTerm | None = self._get_prog()

    def get_proof_hint(self, i : int) -> ProofHintTerm:
        return val_proof_hint(self._proof_hints[i])

    def _get_prog(self) -> ProgSttTerm | None:
        prog_ls = []
        for item in self._proof_hints:
            item_val = val_proof_hint(item)
            # filter out the predicate proofs
            if not isinstance(item_val, QPreHintTerm):
                prog_ls.append(item_val.prog)
        if len(prog_ls) == 0:
            return None
        else:
            return ProgSttSeqTerm(tuple(prog_ls))
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofHintTerm:
        new_hints = []
        for item in self._proof_hints:
            item_val = val_proof_hint(item)
            new_hints.append(item_val.arg_apply(correspondence))
        return ProofSeqHintTerm(tuple(new_hints))
    def wp_statement(self, post: dts.Term, scope: ScopeTerm) -> ProofSttTerm:
        # backward transformation
        proof_stts : List[ProofSttTerm] = []
        cur_post = post
        for i in range(len(self._proof_hints)-1, -1, -1):
            item_val = val_proof_hint(self._proof_hints[i])
            proof_stts.insert(0, item_val.wp_statement(cur_post, scope))
            cur_post = proof_stts[0].pre_val
        
        return ProofSeqTerm(cur_post, post, tuple(proof_stts))
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



# proof statements

class ProofSttTerm(dts.Term):
    def __init__(self, pre : dts.Term, post : dts.Term):

        if not isinstance(pre, dts.Term) or not isinstance(post, dts.Term):
            raise ValueError()
        if pre.type != type_qpre:
            raise RuntimeErrorWithLog("The term '" + str(pre) + "' is not a quantum predicate.")
        if post.type != type_qpre:
            raise RuntimeErrorWithLog("The term '" + str(post) + "' is not a quantum predicate.")

        pre_val = val_qpre(pre)
        post_val = val_qpre(post)

        all_qvarls = pre_val.all_qvarls
        all_qvarls = all_qvarls.join(post_val.all_qvarls)
        super().__init__(type_proof_stt, None)
        self._all_qvarls : QvarlsTerm = all_qvarls
        self._pre : dts.Term = pre
        self._post : dts.Term = post
            
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls
    
    @property
    def pre_val(self) -> QPreTerm:
        return val_qpre(self._pre)
    
    @property
    def post_val(self) -> QPreTerm:
        return val_qpre(self._post)

    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        raise NotImplementedError()

    def get_prog(self) -> ProgSttTerm:
        raise NotImplementedError()
    
    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"

    def expand(self) -> ProofSttTerm:
        '''
        get the proof statement with all subproofs substituted
        '''
        raise NotImplementedError()
    
def val_proof_stt(term : dts.Term) -> ProofSttTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_proof_stt:
        raise ValueError()
        
    if isinstance(term, ProofSttTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProofSttTerm):
            raise Exception()
        return val
    else:
        raise Exception()


# implement the weakest precondition calculus

class SkipProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term):
        super().__init__(pre, post)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "skip"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return SkipProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence)
        )
    
    def expand(self) -> ProofSttTerm:
        return SkipProofTerm(self._pre, self._post)
        

class AbortProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term):
        super().__init__(pre, post)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "abort"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return AbortProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence)
        )

    def expand(self) -> ProofSttTerm:
        return AbortProofTerm(self._pre, self._post)

class InitProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, qvarls : dts.Term):
        if not isinstance(qvarls, dts.Term):
            raise ValueError()
        if qvarls.type != type_qvarls:
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_qvarls(qvarls))
        self._qvarls : dts.Term = qvarls
    
    @property
    def qvarls_val(self) -> QvarlsTerm:
        return val_qvarls(self._qvarls)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + str(self.qvarls_val) + " :=0"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return InitProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self.qvarls_val.qvar_substitute(correspondence)
        )
    
    def expand(self) -> ProofSttTerm:
        return InitProofTerm(self._pre, self._post, self._qvarls)
    
class UnitaryProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, opt_pair : dts.Term):
        if not isinstance(opt_pair, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_opt_pair(opt_pair).qvarls_val)
        self._opt_pair : dts.Term = opt_pair
    
    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + str(self.opt_pair_val.qvarls_val) + " *= " + str(self.opt_pair_val.opt)
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return UnitaryProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self.opt_pair_val.qvar_substitute(correspondence)

        )

    def expand(self) -> ProofSttTerm:
        return UnitaryProofTerm(self._pre, self._post, self._opt_pair)
    
class IfProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, opt_pair : dts.Term, P1 : dts.Term, P0 : dts.Term):        
        if not isinstance(opt_pair, dts.Term) or not isinstance(P1, dts.Term) or not isinstance(P0, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise ValueError()
        if P1.type != type_proof_stt:
            raise RuntimeErrorWithLog("The term '" + str(P1) + "' is not a proof statement.")
        if P0.type != type_proof_stt:
            raise RuntimeErrorWithLog("The term '" + str(P0) + "' is not a proof statement.")

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_opt_pair(opt_pair).qvarls_val)
        self._all_qvarls = self._all_qvarls.join(val_proof_stt(P1).all_qvarls)
        self._all_qvarls = self._all_qvarls.join(val_proof_stt(P0).all_qvarls)
        self._opt_pair = opt_pair
        self._P0 = P0
        self._P1 = P1
    
    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P1_val(self) -> ProofSttTerm:
        return val_proof_stt(self._P1)
    
    @property
    def P0_val(self) -> ProofSttTerm:
        return val_proof_stt(self._P0)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "if " + str(self.opt_pair_val) + " then\n"
        r += self.P1_val.str_content(prefix + "\t") + "\n"
        r += prefix + "else\n"
        r += self.P0_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return IfProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self.opt_pair_val.qvar_substitute(correspondence),
            self.P1_val.arg_apply(correspondence),
            self.P0_val.arg_apply(correspondence)
        )
    
    def expand(self) -> ProofSttTerm:
        return IfProofTerm(
            self._pre, self._post, self._opt_pair, 
            self.P1_val.expand(), self.P0_val.expand()
        )

    
class WhileProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, inv : dts.Term, opt_pair : dts.Term, P : dts.Term):        
        if not isinstance(inv, dts.Term) or not isinstance(opt_pair, dts.Term) or not isinstance(P, dts.Term):
            raise ValueError()
        if inv.type != type_qpre or opt_pair.type != type_opt_pair:
            raise ValueError()
        if P.type != type_proof_stt:
            raise RuntimeErrorWithLog("The term '" + str(P) + "' is not a proof statement.")

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_qpre(inv).all_qvarls)
        self._all_qvarls = self._all_qvarls.join(val_opt_pair(opt_pair).qvarls_val)
        self._all_qvarls = self._all_qvarls.join(val_proof_stt(P).all_qvarls)
        self._inv = inv
        self._opt_pair = opt_pair
        self._P = P
    
    @property
    def inv_val(self) -> QPreTerm:
        return val_qpre(self._inv)

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)
    
    @property
    def P_val(self) -> ProofSttTerm:
        return val_proof_stt(self._P)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "{ inv: " + str(self.inv_val) + " };\n"
        r += prefix + "while " + str(self.opt_pair_val) + " do\n"
        r += self.P_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return WhileProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self.inv_val.qvar_subsitute(correspondence),
            self.opt_pair_val.qvar_substitute(correspondence),
            self.P_val.arg_apply(correspondence)
        )

    def expand(self) -> ProofSttTerm:
        return WhileProofTerm(
            self._pre, self._post, self._inv, self._opt_pair, 
            self.P_val.expand()
        )

class NondetProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, proof_ls : Tuple[dts.Term,...]):        
        if not isinstance(proof_ls, tuple):
            raise ValueError()
        for item in proof_ls:
            item_val = val_proof_stt(item)
        
        super().__init__(pre, post)
        for item in proof_ls:
            item_val = val_proof_stt(item)
            self._all_qvarls = self._all_qvarls.join(item_val.all_qvarls)
        self._proof_ls : Tuple[dts.Term,...] = proof_ls
    
    def get_proof(self, i : int) -> ProofSttTerm:
        return val_proof_stt(self._proof_ls[i])
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "(\n"
        r += self.get_proof(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._proof_ls)):
            r += prefix + "#\n"
            r += self.get_proof(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        new_stts = []
        for i in range(len(self._proof_ls)):
            new_stts.append(self.get_proof(i).arg_apply(correspondence))
        return NondetProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            tuple(new_stts)
        )

    def expand(self) -> ProofSttTerm:
        new_ls = []
        for item in self._proof_ls:
            new_ls.append(val_proof_stt(item).expand())
        return NondetProofTerm(self._pre, self._post, tuple(new_ls))

class SubproofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, subproof : dts.Term, arg_ls : dts.Term):
        if not isinstance(subproof, dts.Term) or not isinstance(arg_ls, dts.Term):
            raise ValueError()
        if subproof.type != type_proof or arg_ls.type != type_qvarls:
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_qvarls(arg_ls))
        self._subproof = subproof
        self._arg_ls = arg_ls
    
    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self._pre) + ";\n"
        r += prefix + str(self._subproof) + " " + str(self.arg_ls_val)
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return SubproofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self._subproof,
            self.arg_ls_val.qvar_substitute(correspondence)
        )
    
    def expand(self) -> ProofSttTerm:
        return val_proof(self._subproof).apply(self.arg_ls_val)

class QPreProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, qpre : dts.Term):
        if not isinstance(qpre, dts.Term):
            raise ValueError()
        if qpre.type != type_qpre:
            raise ValueError()
        
        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(val_qpre(qpre).all_qvarls)
        self._qpre = qpre
    
    @property
    def qpre_val(self) -> QPreTerm:
        return val_qpre(self._qpre)
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.qpre_val)
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        return QPreProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            self.qpre_val.qvar_subsitute(correspondence)
        )

    def expand(self) -> ProofSttTerm:
        return QPreProofTerm(self._pre, self._post, self._qpre)

class UnionProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, proof_ls : Tuple[dts.Term,...]):
        if not isinstance(proof_ls, tuple):
            raise ValueError()
        for item in proof_ls:
            item_val = val_proof_stt(item)

        super().__init__(pre, post)
        for item in proof_ls:
            item_val = val_proof_stt(item)
            self._all_qvarls = self._all_qvarls.join(item_val.all_qvarls)
        self._proof_ls : Tuple[dts.Term,...] = proof_ls
    
    def get_proof(self, i : int) -> ProofSttTerm:
        return val_proof_stt(self._proof_ls[i])
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "(\n"
        r += self.get_proof(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._proof_ls)):
            r += prefix + ",\n"
            r += self.get_proof(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r
    
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        new_stts = []
        for i in range(len(self._proof_ls)):
            new_stts.append(self.get_proof(i).arg_apply(correspondence))
        return UnionProofTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            tuple(new_stts)
        )

    def expand(self) -> ProofSttTerm:
        new_ls = []
        for item in self._proof_ls:
            new_ls.append(val_proof_stt(item).expand())
        return UnionProofTerm(self._pre, self._post, tuple(new_ls))


class ProofSeqTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, proof_ls : Tuple[dts.Term,...]):        
        if not isinstance(proof_ls, tuple):
            raise ValueError()
        for item in proof_ls:
            item_val = val_proof_stt(item)
        
        super().__init__(pre, post)
        for item in proof_ls:
            item_val = val_proof_stt(item)
            self._all_qvarls = self._all_qvarls.join(item_val.all_qvarls)
        self._proof_ls : Tuple[dts.Term,...] = proof_ls

    def get_proof(self, i : int) -> ProofSttTerm:
        return val_proof_stt(self._proof_ls[i])

    def str_content(self, prefix: str) -> str:
        if len(self._proof_ls) == 1:
            return self.get_proof(0).str_content(prefix)
        elif len(self._proof_ls) > 1:
            r = ""
            for i in range(len(self._proof_ls)-1):
                r += self.get_proof(i).str_content(prefix) + ";\n"
            r += self.get_proof(len(self._proof_ls)-1).str_content(prefix)
            return r
        else:
            raise Exception()
        
    def arg_apply(self, correspondence: Dict[str, str]) -> ProofSttTerm:
        new_stts = []
        for i in range(len(self._proof_ls)):
            new_stts.append(self.get_proof(i).arg_apply(correspondence))
        return ProofSeqTerm(
            self.pre_val.qvar_subsitute(correspondence),
            self.post_val.qvar_subsitute(correspondence),
            tuple(new_stts)
        )


    def expand(self) -> ProofSttTerm:
        new_ls = []
        for item in self._proof_ls:
            new_ls.append(val_proof_stt(item).expand())
        return ProofSeqTerm(self._pre, self._post, tuple(new_ls))


class ProofTerm(dts.Term):
    def __init__(self, arg_ls : dts.Term):
        if arg_ls.type != type_qvarls:
            raise RuntimeErrorWithLog("The term '" + str(arg_ls) + "' is not a quantum variable list.")
        arg_ls_val = val_qvarls(arg_ls)

        super().__init__(type_proof, None)
        self._arg_ls : dts.Term = arg_ls
        self._all_qvarls : QvarlsTerm = arg_ls_val

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)

    def __str__(self) -> str:
        raise NotImplementedError()

class ProofDefiningTerm(ProofTerm):
    '''
    The proof being defined.
    '''
    def __str__(self) -> str:
        return "\n(Proof Being Defined) " + str(self.arg_ls_val) + "\n"

class ProofDefinedTerm(ProofTerm):
    '''
    the completed proof
    '''
    def __init__(self, pre : dts.Term, proof_hint : dts.Term, proof_stts : dts.Term, post : dts.Term, arg_ls : dts.Term):
        '''
        proof_hint : proof_hint is necessary for apply_hint method
        the specified pre and post conditions are necessary, because they are not the full extension
        '''
        
        if not isinstance(pre, dts.Term)\
             or not isinstance(proof_hint, dts.Term)\
             or not isinstance(proof_stts, dts.Term)\
             or not isinstance(post, dts.Term)\
             or not isinstance(arg_ls, dts.Term):
            raise ValueError()

        super().__init__(arg_ls)
        self._arg_ls : dts.Term = arg_ls
        self._proof_hint : dts.Term = proof_hint
        self._proof_stts : dts.Term = proof_stts
        self._pre = pre
        self._post = post

    
    @property
    def proof_hint_val(self) -> ProofHintTerm:
        return val_proof_hint(self._proof_hint)

    @property
    def proof_stts_val(self) -> ProofSttTerm:
        return val_proof_stt(self._proof_stts)

    @property
    def pre_val(self) -> QPreTerm:
        return val_qpre(self._pre)
    
    @property
    def post_val(self) -> QPreTerm:
        return val_qpre(self._post)
        
    def apply_hint(self, arg_ls : QvarlsTerm) -> ProofHintTerm:
        cor = self.arg_ls_val.get_sub_correspond(arg_ls)
        return self.proof_hint_val.arg_apply(cor)

    def expand(self) -> ProofDefinedTerm:
        return ProofDefinedTerm(self._pre, self._proof_hint, self.proof_stts_val.expand(), self._post, self._arg_ls)

    def apply(self, arg_ls : QvarlsTerm) -> ProofSttTerm:
        '''
        apply the argument list to get the expaneded proof
        '''
        cor = self.arg_ls_val.get_sub_correspond(arg_ls)
        return self.proof_stts_val.arg_apply(cor)

    def __str__(self) -> str:
        r = "\nproof " + str(self.arg_ls_val) + " : \n" 
        r += "\t" + str(self.pre_val) + ";\n\n"
        r += self.proof_stts_val.str_content("\t") + ";\n"
        r += "\n\t" + str(self.post_val) + "\n"
        return r

def val_proof(term : dts.Term) -> ProofDefinedTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_proof:
        raise ValueError()
        
    if isinstance(term, ProofDefinedTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProofDefinedTerm):
            raise Exception()
        return val
    else:
        raise Exception()
