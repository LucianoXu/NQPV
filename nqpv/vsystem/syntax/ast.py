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

class AstScope(Ast):
    def __init__(self, pos : PosInfo, cmd_ls : List[Ast]):
        super().__init__(pos, "scope")
        self.cmd_ls : List[Ast] = cmd_ls

class AstDefinition(Ast):
    def __init__(self, pos : PosInfo, var : AstID, expr : AstExpression):
        super().__init__(pos, "definition")
        self.var : AstID = var
        self.expr : AstExpression = expr

class AstAxiom(Ast):
    def __init__(self, pos : PosInfo, subproof : AstID, pre : AstPredicate,
        subprog : AstID, qvar_ls : AstQvarLs, post : AstPredicate):
        super().__init__(pos, "axiom")
        raise NotImplementedError()

class AstSetting(Ast):
    def __init__(self, pos : PosInfo, setting_item : str, data : Any):
        super().__init__(pos, "setting")
        self.setting_item : str = setting_item
        self.data : Any = data

class AstShow(Ast):
    def __init__(self, pos : PosInfo, expr : AstExpression):
        super().__init__(pos, "show")
        self.expr : AstExpression = expr

class AstSaveOpt(Ast):
    def __init__(self, pos : PosInfo, var : AstVar, path : str):
        super().__init__(pos, "save operator")
        self.var : AstVar = var
        self.path : str = path


class AstType(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos, "type")

class AstTypeScope(AstType):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)

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

class AstTypeOperator(AstType):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)


class AstLoadOpt(Ast):
    def __init__(self, pos : PosInfo, path : str):
        super().__init__(pos, "load operator")
        self.path : str = path

class AstExpression(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos, "expresssion")

class AstProofExpr(Ast):
    def __init__(self, pos : PosInfo, type : AstType, data : AstProofSeq):
        super().__init__(pos, "proof expression")
        self.type : AstType = type
        self.data : AstProofSeq = data

class AstProgExpr(Ast):
    def __init__(self, pos : PosInfo, type : AstType, data : AstProgSeq):
        super().__init__(pos, "program expression")
        self.type : AstType = type
        self.data : AstProgSeq = data

class AstExpressionValue(AstExpression):
    def __init__(self, pos : PosInfo, data : Ast):
        super().__init__(pos)
        self.data : Ast = data

class AstExpressionVar(AstExpression):
    def __init__(self, pos : PosInfo, var : AstVar):
        super().__init__(pos)
        self.var : AstVar = var

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

class AstVar(Ast):
    def __init__(self, pos : PosInfo, data : List[AstID]):
        super().__init__(pos, "variable")
        self.data : List[AstID] = data
    
    def __str__(self) -> str:
        r = str(self.data[0])
        for i in range(1, len(self.data)):
            r += "." + str(self.data[i])
        return r

class AstID(Ast):
    def __init__(self, pos : PosInfo, id : str):
        super().__init__(pos, "ID")
        self.id : str = id
    
    def __str__(self) -> str:
        return self.id

class AstIfProof(Ast):
    def __init__(self, pos : PosInfo, opt : AstVar, qvar_ls : AstQvarLs, proof1 : AstProof, proof0 : AstProof):
        super().__init__(pos, "if proof")
        self.opt : AstVar = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof1 : AstProof = proof1
        self.proof0 : AstProof = proof0

class AstInv(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstVar, AstQvarLs]]):
        super().__init__(pos, "loop invariant")
        self.data : List[Tuple[AstVar, AstQvarLs]] =  data

class AstUnionProof(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos, "union proof")
        self.data : List[Ast] = data

class AstSubproof(Ast):
    def __init__(self, pos : PosInfo, subproof : AstVar, qvar_ls : AstQvarLs):
        super().__init__(pos, "subproof")
        self.subproof : AstVar = subproof
        self.qvar_ls : AstQvarLs = qvar_ls
    
    def __str__(self) -> str:
        return str(self.subproof) + str(self.qvar_ls)


class AstWhileProof(Ast):
    def __init__(self, pos : PosInfo, inv : AstInv, opt : AstVar, qvar_ls : AstQvarLs, proof : AstProof):
        super().__init__(pos, "while proof")
        self.inv : AstInv = inv
        self.opt : AstVar = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof : AstProof = proof

class AstNondetProof(Ast):
    def __init__(self, pos : PosInfo, data : List[AstProof]):
        super().__init__(pos, "nondeterministic choice proof")
        self.data : List[AstProof] = data

class AstPredicate(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstVar, AstQvarLs]]):
        super().__init__(pos, "predicate")
        self.data : List[Tuple[AstVar, AstQvarLs]] = data


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
    def __init__(self, pos : PosInfo, opt : AstVar, qvar_ls : AstQvarLs, prog : AstProgSeq):
        super().__init__(pos, "while")
        self.opt : AstVar = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog : AstProgSeq = prog

class AstIf(Ast):
    def __init__(self, pos : PosInfo, opt : AstVar, qvar_ls : AstQvarLs, prog1 : AstProgSeq, prog0 : AstProgSeq):
        super().__init__(pos, "if")
        self.opt : AstVar = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog1 : AstProgSeq = prog1
        self.prog0 : AstProgSeq = prog0

class AstUnitary(Ast):
    def __init__(self, pos : PosInfo, opt : AstVar, qvar_ls : AstQvarLs):
        super().__init__(pos, "unitary transformation")
        self.opt : AstVar = opt
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
    def __init__(self, pos : PosInfo, subprog : AstVar, qvar_ls : AstQvarLs):
        super().__init__(pos, "subprogram")
        self.subprog : AstVar = subprog
        self.qvar_ls : AstQvarLs = qvar_ls
