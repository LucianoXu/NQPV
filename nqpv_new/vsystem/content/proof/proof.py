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
# proof.py
#
# define the value of program proof. semantic checks are done in eval_proof.py
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from ...log_system import RuntimeErrorWithLog
from ...syntax.pos_info import PosInfo

from ..predicate.qpredicate import QPredicate

class QProofStatement:
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate):
        self.pos : PosInfo = pos
        self.post : QPredicate  = post
        self.pre : QPredicate = pre
    
        
class QPredicateProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate):
        super().__init__(pos, pre, post)


class QSkipProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate):
        super().__init__(pos, pre, post)

class QAbortProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate):
        super().__init__(pos, pre, post)

class QInitProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, qvar_ls : List[str]):
        super().__init__(pos, pre, post)
        self.qvar_ls : List[str] = qvar_ls
    
class QUnitaryProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, qvar_ls : List[str], opt : str):
        super().__init__(pos, pre, post)
        self.qvar_ls : List[str] = qvar_ls
        self.opt : str = opt

class QIfProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, opt : str, qvar_ls : List[str], P1 : QProof, P0 : QProof):
        super().__init__(pos, pre, post)
        self.opt : str = opt
        self.qvar_ls : List[str] = qvar_ls
        self.P1 : QProof = P1
        self.P0 : QProof = P0

class QWhileProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, inv : QPredicate, opt : str, qvar_ls : List[str], P_inv : QProof):
        super().__init__(pos, pre, post)
        self.inv : QPredicate = inv
        self.opt : str = opt
        self.qvar_ls : List[str] = qvar_ls
        self.P_inv : QProof = P_inv     # the proof is for the legality of the loop invariant

class QSubproof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, proof_id : str, qvar_ls : List[str]):
        super().__init__(pos, pre, post)
        self.proof_id : str = proof_id
        self.qvar_ls : List[str] = qvar_ls
        
class QProof:
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, statements : List[QProofStatement]):
        self.pos : PosInfo = pos
        self.pre : QPredicate = pre
        self.post : QPredicate = post
        self.statements : List[QProofStatement] = statements
    
    def substitute(self, pos : PosInfo, new_qvar : Tuple[str,...]) -> QProof:
        '''
        return the proof with parameter quantum variables substituted
        '''
        new_pre_pairs = [(pair[0], list(new_qvar)) for pair in self.pre.pairs]
        new_post_pairs = [(pair[0], list(new_qvar)) for pair in self.post.pairs]
        return QProof(
            pos,
            QPredicate(PosInfo(), new_pre_pairs), 
            QPredicate(PosInfo(), new_post_pairs),
            self.statements
        )


