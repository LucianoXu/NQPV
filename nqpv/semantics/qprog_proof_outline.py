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

from ..logsystem import LogSystem

# channel
channel = "semantics"

class QProofOutline:
    def __new__(cls, pre : QPredicate | None, progs : QProgSequence | None, post : QPredicate | None):
        instance = super().__new__(cls)
        if pre is None or progs is None or post is None:
            LogSystem.channels[channel].append("Error : Components provided invalid")
            return None
        
        instance.pre = pre
        instance.progs = progs
        instance.post = post
        return instance

    def __init__(self, pre : QPredicate | None, progs : QProgSequence | None, post : QPredicate | None):
        super().__init__()
        self.pre : QPredicate
        self.progs : QProgSequence
        self.post : QPredicate
    
    def __str__(self) -> str:
        r = str(self.pre) + "\n\n"
        r += str(self.progs) + "\n\n"
        r += str(self.post)
        return r

    def proof_check(self) -> bool:
        '''
        doing the check of this proof
        '''
        self.progs.set_post(self.post.full_extension())

        if not self.progs.proof_check():
            return False
        
        if not QPredicate.sqsubseteq(self.pre, self.progs.progs[0].pres.pres[0]):
            return False
        
        return True



