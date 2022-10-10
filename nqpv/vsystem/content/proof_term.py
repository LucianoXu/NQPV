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
type_proof_stt = fac.axiom("proof_statement", fac.sort_term(0))
type_proof = fac.axiom("proof", fac.sort_term(0))



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

    def get_prog(self) -> ProgSttTerm:
        raise NotImplementedError()
    
    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"

    def expand(self, global_qvarls : set[str]) -> ProofSttTerm:
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
    

class AbortProofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term):
        super().__init__(pre, post)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre_val) + ";\n"
        r += prefix + "abort"
        return r
    

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
        r += prefix + "{ inv: " + self.inv_val.str_content() + " };\n"
        r += prefix + "while " + str(self.opt_pair_val) + " do\n"
        r += self.P_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r
    
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
    
class SubproofTerm(ProofSttTerm):
    def __init__(self, pre : dts.Term, post : dts.Term, subproof : dts.Term, arg_ls : dts.Term):
        if not isinstance(subproof, dts.Term) or not isinstance(arg_ls, dts.Term):
            raise ValueError()
        if subproof.type != type_proof or arg_ls.type != type_qvarls:
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = val_qvarls(arg_ls)
        self._subproof = subproof
        self._arg_ls = arg_ls
    
    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self._pre) + ";\n"
        r += prefix + str(self._subproof) + " " + str(self.arg_ls_val)
        return r
    
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
        r += self.get_proof(0).str_content(prefix + "\t") + ";\n"
        r += prefix + "\t" + str(self.get_proof(0).post_val) + "\n"
        for i in range(1, len(self._proof_ls)):
            r += prefix + ",\n"
            r += self.get_proof(i).str_content(prefix + "\t") + ";\n"
            r += prefix + "\t" + str(self.get_proof(i).post_val) + "\n"
        r += prefix + ")"
        return r
    

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
                r += self.get_proof(i).str_content(prefix) + ";\n\n"
            r += self.get_proof(len(self._proof_ls)-1).str_content(prefix)
            return r
        else:
            raise Exception()
        

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

    def __eq__(self, other) -> bool:
        return NotImplemented

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
        self._all_qvarls = self._all_qvarls.join(val_proof_stt(self._proof_stts).all_qvarls)

    
    @property
    def proof_stts_val(self) -> ProofSttTerm:
        return val_proof_stt(self._proof_stts)

    @property
    def pre_val(self) -> QPreTerm:
        return val_qpre(self._pre)
    
    @property
    def post_val(self) -> QPreTerm:
        return val_qpre(self._post)
        

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
