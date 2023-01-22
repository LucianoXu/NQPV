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

from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm
from .opt_term import OperatorTerm
from .opt_pair_term import OptPairTerm, MeaPairTerm
from . import qpre_term
from .qpre_term import QPreTerm
from .prog_term import AbortTerm, IfTerm, InitTerm, NondetTerm, ProgSttSeqTerm, ProgSttTerm, SkipTerm, UnitaryTerm, WhileTerm
from ..var_scope import VVar, VarScope

from .proof_hint_term import ProofHintTerm

# proof statements

class ProofSttTerm(VVar):
    def __init__(self, pre : QPreTerm, post : QPreTerm):

        if not isinstance(pre, QPreTerm):
            raise RuntimeErrorWithLog("The term '" + str(pre) + "' is not a quantum predicate.")
        if not isinstance(post, QPreTerm):
            raise RuntimeErrorWithLog("The term '" + str(post) + "' is not a quantum predicate.")

        all_qvarls = pre.all_qvarls
        all_qvarls = all_qvarls.join(post.all_qvarls)
        self._all_qvarls : QvarlsTerm = all_qvarls
        self._pre : QPreTerm = pre
        self._post : QPreTerm = post

    @property
    def str_type(self) -> str:
        return "quantum_predicate_set"
            
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls
    
    @property
    def pre(self) -> QPreTerm:
        return self._pre
    
    @property
    def post(self) -> QPreTerm:
        return self._post

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



class SkipProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm):
        super().__init__(pre, post)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "skip"
        return r
    

class AbortProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm):
        super().__init__(pre, post)
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "abort"
        return r
    

class InitProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, qvarls : QvarlsTerm):
        if not isinstance(qvarls, QvarlsTerm):
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(qvarls)
        self._qvarls : QvarlsTerm = qvarls
    
    @property
    def qvarls(self) -> QvarlsTerm:
        return self._qvarls
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + str(self.qvarls) + " :=0"
        return r
        
class UnitaryProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, opt_pair : OptPairTerm):
        if not isinstance(opt_pair, OptPairTerm):
            raise ValueError()

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(opt_pair.qvarls)
        self._opt_pair : OptPairTerm = opt_pair
    
    @property
    def opt_pair(self) -> OptPairTerm:
        return self._opt_pair
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + str(self.opt_pair.qvarls) + " *= " + str(self.opt_pair.opt)
        return r
        
class IfProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, opt_pair : MeaPairTerm, 
                P0 : ProofSttTerm, P1 : ProofSttTerm):        
        if not isinstance(opt_pair, MeaPairTerm):
            raise ValueError()
        if not isinstance(P0, ProofSttTerm):
            raise RuntimeErrorWithLog("The term '" + str(P0) + "' is not a proof statement.")
        if not isinstance(P1, ProofSttTerm):
            raise RuntimeErrorWithLog("The term '" + str(P1) + "' is not a proof statement.")

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(opt_pair.qvarls)
        self._all_qvarls = self._all_qvarls.join(P1.all_qvarls)
        self._all_qvarls = self._all_qvarls.join(P0.all_qvarls)
        self._opt_pair = opt_pair
        self._P0 = P0
        self._P1 = P1
    
    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair
    
    @property
    def P0(self) -> ProofSttTerm:
        return self._P0

    @property
    def P1(self) -> ProofSttTerm:
        return self._P1
    
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "if " + str(self.opt_pair) + " then\n"
        r += self.P1.str_content(prefix + "\t") + "\n"
        r += prefix + "else\n"
        r += self.P0.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r
    
    
class WhileProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, inv : QPreTerm, 
                opt_pair : MeaPairTerm, P : ProofSttTerm):        
        if not isinstance(inv, QPreTerm) or not isinstance(opt_pair, MeaPairTerm):
            raise ValueError()
        if not isinstance(P, ProofSttTerm):
            raise RuntimeErrorWithLog("The term '" + str(P) + "' is not a proof statement.")

        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(inv.all_qvarls)
        self._all_qvarls = self._all_qvarls.join(opt_pair.qvarls)
        self._all_qvarls = self._all_qvarls.join(P.all_qvarls)
        self._inv = inv
        self._opt_pair = opt_pair
        self._P = P
    
    @property
    def inv(self) -> QPreTerm:
        return self._inv

    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair
    
    @property
    def P(self) -> ProofSttTerm:
        return self._P
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "{ inv: " + self.inv.str_content() + " };\n"
        r += prefix + "while " + str(self.opt_pair) + " do\n"
        r += self.P.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r
    
class NondetProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, proof_ls : Tuple[ProofSttTerm,...]):        
        if not isinstance(proof_ls, tuple):
            raise ValueError()
        
        super().__init__(pre, post)
        for item in proof_ls:
            self._all_qvarls = self._all_qvarls.join(item.all_qvarls)
        self._proof_ls : Tuple[ProofSttTerm,...] = proof_ls
    
    def get_proof(self, i : int) -> ProofSttTerm:
        return self._proof_ls[i]
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "(\n"
        r += self.get_proof(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._proof_ls)):
            r += prefix + "#\n"
            r += self.get_proof(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r

    
class QPreProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, qpre : QPreTerm):
        if not isinstance(qpre, QPreTerm):
            raise ValueError()
        
        super().__init__(pre, post)
        self._all_qvarls = self._all_qvarls.join(qpre.all_qvarls)
        self._qpre = qpre
    
    @property
    def qpre(self) -> QPreTerm:
        return self._qpre
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self.qpre)
    
class UnionProofTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, proof_ls : Tuple[ProofSttTerm,...]):
        if not isinstance(proof_ls, tuple):
            raise ValueError()

        super().__init__(pre, post)
        for item in proof_ls:
            self._all_qvarls = self._all_qvarls.join(item.all_qvarls)
        self._proof_ls : Tuple[ProofSttTerm,...] = proof_ls
    
    def get_proof(self, i : int) -> ProofSttTerm:
        return self._proof_ls[i]
    
    def str_content(self, prefix: str) -> str:
        r = prefix + str(self.pre) + ";\n"
        r += prefix + "(\n"
        r += self.get_proof(0).str_content(prefix + "\t") + ";\n"
        r += prefix + "\t" + str(self.get_proof(0).post) + "\n"
        for i in range(1, len(self._proof_ls)):
            r += prefix + ",\n"
            r += self.get_proof(i).str_content(prefix + "\t") + ";\n"
            r += prefix + "\t" + str(self.get_proof(i).post) + "\n"
        r += prefix + ")"
        return r
    

class ProofSeqTerm(ProofSttTerm):
    def __init__(self, pre : QPreTerm, post : QPreTerm, proof_ls : Tuple[ProofSttTerm,...]):        
        if not isinstance(proof_ls, tuple):
            raise ValueError()
        
        super().__init__(pre, post)
        for item in proof_ls:
            self._all_qvarls = self._all_qvarls.join(item.all_qvarls)
        self._proof_ls : Tuple[ProofSttTerm,...] = proof_ls

    def get_proof(self, i : int) -> ProofSttTerm:
        return self._proof_ls[i]

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
        

class ProofDefinedTerm(VVar):
    '''
    the completed proof
    '''
    def __init__(self, pre : QPreTerm, proof_hint : ProofHintTerm, 
                proof_stts : ProofSttTerm, post : QPreTerm, arg_ls : QvarlsTerm):
        '''
        proof_hint : proof_hint is necessary for apply_hint method
        the specified pre and post conditions are necessary, because they are not the full extension
        '''
        
        if not isinstance(pre, QPreTerm)\
             or not isinstance(proof_hint, ProofHintTerm)\
             or not isinstance(proof_stts, ProofSttTerm)\
             or not isinstance(post, QPreTerm)\
             or not isinstance(arg_ls, QvarlsTerm):
            raise ValueError()

        self._arg_ls : QvarlsTerm = arg_ls
        self._proof_hint : ProofHintTerm = proof_hint
        self._proof_stts : ProofSttTerm = proof_stts
        self._pre = pre
        self._post = post
        self._all_qvarls : QvarlsTerm = arg_ls
        self._all_qvarls = self._all_qvarls.join(self._proof_stts.all_qvarls)



    @property
    def proof_stts(self) -> ProofSttTerm:
        return self._proof_stts

    @property
    def pre(self) -> QPreTerm:
        return self._pre
    
    @property
    def post(self) -> QPreTerm:
        return self._post
        
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    @property
    def arg_ls(self) -> QvarlsTerm:
        return self._arg_ls

    def __eq__(self, other) -> bool:
        return NotImplemented

    def __str__(self) -> str:
        r = "\nproof " + str(self.arg_ls) + " : \n" 
        r += "\t" + str(self.pre) + ";\n\n"
        r += self.proof_stts.str_content("\t") + ";\n"
        r += "\n\t" + str(self.post) + "\n"
        return r
