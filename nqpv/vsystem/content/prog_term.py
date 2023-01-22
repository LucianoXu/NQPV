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
# prog_term.py
#
# define the program terms
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm
from .opt_pair_term import OptPairTerm, MeaPairTerm
from ..var_scope import VVar, VarScope

class ProgSttTerm(VVar):
    def __init__(self, all_qvarls : QvarlsTerm):
        if not isinstance(all_qvarls, QvarlsTerm):
            raise ValueError()

        self._all_qvarls : QvarlsTerm = all_qvarls

    @property
    def str_type(self) -> str:
        return "program statement"
    
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"
    
    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

    def __eq__(self, other) -> bool:
        raise NotImplemented


class SkipTerm(ProgSttTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))
    
    def str_content(self, prefix: str) -> str:
        return prefix + "skip"

class AbortTerm(ProgSttTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))

    def str_content(self, prefix: str) -> str:
        return prefix + "abort"


class InitTerm(ProgSttTerm):
    def __init__(self, qvarls : QvarlsTerm):
        if not isinstance(qvarls, QvarlsTerm):
            raise ValueError()
        
        super().__init__(qvarls)
        self._qvarls : QvarlsTerm = qvarls
    
    @property
    def qvarls_val(self) -> QvarlsTerm:
        return self._qvarls

    def str_content(self, prefix: str) -> str:
        return prefix + str(self._qvarls) + " *=0"


class UnitaryTerm(ProgSttTerm):
    def __init__(self, opt_pair : OptPairTerm):
        if not isinstance(opt_pair, OptPairTerm):
            raise ValueError()
        # check for unitary opt pair
        if not opt_pair.unitary_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not an unitary pair.")
            
        super().__init__(opt_pair.qvarls)
        self._opt_pair : OptPairTerm = opt_pair

    @property
    def opt_pair(self) -> OptPairTerm:
        return self._opt_pair


    def str_content(self, prefix: str) -> str:
        return prefix + str(self.opt_pair.qvarls) + " *= " + self.opt_pair.opt.name

class IfTerm(ProgSttTerm):
    def __init__(self, opt_pair : MeaPairTerm, S1 : ProgSttTerm, S0 : ProgSttTerm):
        if not isinstance(opt_pair, MeaPairTerm) or not isinstance(S1, ProgSttTerm) or not isinstance(S0, ProgSttTerm):
            raise ValueError()
        
        all_qvarls = opt_pair.qvarls
        all_qvarls = all_qvarls.join(S1.all_qvarls)
        all_qvarls = all_qvarls.join(S0.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : MeaPairTerm = opt_pair
        self._S1 : ProgSttTerm = S1
        self._S0 : ProgSttTerm = S0

    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair

    @property
    def S1(self) -> ProgSttTerm:
        return self._S1

    @property
    def S0(self) -> ProgSttTerm:
        return self._S0

    def str_content(self, prefix: str) -> str:
        r = prefix + "if " + str(self._opt_pair) + " then\n"
        r += self.S1.str_content(prefix + "\t") + "\n"
        r += prefix + "else\n"
        r += self.S0.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class WhileTerm(ProgSttTerm):
    def __init__(self, opt_pair : MeaPairTerm, S : ProgSttTerm):
        if not isinstance(opt_pair, MeaPairTerm) or not isinstance(S, ProgSttTerm):
            raise ValueError()

        all_qvarls = opt_pair.qvarls
        all_qvarls = all_qvarls.join(S.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : MeaPairTerm = opt_pair
        self._S : ProgSttTerm = S

    @property
    def opt_pair(self) -> MeaPairTerm:
        return self._opt_pair

    @property
    def S(self) -> ProgSttTerm:
        return self._S

    def str_content(self, prefix: str) -> str:
        r = prefix + "while " + str(self._opt_pair) + " do\n"
        r += self.S.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class NondetTerm(ProgSttTerm):
    def __init__(self, subprog_ls : Tuple[ProgSttTerm,...]):
        if not isinstance(subprog_ls, tuple):
            raise ValueError()

        all_qvarls = QvarlsTerm(())
        # example each item in the tuple
        for item in subprog_ls:
            if not isinstance(item, ProgSttTerm):
                raise ValueError()
            all_qvarls = all_qvarls.join(item.all_qvarls)
        
        super().__init__(all_qvarls)
        self._subprog_ls : Tuple[ProgSttTerm,...] = subprog_ls

    def get_stt(self, i : int) -> ProgSttTerm:
        return self._subprog_ls[i]

    def __len__(self) -> int:
        return len(self._subprog_ls)

    
    def str_content(self, prefix: str) -> str:
        r = prefix + "(\n"
        r += self.get_stt(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._subprog_ls)):
            r += prefix + "#\n"
            r += self.get_stt(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r


class ProgSttSeqTerm(ProgSttTerm):
    '''
    A sequence of program statements. This is the structure for programs we are dealing with.
    '''
    def __init__(self, stt_ls : Tuple[ProgSttTerm,...]):
        if not isinstance(stt_ls, tuple):
            raise ValueError()
        if len(stt_ls) == 0:
            raise ValueError()

        all_qvarls = QvarlsTerm(())
        for item in stt_ls:
            if not isinstance(item, ProgSttTerm):
                raise ValueError()
            all_qvarls = all_qvarls.join(item.all_qvarls)

        super().__init__(all_qvarls)
        # flatten the sequential composition
        flattened = ()
        for item in stt_ls:
            if isinstance(item, ProgSttSeqTerm):
                flattened = flattened + item._stt_ls
            else:
                flattened = flattened + (item,)
        self._stt_ls : Tuple[ProgSttTerm,...] = flattened
        
    def __len__(self) -> int:
        return len(self._stt_ls)

    def get_stt(self, i : int) -> ProgSttTerm:
        return self._stt_ls[i]

    def str_content(self, prefix: str) -> str:
        if len(self._stt_ls) == 1:
            return self.get_stt(0).str_content(prefix)
        elif len(self._stt_ls) > 1:
            r = ""
            for i in range(len(self._stt_ls)-1):
                r += self.get_stt(i).str_content(prefix) + ";\n"
            r += self.get_stt(len(self._stt_ls)-1).str_content(prefix)
            return r
        else:
            raise Exception()


class ProgDefinedTerm(VVar):
    '''
    A program term, with the specification of parameter variable list.
    This is the program signature, so there is no methods "eval" or "arg_apply"
    '''
    def __init__(self, prog_seq : ProgSttTerm, arg_ls : QvarlsTerm):
        '''
        '''
        if not isinstance(prog_seq, ProgSttTerm) or not isinstance(arg_ls, QvarlsTerm):
            raise ValueError()

        self._prog_seq : ProgSttTerm = prog_seq
        self._arg_ls : QvarlsTerm = arg_ls
        self._all_qvarls : QvarlsTerm = arg_ls.join(self.prog_seq.all_qvarls)

    @property
    def str_type(self) -> str:
        return "defined_program"
    
    @property
    def prog_seq(self) -> ProgSttTerm:
        return self._prog_seq

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    @property
    def arg_ls(self) -> QvarlsTerm:
        return self._arg_ls

    def __str__(self) -> str:
        return "\nprogram " + str(self._arg_ls) + " : \n" + self.prog_seq.str_content("\t") + "\n"