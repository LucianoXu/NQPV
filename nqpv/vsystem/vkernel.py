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

from nqpv import dts

from .settings import Settings
from .syntax import ast
from .log_system import LogSystem, RuntimeErrorWithLog
from .optenv_inject import get_opt_env

from .content.qvarls_term import QvarlsTerm
from .content.opt_pair_term import OptPairTerm
from .content.qpre_term import QPreTerm
from .content.prog_term import AbortTerm, IfTerm, InitTerm, NondetTerm, ProgDefinedTerm, ProgDefiningTerm, ProgSttSeqTerm, ProgSttTerm, ProgTerm, SkipTerm, SubProgTerm, UnitaryTerm, WhileTerm
from .content.proof_term import AbortHintTerm, IfHintTerm, InitHintTerm, NondetHintTerm, ProofDefiningTerm, ProofHintTerm, ProofSeqHintTerm, ProofDefinedTerm, QPreHintTerm, SkipHintTerm, SubproofHintTerm, UnionHintTerm, UnitaryHintTerm, WhileHintTerm
from .content.scope_term import ScopeTerm, VarPath


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


    def eval_varpath(self, varpath_ast : ast.AstVar) -> VarPath:
        list = [item.id for item in varpath_ast.data]
        return VarPath(tuple(list))

    def eval_scope(self, scope_ast : ast.AstScope) -> None:
        '''
        in the current scope, process the scope abstract syntax tree
        '''
        for cmd in scope_ast.cmd_ls:

            if isinstance(cmd, ast.AstDefinition):

                self.eval_def(cmd)

            elif isinstance(cmd, ast.AstAxiom):
                raise NotImplementedError()
            elif isinstance(cmd, ast.AstShow):
                var_path = self.eval_varpath(cmd.var)
                if var_path not in self.cur_scope:
                    raise RuntimeErrorWithLog("The variable '" + str(var_path) + "' does not exist.")
                # append the information
                LogSystem.channels["info"].append("\n" + str(cmd.pos) + "\n" + str(self.cur_scope[var_path].eval()))
            else:
                raise Exception("unexpected situation")
    
    def eval_qvarls(self, qvarls : ast.AstQvarLs) -> QvarlsTerm:
        try:
            id_ls = []
            for item in qvarls.data:
                if VarPath((item.id,)) in self.cur_scope:
                    raise RuntimeErrorWithLog("The variable '" + str(item) + "' already exists, and cannot be used as a quantum variable identifier.")
                id_ls.append(item.id)

            return QvarlsTerm(tuple(id_ls))
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("Invalid quantum variable list.", qvarls.pos)

    def eval_qpre(self, qpre : ast.AstPredicate | ast.AstInv) -> QPreTerm:
        try:
            pair_ls : List[OptPairTerm] = []
            for pair in qpre.data:
                var_path = self.eval_varpath(pair[0])
                opt = self.cur_scope[var_path]
                qvarls = self.eval_qvarls(pair[1])
                pair_ls.append(OptPairTerm(opt, qvarls))
            return QPreTerm(tuple(pair_ls))
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("Invalid quantum predicate.", qpre.pos)



    def eval_prog(self, data : ast.Ast) -> ProgSttTerm:
        if isinstance(data, ast.AstSkip):
            return SkipTerm()
        elif isinstance(data, ast.AstAbort):
            return AbortTerm()
        elif isinstance(data, ast.AstInit):
            qvarls = self.eval_qvarls(data.qvar_ls)
            return InitTerm(qvarls)
        elif isinstance(data, ast.AstUnitary):
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return UnitaryTerm(pair)
        elif isinstance(data, ast.AstIf):
            S1 = self.eval_prog(data.prog1)
            S0 = self.eval_prog(data.prog0)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return IfTerm(pair, S1, S0)
        elif isinstance(data, ast.AstWhile):
            S = self.eval_prog(data.prog)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return WhileTerm(pair, S)
        elif isinstance(data, ast.AstNondet):
            prog_ls = []
            for subprog in data.data:
                prog_ls.append(self.eval_prog(subprog))
            return NondetTerm(tuple(prog_ls))
        elif isinstance(data, ast.AstSubprog):
            subprog = self.cur_scope[self.eval_varpath(data.subprog)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            return SubProgTerm(subprog, qvarls)
        elif isinstance(data, ast.AstProgSeq):
            prog_ls = []
            for subprog in data.data:
                prog_ls.append(self.eval_prog(subprog))
            return ProgSttSeqTerm(tuple(prog_ls))
        else:
            raise Exception("unexpected situation")

    def eval_proof(self, data : ast.Ast) -> ProofHintTerm:
        if isinstance(data, ast.AstSkip):
            return SkipHintTerm()
        elif isinstance(data, ast.AstAbort):
            return AbortHintTerm()
        elif isinstance(data, ast.AstInit):
            qvarls = self.eval_qvarls(data.qvar_ls)
            return InitHintTerm(qvarls)
        elif isinstance(data, ast.AstUnitary):
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return UnitaryHintTerm(pair)
        elif isinstance(data, ast.AstIfProof):
            P1 = self.eval_proof(data.proof1)
            P0 = self.eval_proof(data.proof0)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return IfHintTerm(pair, P1, P0)
        elif isinstance(data, ast.AstWhileProof):
            inv = self.eval_qpre(data.inv)
            P = self.eval_proof(data.proof)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return WhileHintTerm(inv, pair, P)
        elif isinstance(data, ast.AstNondetProof):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof(subproof))
            return NondetHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstSubproof):
            subproof = self.cur_scope[self.eval_varpath(data.subproof)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            return SubproofHintTerm(subproof, qvarls)
        elif isinstance(data, ast.AstUnionProof):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof(subproof))
            return UnionHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstProofSeq):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof(subproof))
            return ProofSeqHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstPredicate):
            qpre = self.eval_qpre(data)
            return QPreHintTerm(qpre)
        else:
            raise Exception("unexpected situation")

    def eval_def(self, cmd : ast.AstDefinition) -> None:
        '''
        evaluate the expression and return the value (containing type and data)
        '''
        try:            
            if isinstance(cmd.vtype, ast.AstTypeProg):
                # create the var being defined
                self.cur_scope[cmd.var.id] = ProgDefiningTerm(self.eval_qvarls(cmd.vtype.qvarls))

                if not isinstance(cmd.expr.data, ast.AstProgSeq):
                    raise Exception("unexpected situation")

                # evaluate
                prog_content = self.eval_prog(cmd.expr.data)
                arg_ls = self.eval_qvarls(cmd.vtype.qvarls)
                value = ProgDefinedTerm(prog_content, arg_ls)
                
                # assign
                self.cur_scope.remove_var(cmd.var.id)
                self.cur_scope[cmd.var.id] = value

            elif isinstance(cmd.vtype, ast.AstTypeProof):
                # create the var being defined
                self.cur_scope[cmd.var.id] = ProofDefiningTerm(self.eval_qvarls(cmd.vtype.qvarls))

                if not isinstance(cmd.expr.data, ast.AstProof):
                    raise Exception("unexpected situation")
                
                # evaluate
                proof_hint = self.eval_proof(cmd.expr.data.seq)
                arg_ls = self.eval_qvarls(cmd.vtype.qvarls)
                value = ProofDefinedTerm(
                    self.eval_qpre(cmd.expr.data.pre), 
                    proof_hint, 
                    self.eval_qpre(cmd.expr.data.post), 
                    arg_ls, self.cur_scope
                )

                # assign
                self.cur_scope.remove_var(cmd.var.id)
                self.cur_scope[cmd.var.id] = value

            elif isinstance(cmd.vtype, ast.AstTypeScope):
                if not isinstance(cmd.expr.data, ast.AstScope):
                    raise Exception("unexpected situation")
                
                self.push(cmd.var.id)
                self.eval_scope(cmd.expr.data)
                self.pop()

            else:
                raise Exception("unexpected situation")
        except RuntimeErrorWithLog:
            # report the failure
            raise RuntimeErrorWithLog("Invalid '" + cmd.expr.data.label + "' definition.", cmd.expr.data.pos)

