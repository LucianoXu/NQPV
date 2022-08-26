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
# contains the essential methods
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv_new.vsystem.content.prog.eval_prog import eval_prog
from nqpv_new.vsystem.content.proof.eval_proof import eval_proof

from .var_env import VType, Value, VarEnv
from .settings import Settings
from .syntax import ast
from .log_system import RuntimeErrorWithLog
from .venv import VEnv
from .optenv_inject import get_opt_env

class VKernel:
    def __init__(self):
        super().__init__()
        self.cur_venv : VEnv
        self.reset()
        self.cur_venv.var_env_inject(get_opt_env())

    def reset(self) -> None:
        self.cur_venv = VEnv(None)

    def push(self) -> None:
        '''
        create a new child environment
        '''
        child = VEnv(self.cur_venv)
        child.refresh()
        self.cur_venv = child
    
    def pop(self) -> VEnv:
        '''
        return to the parent environment
        '''
        if self.cur_venv.parent is None:
            raise Exception("can not exit the global environment")

        r = self.cur_venv
        self.cur_venv = self.cur_venv.parent
        self.cur_venv.refresh()
        return r

    def env_inject(self, env : VEnv) -> None:
        '''
        inject the environment to the current environment
        (variables with the same name will be reassigned, and settings will be updated)
        '''
        self.cur_venv.env_inject(env)
        self.cur_venv.refresh()


    def process_env(self, env_ast : ast.AstEnv) -> VEnv:
        '''
        in the current environment, process the environment abstract syntax tree
        return None when env_ast cannot be property processed
        '''
        self.push()

        for cmd in env_ast.cmd_ls:

            if isinstance(cmd, ast.AstDefinition):
                # check the special case first
                if isinstance(cmd.var, ast.AstOptGetLs):
                    if cmd.vtype.data[0] != "wp":
                        raise RuntimeErrorWithLog("The type should be 'wp'.", cmd.pos)

                # get the type
                if cmd.vtype.type == "proof_limited":
                    vtype = VType("proof", cmd.vtype.data)
                else:
                    vtype = VType(cmd.vtype.type, (len(cmd.vtype.data[1]),))

                # create the subenvironments                        
                self.push()

                # process the environment
                if cmd.expr.env is not None:
                    sub_env = self.process_env(cmd.expr.env)
                    self.env_inject(sub_env)

                # evaluate
                value = self.eval_expr(cmd.vtype, cmd.expr)
                # exit the subenvironments
                self.pop()
                
                # assign
                if isinstance(cmd.var, ast.AstOptGetLs):
                    self.cur_venv.var_env.assign_var(cmd.var, vtype, value)
                else:
                    self.cur_venv.var_env.assign_var(cmd.var.id, vtype, value)


            elif isinstance(cmd, ast.AstExample):
                # create the subenvironments                        
                self.push()
                # process the environment
                if cmd.expr.env is not None:
                    sub_env = self.process_env(cmd.expr.env)
                    self.env_inject(sub_env)

                # we need to implement the automatic type hint
                raise NotImplementedError()

                # evaluate only
                value = self.eval_expr(cmd.expr)
                # exit the subenvironments
                self.pop()

            elif isinstance(cmd, ast.AstAxiom):
                raise NotImplementedError()
            else:
                raise Exception("unexpected situation")
            
        return self.pop()


    def eval_expr(self, ast_type : ast.AstType, expr : ast.AstExpression) -> Value:
        '''
        evaluate the expression and return the value (containing type and data)
        '''
        if expr.elabel == 'program':
            if not isinstance(expr.data, ast.AstProg):
                raise Exception("unexpected situation")

            prog = eval_prog(self.cur_venv, expr.data)
            return Value(VType("program", ()), prog)
        elif expr.elabel == 'proof':
            if not isinstance(expr.data, ast.AstProof):
                raise Exception("unexpected situation")
            
            para_list = [id.id for id in ast_type.data[1].data]
            proof = eval_proof(self.cur_venv, expr.data.qvar_seq(tuple(para_list)), None, expr.data)
            
            # move the generated variables to the parent environment
            for pair in proof.pre.pairs:
                self.cur_venv.move_var_up(pair[0])
            for pair in proof.post.pairs:
                self.cur_venv.move_var_up(pair[0])

            return Value(VType("proof", ()), proof)
        elif expr.elabel == 'wp':
            raise NotImplementedError()
        else:
            raise Exception("unexpected situation")

