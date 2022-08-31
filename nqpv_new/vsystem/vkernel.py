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
# vkernel.py
#
# transform abstract syntax tree to semantic contents, and adjust the verification system
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple
from nqpv_new.vsystem.content.opt_pair_term import OptPairTerm


from nqpv_new.vsystem.content.prog_term import AbortTerm, IfTerm, InitTerm, NondetTerm, ProgDefinedTerm, ProgDefiningTerm, ProgSttSeqTerm, ProgSttTerm, ProgTerm, SkipTerm, SubProgTerm, UnitaryTerm, WhileTerm
from nqpv_new.vsystem.content.qvarls_term import QvarlsTerm

from nqpv_new.vsystem.content.scope_term import ScopeTerm

from nqpv_new import dts

from .settings import Settings
from .syntax import ast
from .log_system import RuntimeErrorWithLog
from .optenv_inject import get_opt_env

class VKernel:
    def __init__(self):
        super().__init__()
        self.cur_scope : ScopeTerm
        self.reset()

    def reset(self) -> None:
        self.cur_scope = ScopeTerm("global", None)
        self.cur_scope.inject(get_opt_env())

    def push(self, label : str) -> None:
        '''
        create a new child scope and enter the scope
        '''
        if not isinstance(label, str):
            raise ValueError()

        child = ScopeTerm(label, self.cur_scope)
        # store the child scope in the current scope
        self.cur_scope[label] = child
        self.cur_scope = child
    
    def pop(self) -> ScopeTerm:
        '''
        return to the parent scope
        '''
        if self.cur_scope.parent_scope is None:
            raise Exception("can not exit the global scope")

        r = self.cur_scope
        self.cur_scope = self.cur_scope.parent_scope
        return r

    def inject(self, scope : ScopeTerm) -> None:
        '''
        inject the scope to the current scope
        variables with the same name will not be reassigned
        '''
        self.cur_scope.inject(scope)


    def process_ast(self, env_ast : ast.AstScope) -> None:
        '''
        in the current scope, process the scope abstract syntax tree
        '''
        for cmd in env_ast.cmd_ls:

            if isinstance(cmd, ast.AstDefinition):

                # create the var being defined
                if isinstance(cmd.vtype, ast.AstTypeProg):
                    defining_var = ProgDefiningTerm(self.eval_qvarls(cmd.vtype.qvarls))
                else:
                    raise Exception("unexpected situation")
                self.cur_scope[cmd.var.id] = defining_var

                # create the subenvironments                        
                self.push("scope_" + cmd.var.id)

                # process the scope
                if cmd.scope_expr.scope is not None:
                    self.process_ast(cmd.scope_expr.scope)

                # evaluate
                value = self.eval_expr(cmd.vtype, cmd.scope_expr.expr.data)
                # exit the subenvironments
                self.pop()
                
                # assign
                self.cur_scope.remove_var(cmd.var.id)
                self.cur_scope[cmd.var.id] = value

            elif isinstance(cmd, ast.AstAxiom):
                raise NotImplementedError()
            else:
                raise Exception("unexpected situation")
    
    def eval_qvarls(self, qvarls : ast.AstQvarLs) -> QvarlsTerm:
        try:
            id_ls = []
            for item in qvarls.data:
                if item.id in self.cur_scope:
                    raise RuntimeErrorWithLog("The variable '" + str(item) + "' already exists, and cannot be used as a quantum variable identifier.")
                id_ls.append(item.id)

            return QvarlsTerm(tuple(id_ls))
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("Invalid quantum variable list.", qvarls.pos)

    def eval_prog(self, data : ast.Ast) -> ProgSttTerm:
        try:
            if isinstance(data, ast.AstSkip):
                return SkipTerm()
            elif isinstance(data, ast.AstAbort):
                return AbortTerm()
            elif isinstance(data, ast.AstInit):
                qvarls = self.eval_qvarls(data.qvar_ls)
                return InitTerm(qvarls)
            elif isinstance(data, ast.AstUnitary):
                opt = self.cur_scope[data.opt.id]
                qvarls = self.eval_qvarls(data.qvar_ls)
                pair = OptPairTerm(opt, qvarls)
                return UnitaryTerm(pair)
            elif isinstance(data, ast.AstIf):
                S1 = self.eval_prog(data.prog1)
                S0 = self.eval_prog(data.prog0)
                opt = self.cur_scope[data.opt.id]
                qvarls = self.eval_qvarls(data.qvar_ls)
                pair = OptPairTerm(opt, qvarls)
                return IfTerm(pair, S1, S0)
            elif isinstance(data, ast.AstWhile):
                S = self.eval_prog(data.prog)
                opt = self.cur_scope[data.opt.id]
                qvarls = self.eval_qvarls(data.qvar_ls)
                pair = OptPairTerm(opt, qvarls)
                return WhileTerm(pair, S)
            elif isinstance(data, ast.AstNondet):
                prog_ls = []
                for subprog in data.data:
                    prog_ls.append(self.eval_prog(subprog))
                return NondetTerm(tuple(prog_ls))
            elif isinstance(data, ast.AstSubprog):
                subprog = self.cur_scope[data.subprog.id]
                qvarls = self.eval_qvarls(data.qvar_ls)
                return SubProgTerm(subprog, qvarls)
            elif isinstance(data, ast.AstProg):
                prog_ls = []
                for subprog in data.data:
                    prog_ls.append(self.eval_prog(subprog))
                return ProgSttSeqTerm(tuple(prog_ls))
            else:
                raise Exception("unexpected situation")
        except RuntimeErrorWithLog:
            # report the failure
            raise RuntimeErrorWithLog("Invalid '" + data.label + "' statement.", data.pos)

    def eval_expr(self, expr_type : ast.AstType, expr_data : ast.Ast) -> dts.Term:
        '''
        evaluate the expression and return the value (containing type and data)
        '''
        if isinstance(expr_type, ast.AstTypeProg):
            if not isinstance(expr_data, ast.AstProg):
                raise Exception("unexpected situation")

            prog_content = self.eval_prog(expr_data)
            arg_ls = self.eval_qvarls(expr_type.qvarls)
            return ProgDefinedTerm(prog_content, arg_ls)
            
        elif isinstance(expr_type, ast.AstTypeProof):
            if not isinstance(expr_data, ast.AstProof):
                raise Exception("unexpected situation")
            
            raise NotImplementedError()

            para_list = [id.id for id in ast_type.data[1].data]
            proof = eval_proof(self.cur_venv, expr.data.qvar_seq(tuple(para_list)), None, expr.data)
            
            # move the generated variables to the parent scope
            for pair in proof.pre.pairs:
                self.cur_venv.move_var_up(pair[0])
            for pair in proof.post.pairs:
                self.cur_venv.move_var_up(pair[0])

            return Value(VType("proof", ()), proof)
        else:
            raise Exception("unexpected situation")

