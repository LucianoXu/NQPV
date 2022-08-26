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
# nondet_proof.py
#
# nondeterministic choice structure
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from ...log_system import RuntimeErrorWithLog
from ...syntax.pos_info import PosInfo
from .proof import QProof, QProofStatement
from ..predicate.qpredicate import QPredicate

class QNondetProof(QProofStatement):
    def __init__(self, pos : PosInfo, pre : QPredicate, post : QPredicate, subproofs : List[QProof]):
        super().__init__(pos, pre, post)
        self.subproofs : List[QProof] = subproofs
