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
    def __init__(self, pos : PosInfo):
        pass
        self.pos : PosInfo = pos
        #self.label : str
        #self.legal : bool = True

class AstEnv(Ast):
    def __init__(self, pos : PosInfo, cmd_ls : List[Ast]):
        super().__init__(pos)
        self.cmd_ls : List[Ast] = cmd_ls

class AstDefinition(Ast):
    def __init__(self, pos : PosInfo, var : AstID | AstOptGetLs, vtype : AstType, expr : AstExpression):
        super().__init__(pos)
        self.var : AstID | AstOptGetLs = var
        self.vtype : AstType = vtype
        self.expr : AstExpression = expr


class AstExample(Ast):
    def __init__(self, pos : PosInfo, expr : AstExpression):
        super().__init__(pos)
        self.expr : AstExpression = expr

class AstAxiom(Ast):
    def __init__(self, pos : PosInfo, subproof : AstID, pre : AstPredicate,
        subprog : AstID, qvar_ls : AstQvarLs, post : AstPredicate):
        super().__init__(pos)
        self.subproof : AstID = subproof
        self.pre : AstPredicate = pre
        self.subprog : AstID = subprog
        self.qvar_ls : AstQvarLs = qvar_ls
        self.post : AstPredicate = post


class AstType(Ast):
    def __init__(self, pos : PosInfo, type : str, data : Tuple):
        super().__init__(pos)
        self.type : str = type
        self.data : Tuple = data

class AstExpression(Ast):
    def __init__(self, pos : PosInfo, elabel : str, data : AstProg | AstProof):
        super().__init__(pos)
        self.elabel : str = elabel
        self.data : AstProg | AstProof = data
        self.env : AstEnv | None = None

class AstOptGetLs(Ast):
    def __init__(self, pos: PosInfo, data : List[AstID]):
        super().__init__(pos)
        self.data : List[AstID] = data

class AstQvarLs(Ast):
    def __init__(self, pos : PosInfo, data : List[AstID]):
        super().__init__(pos)
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

    def no_repeat(self) -> bool:
        '''
        check whether there is no repeat in this qvar list
        '''
        appeared : set[str] = set()
        for id in self.data:
            if id.id not in appeared:
                appeared.add(id.id)
            else:
                return False
        return True

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for id in self.data:
            if id.id not in r:
                r = r + (id.id,)
        return r



class AstID(Ast):
    def __init__(self, pos : PosInfo, id : str):
        super().__init__(pos)
        self.id : str = id
    
    def __str__(self) -> str:
        return self.id

class AstIfProof(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, proof1 : AstProof, proof0 : AstProof):
        super().__init__(pos)
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof1 : AstProof = proof1
        self.proof0 : AstProof = proof0

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        r = self.proof1.qvar_seq(r)
        r = self.proof0.qvar_seq(r)
        return r

class AstInv(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstID, AstQvarLs]]):
        super().__init__(pos)
        self.data : List[Tuple[AstID, AstQvarLs]] =  data

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for pair in self.data:
            r = pair[1].qvar_seq(r)
        return r 


class AstSubproof(Ast):
    def __init__(self, pos : PosInfo, subproof : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos)
        self.subproof : AstID = subproof
        self.qvar_ls : AstQvarLs = qvar_ls

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        return r


class AstWhileProof(Ast):
    def __init__(self, pos : PosInfo, inv : AstInv, opt : AstID, qvar_ls : AstQvarLs, proof : AstProof):
        super().__init__(pos)
        self.inv : AstInv = inv
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.proof : AstProof = proof

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.inv.qvar_seq(r)
        r = self.qvar_ls.qvar_seq(r)
        r = self.proof.qvar_seq(r)
        return r

class AstNondetProof(Ast):
    def __init__(self, pos : PosInfo, data : List[AstProof]):
        super().__init__(pos)
        self.data : List[AstProof] = data

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for proof in self.data:
            r = prog.qvar_seq(r)  # type: ignore
        return r

class AstPredicate(Ast):
    def __init__(self, pos : PosInfo, data : List[Tuple[AstID, AstQvarLs]]):
        super().__init__(pos)
        self.data : List[Tuple[AstID, AstQvarLs]] = data

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for pair in self.data:
            r = pair[1].qvar_seq(r)
        return r


class AstProof(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos)
        self.data : List[Ast] = data

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for p in self.data:
            r = p.qvar_seq(r)  # type: ignore
        return r


class AstProg(Ast):
    def __init__(self, pos : PosInfo, data : List[Ast]):
        super().__init__(pos)
        self.data : List[Ast] = data
    
    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for prog in self.data:
            r = prog.qvar_seq(r)  # type: ignore
        return r


class AstNondet(Ast):
    def __init__(self, pos : PosInfo, data : List[AstProg]):
        super().__init__(pos)
        self.data : List[AstProg] = data

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        for prog in self.data:
            r = prog.qvar_seq(r)  # type: ignore
        return r

class AstWhile(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, prog : AstProg):
        super().__init__(pos)
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog : AstProg = prog

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        r = self.prog.qvar_seq(r)
        return r

class AstIf(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs, prog1 : AstProg, prog0 : AstProg):
        super().__init__(pos)
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls
        self.prog1 : AstProg = prog1
        self.prog0 : AstProg = prog0

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        r = self.prog1.qvar_seq(r)
        r = self.prog0.qvar_seq(r)
        return r

class AstUnitary(Ast):
    def __init__(self, pos : PosInfo, opt : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos)
        self.opt : AstID = opt
        self.qvar_ls : AstQvarLs = qvar_ls

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        return r

class AstInit(Ast):
    def __init__(self, pos : PosInfo, qvar_ls : AstQvarLs):
        super().__init__(pos)
        self.qvar_ls : AstQvarLs = qvar_ls
    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        return r

class AstAbort(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        return seq_set

class AstSkip(Ast):
    def __init__(self, pos : PosInfo):
        super().__init__(pos)

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        return seq_set


class AstSubprog(Ast):
    def __init__(self, pos : PosInfo, subprog : AstID, qvar_ls : AstQvarLs):
        super().__init__(pos)
        self.subprog : AstID = subprog
        self.qvar_ls : AstQvarLs = qvar_ls

    def qvar_seq(self, seq_set : Tuple[str,...] = ()) -> Tuple[str,...]:
        '''
        return the qvar (ordered) list appear in this program
        seq_set : the list that is already considered
        '''
        r = seq_set
        r = self.qvar_ls.qvar_seq(r)
        return r

