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
# qvarls_term.py
#
# defining the quantum variable list terms
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Tuple, Dict

from nqpv import dts

from nqpv.vsystem.log_system import RuntimeErrorWithLog

fac = dts.TermFact()

type_qvarls = fac.axiom("qvarls", fac.sort_term(0))

class QvarlsTerm(dts.Term):
    def __init__(self, qvarls : Tuple[str,...]):
        #check the terms
        if not isinstance(qvarls, tuple):
            raise ValueError()

        #repeat check
        appeared = set()
        for item in qvarls:
            if not isinstance(item, str):
                raise ValueError()

            if item in appeared:
                raise RuntimeErrorWithLog("The variable '" + item + "' repeats in the list '" + str(qvarls) + "'.")
            else:
                appeared.add(item)

        super().__init__(type_qvarls, None)
        self._qvarls : Tuple[str,...] = qvarls
    
    @property
    def vls(self) -> Tuple[str,...]:
        return self._qvarls

    @property
    def qnum(self) -> int:
        return len(self._qvarls)
    
    def __len__(self) -> int:
        return len(self._qvarls)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, QvarlsTerm):
            return self._qvarls == other._qvarls
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def __str__(self) -> str:
        if len(self) == 0:
            return "[]"
        r = "[" + self._qvarls[0]
        for i in range(1, len(self)):
            r += " " + self._qvarls[i]
        r += "]"
        return r


    def get_sub_correspond(self, arg_ls : QvarlsTerm) -> Dict[str, str]:
        '''
        get the substitution correspondence (arg_ls as arguments) for qvar_substitution
        '''
        if not isinstance(arg_ls, QvarlsTerm):
            raise ValueError()
        if self.qnum != arg_ls.qnum:
            raise ValueError()

        cor : Dict[str, str] = {}
        for i in range(self.qnum):
            cor[self._qvarls[i]] = arg_ls._qvarls[i]
        return cor
        
    
    def qvar_substitute(self, correspondence : Dict[str, str]) -> QvarlsTerm:
        if not isinstance(correspondence, dict):
            raise ValueError()
        new_qvarls = []
        for qvar in self._qvarls:
            if qvar not in correspondence:
                raise ValueError()
            new_qvar = correspondence[qvar]
            if not isinstance(new_qvar, str):
                raise ValueError()
            new_qvarls.append(new_qvar)
        
        return QvarlsTerm(tuple(new_qvarls))

    def cover(self, other : QvarlsTerm) -> bool:
        '''
        return whether this qvar list 'covers' the other qvar list
        '''
        for qvar in other._qvarls:
            if qvar not in self._qvarls:
                return False
        return True

    
    def join(self, other : QvarlsTerm) -> QvarlsTerm:
        '''
        return the new qvarls term, which joins the new variables in 'other'
        at the end of 'self' list
        '''
        new_qvarls = list(self._qvarls)
        for qvar in other._qvarls:
            if qvar not in new_qvarls:
                new_qvarls.append(qvar)
        return QvarlsTerm(tuple(new_qvarls))

def val_qvarls(term : dts.Term) -> QvarlsTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_qvarls:
        raise ValueError()
        
    val = term.eval()
    if not isinstance(val, QvarlsTerm):
        raise Exception()
    return val

