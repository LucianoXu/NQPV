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
# qprog_nondet.py
#
# nondeterministic choice structure
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from .opt_env import Operator, OptEnv
from .qVar import QvarLs
from .opt_qvar_pair import OptQvarPair
from .qPre import QPredicate
from .qprog_std import QProg, QProgSequence, Preconditions

from ..logsystem import LogSystem
from ..tools import code_add_prefix

class QProgNondet(QProg):
    '''
    We will not allow intermediate assertions before Sequence, 
    since they can always be considered as the preconditions of the first subprogram in the sequence.
    '''
    def __new__(cls, pres : Preconditions | None, data : QProgSequence | QProgNondet | None):
        if data is None:
            LogSystem.channels["error"].append("The program provided here is invalid.")
            return None

        # examine whether it is a copy construction
        if isinstance(data, QProgNondet):
            instance = super().__new__(cls, data.pres)
            if instance is None:
                return None
            instance.label = "NONDET_CHOICE"
            instance.post = data.post
            instance.progs = data.progs   # type: ignore
            return instance 

        instance = super().__new__(cls, pres)
        if instance is None:
            return None
        instance.label = "NONDET_CHOICE"
        instance.progs = (data,)  # type: ignore

        return instance
    
    def __init__(self, pres : Preconditions | None, data : QProgSequence | QProgNondet | None):
        super().__init__(pres)
        self.progs : Tuple[QProgSequence,...]
    
    @staticmethod
    def append(obj : QProgNondet | None, prog: QProgSequence | None) -> QProgNondet | None:
        if obj is None or prog is None:
            LogSystem.channels["error"].append("The components provided for 'nondet choice' here are invalid.")
            return None

        result = QProgNondet(None, obj) # type: ignore
        result.progs = result.progs + (prog,)
        return result

    def __str__(self) -> str:
        r = "(\n" + code_add_prefix(str(self.progs[0]), "\t") + "\n"
        for i in range(1, len(self.progs)):
            r += "# \n" + code_add_prefix(str(self.progs[i]), "\t") + "\n"
        r += ")"
        return self._pre_post_decorate(r)

    def _wp(self) -> QPredicate | None:
        if self.post is None:
            raise Exception("unexpected situation")
        
        r = QPredicate([])
        for prog in self.progs:
            prog.set_post(self.post)
            if not prog.proof_check():
                return None
            for pre in prog.get_pre().opts:
                r = QPredicate.append(r, pre)
        
        return r
        
