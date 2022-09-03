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
# ast.py
#
# the abstract syntax tree
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Tuple

from .pos_info import PosInfo

class Ast:
    def __init__(self, pos : PosInfo, ast_label : str):
        pass
        self.pos : PosInfo = pos
        self.label : str = ast_label
        #self.legal : bool = True

class AstScope(Ast):
    def __init__(self, pos : PosInfo, cmd_ls : List[Ast]):
        super().__init__(pos, "scope")
        self.cmd_ls : List[Ast] = cmd_ls

class AstDefinition(Ast):
    def __init__(self, pos : PosInfo, var : AstID, vtype : AstType, scope_expr : AstScopeExpr):
        super().__init__(pos, "definition")
        self.var : AstID = var
        self.vtype : AstType = vtype
        self.scope_expr : AstScopeExpr = scope_expr

class AstAxiom(Ast):
    def __init__(self, pos : PosInfo, subproof : AstID, pre : AstPredicate,
        subprog : AstID, qvar_ls : AstQvarLs, post : AstPredicate):
        super().__init__(pos, "axiom")
        self.subproof : AstID = subproof
        self.pre : AstPredicate = pre
        self.subprog : AstID = subprog
        self.qvar_ls : AstQvarLs = qvar_ls
        self.post : AstPredicate = post

class AstShow(Ast):
    def __init__(self, pos : PosInfo, var : AstID):
        super().__init__(pos, "show")
        self.var : AstID = var


class AstScopeExpr(Ast):
    def __init__(self, pos : PosInfo, scope : AstScope | None, expr : AstExpression):
        super().__init__(pos, "scope expression")
        self.scope : AstScope | None = scope
        self.expr : AstExpression = expr

class AstType(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos, "type")

class AstTypeProg(AstType):
    def __init__(self, pos : PosInfo, qvarls : AstQvarLs):
        super().__init__(pos)
        self.qvarls : AstQvarLs = qvarls
    def __str__(self) -> str:
        return "program " + str(self.qvarls)

class AstTypeProof(AstType):
    def __init__(self, pos : PosInfo, qvarls : AstQvarLs):
        super().__init__(pos)
        self.qvarls : AstQvarLs = qvarls
    def __str__(self) -> str:
        return "proof " + str(self.qvarls)

class AstExpression(Ast):
    def __init__(self, pos : PosInfo, elabel : str, data : AstProgSeq | AstProof):
        super().__init__(pos, "expresssion")
        self.elabel : str = elabel
        self.data : AstProgSeq | AstProof = data

class AstQvarLs(Ast):
    def __init__(self, pos : PosInfo, data : List[AstID]):
        super().__init__(pos, "qvar list")
        self.data : List[AstID] = data
    
    def __len__(self) -> int:
        return len(self.data)

    def __str__(self) -> str:
        if len(self.data) == 0:
            return "[]"

        r = "[" + str(self.data[0])
        for i in range(1, len(self.data)):
            r += " " + str(self.data[i])
        r += "]"
        return r

class AstID(Ast):
    def __init__(self, pos : PosInfo, id : str):
        super().__init__(pos, "ID")
        self.id : str = id
    
    def __str__(self) -> str:
        return self.id

class AstIfProof(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, proof1 : AstProof, proof0 : AstProof):
        super().__init__(pos, "if proof")
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof1 : AstProof = proof1
        self.proof0 : AstProof = proof0

class AstInv(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstID, AstQvarLs]]):
        super().__init__(pos, "loop invariant")
        self.data : List[Tuple[AstID, AstQvarLs]] =  data

class AstUnionProof(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos, "union proof")
        self.data : List[Ast] = data

class AstSubproof(Ast):
    def __init__(self, pos : PosInfo, subproof : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos, "subproof")
        self.subproof : AstID = subproof
        self.qvar_ls : AstQvarLs = qvar_ls
    
    def __str__(self) -> str:
        return str(self.subproof) + str(self.qvar_ls)


class AstWhileProof(Ast):
    def __init__(self, pos : PosInfo, inv : AstInv, opt : AstID, qvar_ls : AstQvarLs, proof : AstProof):
        super().__init__(pos, "while proof")
        self.inv : AstInv = inv
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof : AstProof = proof

class AstNondetProof(Ast):
    def __init__(self, pos : PosInfo, data : List[AstProof]):
        super().__init__(pos, "nondeterministic choice proof")
        self.data : List[AstProof] = data

class AstPredicate(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstID, AstQvarLs]]):
        super().__init__(pos, "predicate")
        self.data : List[Tuple[AstID, AstQvarLs]] = data


class AstProof(Ast):
    def __init__(self, pos : PosInfo, pre : AstPredicate, seq : AstProofSeq, post : AstPredicate):
        super().__init__(pos, "proof")
        self.seq : AstProofSeq = seq
        self.pre : AstPredicate = pre
        self.post : AstPredicate = post

class AstProofSeq(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos, "proof sequence")
        self.data : List[Ast] = data

class AstProgSeq(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos, "program sequence")
        self.data : List[Ast] = data
    

class AstNondet(Ast):
    def __init__(self, pos : PosInfo, data : List[AstProgSeq]):
        super().__init__(pos, "nondeterministic choice")
        self.data : List[AstProgSeq] = data

class AstWhile(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, prog : AstProgSeq):
        super().__init__(pos, "while")
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog : AstProgSeq = prog

class AstIf(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, prog1 : AstProgSeq, prog0 : AstProgSeq):
        super().__init__(pos, "if")
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog1 : AstProgSeq = prog1
        self.prog0 : AstProgSeq = prog0

class AstUnitary(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos, "unitary transformation")
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls


class AstInit(Ast):
    def __init__(self, pos : PosInfo, qvar_ls : AstQvarLs):
        super().__init__(pos, "initialization")
        self.qvar_ls : AstQvarLs = qvar_ls
class AstAbort(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos, "abort")


class AstSkip(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos, "skip")


class AstSubprog(Ast):
    def __init__(self, pos : PosInfo, subprog : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos, "subprogram")
        self.subprog : AstID = subprog
        self.qvar_ls : AstQvarLs = qvar_ls
