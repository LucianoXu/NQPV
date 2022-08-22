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
# qprog_proof_outline.py
#
# Define the structure framework for a proof outline
# ------------------------------------------------------------



from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from .opt_env import Operator, OptEnv
from .qVar import QvarLs
from .opt_qvar_pair import OptQvarPair
from .qPre import QPredicate
from .qprog_std import QProg, QProgSequence

from ..syntaxes.pos_info import PosInfo
from ..logsystem import LogSystem

class QProofOutline:
    def __new__(cls, pre : QPredicate | None, progs : QProgSequence | None, post : QPredicate | None):
        if pre is None:
            LogSystem.channels["error"].append("The precondition is invalid.")
            return None
        if progs is None:
            LogSystem.channels["error"].append("The programs is invalid." + PosInfo.str(pre.pos))
            return None
        if post is None:
            LogSystem.channels["error"].append("The postcondition is invalid." + PosInfo.str(pre.pos))
            return None

        instance = super().__new__(cls)
        instance.pre = pre
        instance.progs = progs
        instance.post = post
        instance.pos = pre.pos
        return instance

    def __init__(self, pre : QPredicate | None, progs : QProgSequence | None, post : QPredicate | None):
        super().__init__()
        self.pre : QPredicate
        self.progs : QProgSequence
        self.post : QPredicate
        self.pos : PosInfo | None
    
    def __str__(self) -> str:
        r = str(self.pre) + "\n\n"
        r += str(self.progs) + "\n\n"
        r += str(self.post)
        return r

    def proof_check(self) -> bool:
        '''
        doing the check of this proof
        '''
        self.post = self.post.full_extension()
        self.progs.set_post(self.post)

        if not self.progs.proof_check():
            LogSystem.channels["info"].append("The proof does not hold." + PosInfo.str(self.pos))
            return False

        full_pre = self.pre.full_extension()
        
        if not QPredicate.sqsubseteq(full_pre, self.progs.progs[0].pres.pres[0]):
            LogSystem.channels["info"].append("The proof does not hold." + PosInfo.str(self.pos))
            return False

        LogSystem.channels["info"].append("The proof holds." + PosInfo.str(self.pos))
        return True



