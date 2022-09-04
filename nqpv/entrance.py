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

# the entrance of this verification system

from __future__ import annotations
from typing import Any, List, Dict, Tuple

import os

from .vsystem import vkernel
from .vsystem.content.scope_term import ScopeTerm
from .vsystem.log_system import LogSystem, RuntimeErrorWithLog

def verify(path : str) -> None:
    LogSystem("error", "Error: ")
    LogSystem("warning", "Warning: ")
    LogSystem("info")
    
    try:
        p_prog = open(path, 'r')
        prog_str = p_prog.read()
        p_prog.close()
    except:
        raise FileNotFoundError()
    
    folder_path = os.path.dirname(path)

    kernel = vkernel.VKernel("global", folder_path)

    try:
        ast_scope = vkernel.get_ast(prog_str)
        scope = kernel.eval_scope(ast_scope)
    except RuntimeErrorWithLog:
        pass

    LogSystem("error").summary(None, True)
    LogSystem("info").summary(None, True)
    

