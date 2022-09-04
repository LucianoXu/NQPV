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
from .optenv import get_opt_env, optload, optsave

from .content.qvarls_term import QvarlsTerm
from .content.opt_pair_term import OptPairTerm
from .content.qpre_term import QPreTerm
from .content.prog_term import type_prog, AbortTerm, IfTerm, InitTerm, NondetTerm, ProgDefinedTerm, ProgDefiningTerm, ProgSttSeqTerm, ProgSttTerm, ProgTerm, SkipTerm, SubProgTerm, UnitaryTerm, WhileTerm
from .content.proof_term import type_proof, AbortHintTerm, IfHintTerm, InitHintTerm, NondetHintTerm, ProofDefiningTerm, ProofHintTerm, ProofSeqHintTerm, ProofDefinedTerm, QPreHintTerm, SkipHintTerm, SubproofHintTerm, UnionHintTerm, UnitaryHintTerm, WhileHintTerm
from .content.scope_term import ScopeTerm, VarPath


class VKernel:
    def __init__(self, name : str, parent : VKernel | None = None):
        '''
        parent : the parent scope. if None, then the new scope will be created
        '''
        super().__init__()
        self.cur_scope : ScopeTerm
        if parent is None:
            self.cur_scope = ScopeTerm(name, None)
            self.cur_scope.inject(get_opt_env())
        else:
            self.cur_scope = ScopeTerm(name, parent.cur_scope)


    def inject(self, scope : ScopeTerm) -> None:
        '''
        inject the scope to the current scope
        variables with the same name will not be reassigned
        '''
        self.cur_scope.inject(scope)


    def eval_varpath(self, varpath_ast : ast.AstVar) -> VarPath:
        list = [item.id for item in varpath_ast.data]
        return VarPath(tuple(list))

    def eval_scope(self, scope_ast : ast.AstScope, name = "local_scope") -> ScopeTerm:
        '''
        evaluate the scope using a subkernel. this allows the nested setting strategy
        '''
        new_kernel = VKernel(name, self)
        for cmd in scope_ast.cmd_ls:

            if isinstance(cmd, ast.AstDefinition):
                try:
                    new_kernel.eval_def(cmd)
                except RuntimeErrorWithLog:
                    raise RuntimeErrorWithLog("Invalid 'def' command.", cmd.pos)

            elif isinstance(cmd, ast.AstAxiom):
                try:
                    raise NotImplementedError()
                except RuntimeErrorWithLog:
                    raise RuntimeErrorWithLog("Invalid 'axiom' command.", cmd.pos)

            elif isinstance(cmd, ast.AstShow):
                try:
                    # append the information
                    LogSystem.channels["info"].append("\n" + str(cmd.pos) + "\n" + str(new_kernel.eval_expr(cmd.expr)))
                except RuntimeErrorWithLog:
                    raise RuntimeErrorWithLog("Invalid 'show' command.", cmd.pos)

            elif isinstance(cmd, ast.AstSaveOpt):
                try:
                    var_path = new_kernel.eval_varpath(cmd.var)
                    optsave(new_kernel.cur_scope[var_path], cmd.path)
                except RuntimeErrorWithLog:
                    raise RuntimeErrorWithLog("Invalid 'save' command.", cmd.pos)
            else:
                raise Exception()
            
        return new_kernel.cur_scope
    
    def eval_qvarls(self, qvarls : ast.AstQvarLs) -> QvarlsTerm:
        try:
            id_ls = []
            for item in qvarls.data:
                # now we do not require this
                '''
                if VarPath((item.id,)) in self.cur_scope:
                    raise RuntimeErrorWithLog("The variable '" + str(item) + "' already exists, and cannot be used as a quantum variable identifier.")
                '''
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
            raise Exception()

    def eval_proof_hint(self, data : ast.Ast) -> ProofHintTerm:
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
            P1 = self.eval_proof_hint(data.proof1)
            P0 = self.eval_proof_hint(data.proof0)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return IfHintTerm(pair, P1, P0)
        elif isinstance(data, ast.AstWhileProof):
            inv = self.eval_qpre(data.inv)
            P = self.eval_proof_hint(data.proof)
            opt = self.cur_scope[self.eval_varpath(data.opt)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            pair = OptPairTerm(opt, qvarls)
            return WhileHintTerm(inv, pair, P)
        elif isinstance(data, ast.AstNondetProof):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof_hint(subproof))
            return NondetHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstSubproof):
            subproof = self.cur_scope[self.eval_varpath(data.subproof)]
            qvarls = self.eval_qvarls(data.qvar_ls)
            return SubproofHintTerm(subproof, qvarls)
        elif isinstance(data, ast.AstUnionProof):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof_hint(subproof))
            return UnionHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstProofSeq):
            proof_ls = []
            for subproof in data.data:
                proof_ls.append(self.eval_proof_hint(subproof))
            return ProofSeqHintTerm(tuple(proof_ls))
        elif isinstance(data, ast.AstPredicate):
            qpre = self.eval_qpre(data)
            return QPreHintTerm(qpre)
        else:
            raise Exception()
    
    def eval_expr(self, expr : ast.AstExpression) -> dts.Term:
        '''
        this method will always return the value, not the variable
        '''
        try:
            if isinstance(expr, ast.AstExpressionVar):
                var_path = self.eval_varpath(expr.var)
                return self.cur_scope[var_path].val

            elif isinstance(expr, ast.AstExpressionValue):
                if isinstance(expr.data, ast.AstProgExpr):    
                    # definition
                    if isinstance(expr.data.data, ast.AstProgSeq):
                        if not isinstance(expr.data.type, ast.AstTypeProg):
                            raise Exception()
                        prog_seq = self.eval_prog(expr.data.data)
                        arg_ls = self.eval_qvarls(expr.data.type.qvarls)
                        return ProgDefinedTerm(prog_seq, arg_ls)
                    else:
                        raise RuntimeErrorWithLog("The expression is not of type '" + str(expr.data.type) + "'.", expr.data.pos)
                    
                elif isinstance(expr.data, ast.AstProofExpr):
                    #definition
                    if isinstance(expr.data.data, ast.AstProof):
                        if not isinstance(expr.data.type, ast.AstTypeProof):
                            raise Exception()
                        pre = self.eval_qpre(expr.data.data.pre)
                        proof_hint_seq = self.eval_proof_hint(expr.data.data.seq)
                        post = self.eval_qpre(expr.data.data.post)
                        arg_ls = self.eval_qvarls(expr.data.type.qvarls)
                        return proof_hint_seq.construct_proof(pre, post, arg_ls, self.cur_scope)
                    else:
                        raise RuntimeErrorWithLog("The expression is not of type '" + str(expr.data.type) + "'.", expr.data.pos)

                elif isinstance(expr.data, ast.AstLoadOpt):
                    return optload(expr.data.path)

                elif isinstance(expr.data, ast.AstScope):
                    return self.eval_scope(expr.data)
                else:
                    raise Exception()
            else:
                raise Exception()

        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("Invalid expression.", expr.pos)
        
    def eval_def(self, cmd : ast.AstDefinition) -> None:
        '''
        evaluate the expression and return the value (containing type and data)
        '''
        try:            
            if isinstance(cmd.expr, ast.AstExpressionVar):
                var_path = self.eval_varpath(cmd.expr.var)
                self.cur_scope[cmd.var.id] = self.cur_scope[var_path]
            elif isinstance(cmd.expr, ast.AstExpressionValue):
                if isinstance(cmd.expr.data, ast.AstProgExpr):
                    if not isinstance(cmd.expr.data.type, ast.AstTypeProg):
                        raise Exception()
                    # create the var being defined
                    self.cur_scope[cmd.var.id] = ProgDefiningTerm(self.eval_qvarls(cmd.expr.data.type.qvarls))

                    # evaluate
                    value = self.eval_expr(cmd.expr)
                    
                    # assign
                    self.cur_scope.remove_var(cmd.var.id)
                    self.cur_scope[cmd.var.id] = value

                elif isinstance(cmd.expr.data, ast.AstProofExpr):
                    if not isinstance(cmd.expr.data.type, ast.AstTypeProof):
                        raise Exception()
                    # create the var being defined
                    self.cur_scope[cmd.var.id] = ProofDefiningTerm(self.eval_qvarls(cmd.expr.data.type.qvarls))
                    
                    # evaluate
                    value = self.eval_expr(cmd.expr)

                    # assign
                    self.cur_scope.remove_var(cmd.var.id)
                    self.cur_scope[cmd.var.id] = value

                elif isinstance(cmd.expr.data, ast.AstScope):                    
                    subscope = self.eval_scope(cmd.expr.data, cmd.var.id)
                    self.cur_scope[cmd.var.id] = subscope

                # normal assignment
                elif isinstance(cmd.expr.data, ast.AstLoadOpt):
                    self.cur_scope[cmd.var.id] = self.eval_expr(cmd.expr)
                else:
                    raise Exception()
            else:
                raise Exception()

        except RuntimeErrorWithLog:
            # report the failure
            raise RuntimeErrorWithLog("Invalid definition command.", cmd.pos)

