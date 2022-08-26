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
# content_tools.py
#
# define the tools used in content description
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple

from ..syntax import ast
from ..log_system import RuntimeErrorWithLog
from ..venv import VEnv


def opt_qvarls_check(venv : VEnv, opt_id : ast.AstID, property : str, qvar_ls : ast.AstQvarLs) -> None:
    opt =  venv.get_var(opt_id.id)
    # check for operator and property
    if opt.vtype.type != "operator":
        raise RuntimeErrorWithLog("The variable '" + str(opt_id) + "' is not an operator.", opt_id.pos)
    if not opt.get_property(property):
        raise RuntimeErrorWithLog("The operator '" + str(opt_id) + "' is not '" + property + "'.", opt_id.pos)
    # check qubit number
    if opt.get_property("qnum") != len(qvar_ls):
        raise RuntimeErrorWithLog(
            "The operator '" + str(opt_id) + "' operates on " + str(opt.get_property("qnum")) +
            " qubit(s), while the quantum variable list has " + str(len(qvar_ls)) + " qubit(s).", opt_id.pos
        )
    # check whether qvar_ls has no repeat ids
    if not qvar_ls.no_repeat():
        raise RuntimeErrorWithLog("There are repeat quantum variables in the list " + 
            str(qvar_ls) + " .", qvar_ls.pos)
