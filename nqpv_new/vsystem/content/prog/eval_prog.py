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
# eval_prog.py
#
# evaluate the program expression, invocated by the kernel
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from ...var_env import Value, VarEnv
from ...settings import Settings
from ...syntax import ast
from ...log_system import RuntimeErrorWithLog
from ...venv import VEnv

from .prog import QProg, QSkip, QAbort, QInit, QSubprog, QUnitary, QIf, QWhile
from .nondet import QNondet

from ..content_tools import opt_qvarls_check


def eval_skip(venv : VEnv, ast_stt : ast.AstSkip):
    return QSkip(ast_stt.pos)

def eval_abort(venv : VEnv, ast_stt : ast.AstAbort):
    return QAbort(ast_stt.pos)

def eval_init(venv : VEnv, ast_stt : ast.AstInit):
    id_ls = [id.id for id in ast_stt.qvar_ls.data]
    return QInit(ast_stt.pos, id_ls)

def eval_unitary(venv : VEnv, ast_stt : ast.AstUnitary):
    try:
        opt_qvarls_check(venv, ast_stt.opt, 'unitary', ast_stt.qvar_ls)
        id_ls = [id.id for id in ast_stt.qvar_ls.data]
        return QUnitary(ast_stt.qvar_ls.pos, id_ls, ast_stt.opt.id)

    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'unitary transform' statement.", ast_stt.pos)
    
def eval_if(venv : VEnv, ast_stt : ast.AstIf):
    try:
        opt_qvarls_check(venv, ast_stt.opt, 'measurement', ast_stt.qvar_ls)
        S1 = eval_prog(venv, ast_stt.prog1)
        S0 = eval_prog(venv, ast_stt.prog0)
        id_ls = [id.id for id in ast_stt.qvar_ls.data]

        return QIf(ast_stt.pos, ast_stt.opt.id, id_ls, S1, S0)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'if' statement.", ast_stt.pos)

def eval_while(venv : VEnv, ast_stt : ast.AstWhile):
    try:
        opt_qvarls_check(venv, ast_stt.opt, 'measurement', ast_stt.qvar_ls)
        S = eval_prog(venv, ast_stt.prog)
        id_ls = [id.id for id in ast_stt.qvar_ls.data]

        return QWhile(ast_stt.pos, ast_stt.opt.id, id_ls, S)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'while' statement.", ast_stt.pos)

def eval_nondet(venv : VEnv, ast_stt : ast.AstNondet):
    try:
        subprogs : List[QProg] = []
        for ast_prog in ast_stt.data:
            subprogs.append(eval_prog(venv, ast_prog))
        return QNondet(ast_stt.pos, subprogs)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'nondeterministic choice' statement.", ast_stt.pos)

def eval_subprog(venv : VEnv, ast_stt : ast.AstSubprog):
    try:
        subprog =  venv.get_var(ast_stt.subprog.id)
        if subprog.vtype.type != "program":
            raise RuntimeErrorWithLog("The variable '" + ast_stt.subprog.id + "' is not a program.", ast_stt.pos)
        if subprog.get_property("qnum") != len(ast_stt.qvar_ls):
            raise RuntimeErrorWithLog(            
            "The program '" + str(ast_stt.subprog.id) + "' operates on " + str(subprog.get_property("qnum")) +
            " qubits, while the quantum variable list has " + str(len(ast_stt.qvar_ls)) + " qubits.", ast_stt.subprog.pos
        )
        id_ls = [id.id for id in ast_stt.qvar_ls.data]

        return QSubprog(ast_stt.pos, ast_stt.subprog.id, id_ls)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'subprogram' statement.", ast_stt.pos)

eval_dict = {
    ast.AstSkip : eval_skip,
    ast.AstAbort : eval_abort,
    ast.AstInit : eval_init,
    ast.AstUnitary : eval_unitary,
    ast.AstIf : eval_if,
    ast.AstWhile : eval_while,
    ast.AstNondet : eval_nondet,
    ast.AstSubprog : eval_subprog,
}

def eval_prog(venv : VEnv, ast_prog : ast.AstProg) -> QProg:
    r = QProg(ast_prog.pos, [])
    for statement in ast_prog.data:
        if type(statement) in eval_dict:
            r.statements.append(
                eval_dict[type(statement)](venv, statement)  # type: ignore
            )
        else:
            raise Exception("unexpected situation")


    return r
