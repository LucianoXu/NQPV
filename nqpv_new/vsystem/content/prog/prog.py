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
# prog.py
#
# define the value of programs. semantic checks are done in eval_prog.py
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from ...log_system import RuntimeErrorWithLog
from ...syntax.pos_info import PosInfo

class QProgStatement:
    def __init__(self, pos : PosInfo):
        self.pos : PosInfo = pos
        
class QSkip(QProgStatement):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)

class QAbort(QProgStatement):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)

class QInit(QProgStatement):
    def __init__(self, pos : PosInfo, qvar_ls : List[str]):
        super().__init__(pos)
        self.qvar_ls : List[str] = qvar_ls
    
class QUnitary(QProgStatement):
    def __init__(self, pos : PosInfo, qvar_ls : List[str], opt : str):
        super().__init__(pos)
        self.qvar_ls : List[str] = qvar_ls
        self.opt : str = opt

class QIf(QProgStatement):
    def __init__(self, pos : PosInfo, opt : str, qvar_ls : List[str], S1 : QProg, S0 : QProg):
        super().__init__(pos)
        self.opt : str = opt
        self.qvar_ls : List[str] = qvar_ls
        self.S1 : QProg = S1
        self.S0 : QProg = S0

class QWhile(QProgStatement):
    def __init__(self, pos : PosInfo, opt : str, qvar_ls : List[str], S : QProg):
        super().__init__(pos)
        self.opt : str = opt
        self.qvar_ls : List[str] = qvar_ls
        self.S : QProg = S

class QSubprog(QProgStatement):
    def __init__(self, pos : PosInfo, prog_id : str, qvar_ls : List[str]):
        super().__init__(pos)
        self.prog_id : str = prog_id
        self.qvar_ls : List[str] = qvar_ls
    
class QProg:
    def __init__(self, pos : PosInfo, statements : List[QProgStatement]):
        self.pos : PosInfo = pos
        self.statements : List[QProgStatement] = statements

