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

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm, type_qvarls, val_qvarls
from .opt_pair_term import OptPairTerm, type_opt_pair, val_opt_pair


fac = dts.TermFact()

type_prog_stt = fac.axiom("prog_statement", fac.sort_term(0))
#type_prog_stt_seq = fac.axiom("prog_statement_sequence", fac.sort_term(0))
type_prog = fac.axiom("prog", fac.sort_term(0))

class ProgSttTerm(dts.Term):
    def __init__(self, all_qvarls : QvarlsTerm):
        if not isinstance(all_qvarls, QvarlsTerm):
            raise ValueError()

        super().__init__(type_prog_stt, None)
        self._all_qvarls : QvarlsTerm = all_qvarls
    
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    def __str__(self) -> str:
        return "\n" + self.str_content("") + "\n"
    
    def str_content(self, prefix : str) -> str:
        raise NotImplementedError()

def val_prog_stt(term : dts.Term) -> ProgSttTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_prog_stt:
        raise ValueError()

    if isinstance(term, ProgSttTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProgSttTerm):
            raise Exception()
        return val
    else:
        raise Exception()

# note: by program equivalence, we allow the freedom of subprogram substitution
# for eval() the subprogram substitution is also considered.

class SkipTerm(ProgSttTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))
    
    def __eq__(self, other) -> bool:
        if isinstance(other, SkipTerm):
            return True
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def eval(self) -> dts.Term:
        return SkipTerm()
    
    def str_content(self, prefix: str) -> str:
        return prefix + "skip"

class AbortTerm(ProgSttTerm):
    def __init__(self):
        super().__init__(QvarlsTerm(()))

    def __eq__(self, other) -> bool:
        if isinstance(other, AbortTerm):
            return True
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def eval(self) -> dts.Term:
        return AbortTerm()
        
    def str_content(self, prefix: str) -> str:
        return prefix + "abort"


class InitTerm(ProgSttTerm):
    def __init__(self, qvarls : dts.Term):
        if not isinstance(qvarls, dts.Term):
            raise ValueError()
        if qvarls.type != type_qvarls:
            raise RuntimeErrorWithLog("The input '" + str(qvarls) + "' is not of type '" + str(type_qvarls) + "'.")
        
        qvarls_val = val_qvarls(qvarls)
        super().__init__(qvarls_val)
        self._qvarls : dts.Term = qvarls
    
    @property
    def qvarls_val(self) -> QvarlsTerm:
        return val_qvarls(self._qvarls)

    def __eq__(self, other) -> bool:
        if isinstance(other, InitTerm):
            return self._qvarls == other._qvarls
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def eval(self) -> dts.Term:
        return InitTerm(self._qvarls.eval())
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self._qvarls) + " *=0"


class UnitaryTerm(ProgSttTerm):
    def __init__(self, opt_pair : dts.Term):
        if not isinstance(opt_pair, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The input '" + str(opt_pair) + "' is not of type '" + str(type_opt_pair) + "'.")
        opt_pair_val = val_opt_pair(opt_pair)
        # check for unitary opt pair
        if not opt_pair_val.unitary_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not an unitary pair.")
        
        super().__init__(opt_pair_val.qvarls_val)
        self._opt_pair : dts.Term = opt_pair

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)

    def __eq__(self, other) -> bool:
        if isinstance(other, UnitaryTerm):
            return self._opt_pair == other._opt_pair
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def eval(self) -> dts.Term:
        return UnitaryTerm(self._opt_pair.eval())

    def str_content(self, prefix: str) -> str:
        return prefix + str(self.opt_pair_val.qvarls) + " *= " + str(self.opt_pair_val.opt)

class IfTerm(ProgSttTerm):
    def __init__(self, opt_pair : dts.Term, S1 : dts.Term, S0 : dts.Term):
        if not isinstance(opt_pair, dts.Term) or not isinstance(S1, dts.Term) or not isinstance(S0, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The input '" + str(opt_pair) + "' is not of type '" + str(type_opt_pair) + "'.")
        opt_par_val = val_opt_pair(opt_pair)
        # check for measurement opt pair
        if not opt_par_val.measurement_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not a measurement set pair.")
        
        if S1.type != type_prog_stt:
            raise RuntimeErrorWithLog("The S1 input term '" + str(S1) + "' is not a program statement sequence.")
        S1_val = val_prog_stt(S1)

        if S0.type != type_prog_stt:
            raise RuntimeErrorWithLog("The S0 input term '" + str(S0) + "' is not a program statement sequence.")
        S0_val = val_prog_stt(S0)

        all_qvarls = opt_par_val.qvarls_val
        all_qvarls = all_qvarls.join(S1_val.all_qvarls)
        all_qvarls = all_qvarls.join(S0_val.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : dts.Term = opt_pair
        self._S1 : dts.Term = S1
        self._S0 : dts.Term = S0

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)

    @property
    def S1_val(self) -> ProgSttTerm:
        return val_prog_stt(self._S1)

    @property
    def S0_val(self) -> ProgSttTerm:
        return val_prog_stt(self._S0)

    def __eq__(self, other) -> bool:
        if isinstance(other, IfTerm):
            return self._opt_pair == other._opt_pair \
                and self.S1_val == other.S1_val \
                and self.S0_val == other.S0_val
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
    
    def eval(self) -> dts.Term:
        return IfTerm(self._opt_pair.eval(), self._S1.eval(), self._S0.eval())

    def str_content(self, prefix: str) -> str:
        r = prefix + "if " + str(self._opt_pair) + " then\n"
        r += self.S1_val.str_content(prefix + "\t") + "\n"
        r += prefix + "else\n"
        r += self.S0_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class WhileTerm(ProgSttTerm):
    def __init__(self, opt_pair : dts.Term, S : dts.Term):
        if not isinstance(opt_pair, dts.Term) or not isinstance(S, dts.Term):
            raise ValueError()
        if opt_pair.type != type_opt_pair:
            raise RuntimeErrorWithLog("The input '" + str(opt_pair) + "' is not of type '" + str(type_opt_pair) + "'.")
        opt_pair_val = val_opt_pair(opt_pair)

        # check for measurement opt pair
        if not opt_pair_val.measurement_pair:
            raise RuntimeErrorWithLog("The operator variable pair '" + str(opt_pair) + "' is not a measurement set pair.")
        
        if S.type != type_prog_stt:
            raise RuntimeErrorWithLog("The S input term '" + str(S) + "' is not a program statement sequence.")
        S_val = val_prog_stt(S)
        
        all_qvarls = opt_pair_val.qvarls_val
        all_qvarls = all_qvarls.join(S_val.all_qvarls)
        super().__init__(all_qvarls)
        self._opt_pair : dts.Term = opt_pair
        self._S : dts.Term = S

    @property
    def opt_pair_val(self) -> OptPairTerm:
        return val_opt_pair(self._opt_pair)

    @property
    def S_val(self) -> ProgSttTerm:
        return val_prog_stt(self._S)

    def __eq__(self, other) -> bool:
        if isinstance(other, WhileTerm):
            return self._opt_pair == other._opt_pair and self.S_val == other.S_val
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
    
    def eval(self) -> dts.Term:
        return WhileTerm(self._opt_pair.eval(), self._S.eval())

    def str_content(self, prefix: str) -> str:
        r = prefix + "while " + str(self._opt_pair) + " do\n"
        r += self.S_val.str_content(prefix + "\t") + "\n"
        r += prefix + "end"
        return r

class NondetTerm(ProgSttTerm):
    def __init__(self, subprog_ls : Tuple[dts.Term,...]):
        if not isinstance(subprog_ls, tuple):
            raise ValueError()

        all_qvarls = QvarlsTerm(())
        # example each item in the tuple
        for item in subprog_ls:
            if not isinstance(item, dts.Term):
                raise ValueError()
            if item.type != type_prog_stt:
                raise RuntimeErrorWithLog("The input term '" + str(item) + "' is not a program statement sequence.")
            item_val = val_prog_stt(item)
            all_qvarls = all_qvarls.join(item_val.all_qvarls)
        
        super().__init__(all_qvarls)
        self._subprog_ls : Tuple[dts.Term,...] = subprog_ls

    def get_stt(self, i : int) -> ProgSttTerm:
        return val_prog_stt(self._subprog_ls[i])

    def __len__(self) -> int:
        return len(self._subprog_ls)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, NondetTerm):
            if len(self) != len(other):
                return False
            # compare each element
            for i in range(len(self)):
                if self.get_stt(i) != other.get_stt(i):
                    return False
            return True
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
    
    def eval(self) -> dts.Term:
        new_ls = []
        for item in self._subprog_ls:
            new_ls.append(item.eval())
        return NondetTerm(tuple(new_ls))
    
    def str_content(self, prefix: str) -> str:
        r = prefix + "(\n"
        r += self.get_stt(0).str_content(prefix + "\t") + "\n"
        for i in range(1, len(self._subprog_ls)):
            r += prefix + "#\n"
            r += self.get_stt(i).str_content(prefix + "\t") + "\n"
        r += prefix + ")"
        return r

class SubProgTerm(ProgSttTerm):
    def __init__(self, subprog : dts.Term, arg_ls : dts.Term):
        # note: we need subprog to be a dts.Var
        if not isinstance(subprog, dts.Var) or not isinstance(arg_ls, dts.Term):
            raise ValueError()
        if subprog.type != type_prog:
            raise RuntimeErrorWithLog("The term '" + str(subprog) + "' is not a program.")
        if arg_ls.type != type_qvarls:
            raise RuntimeErrorWithLog("The term '" + str(arg_ls) + "' is not a quantum variable list.")
        
        # check whether the arguments match the program signature
        subprog_val = val_prog(subprog)
        arg_ls_val = val_qvarls(arg_ls)
        if len(subprog_val.arg_ls_val) != len(arg_ls_val):
            raise RuntimeErrorWithLog("The argument list '" + str(arg_ls) + "' does not match the program '" + str(subprog) + "'.")
        
        super().__init__(arg_ls_val)
        self._subprog : dts.Var = subprog
        self._arg_ls : dts.Term = arg_ls

    @property
    def subprog_val(self) -> ProgDefinedTerm:
        return val_prog_defined(self._subprog)
    
    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)

    def __eq__(self, other) -> bool:
        if isinstance(other, SubProgTerm):
            return self._subprog == other._subprog and self._arg_ls == other._arg_ls
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False

    def eval(self) -> dts.Term:
        # construct the substitution correspondence
        return SubProgTerm(self._subprog.eval(), self._arg_ls.eval())
    
    def str_content(self, prefix: str) -> str:
        return prefix + str(self._subprog) + " " + str(self._arg_ls)


class ProgSttSeqTerm(ProgSttTerm):
    '''
    A sequence of program statements. This is the structure for programs we are dealing with.
    '''
    def __init__(self, stt_ls : Tuple[dts.Term,...]):
        if not isinstance(stt_ls, tuple):
            raise ValueError()
        if len(stt_ls) == 0:
            raise ValueError()

        all_qvarls = QvarlsTerm(())
        for item in stt_ls:
            if not isinstance(item, dts.Term):
                raise ValueError()
            if item.type != type_prog_stt:
                raise RuntimeErrorWithLog("The term '" + str(item) + "' is not a program statement.")
            item_val = val_prog_stt(item)
            all_qvarls = all_qvarls.join(item_val.all_qvarls)

        super().__init__(all_qvarls)
        # flatten the sequential composition
        flattened = ()
        for item in stt_ls:
            if isinstance(item, ProgSttSeqTerm):
                flattened = flattened + item._stt_ls
            else:
                flattened = flattened + (item,)
        self._stt_ls : Tuple[dts.Term,...] = flattened
        
    def __len__(self) -> int:
        return len(self._stt_ls)

    def get_stt(self, i : int) -> ProgSttTerm:
        return val_prog_stt(self._stt_ls[i])

    def __eq__(self, other) -> bool:
        if isinstance(other, ProgSttSeqTerm):
            if len(self) != len(other):
                return False
            # compare each statement
            for i in range(len(self)):
                if self.get_stt(i) != other.get_stt(i):
                    return False
            return True
        elif isinstance(other, dts.Var):
            raise NotImplemented
        else:
            return False
        
    def eval(self) -> dts.Term:
        new_ls = []
        for i in range(len(self)):
            new_ls.append(self.get_stt(i).eval())
        return ProgSttSeqTerm(tuple(new_ls))

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


def val_prog_stt_seq(term : dts.Term) -> ProgSttSeqTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_prog_stt:
        raise ValueError()

    if isinstance(term, ProgSttSeqTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProgSttSeqTerm):
            raise Exception()
        return val
    else:
        raise Exception()

class ProgTerm(dts.Term):
    def __init__(self, arg_ls : dts.Term):
        if arg_ls.type != type_qvarls:
            raise RuntimeErrorWithLog("The term '" + str(arg_ls) + "' is not a quantum variable list.")
        arg_ls_val = val_qvarls(arg_ls)
        
        super().__init__(type_prog, None)
        self._arg_ls : dts.Term = arg_ls
        self._all_qvarls : QvarlsTerm = arg_ls_val
    
    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)

    def __eq__(self, other) -> bool:
        raise NotImplementedError()

    def __str__(self) -> str:
        raise NotImplementedError()

def val_prog(term : dts.Term) -> ProgTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_prog:
        raise ValueError()

    if isinstance(term, ProgTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProgTerm):
            raise Exception()
        return val
    else:
        raise Exception()

class ProgDefiningTerm(ProgTerm):
    '''
    The program being defined, may be used in recursive invocations.
    '''
    def __str__(self) -> str:
        return "\n(Program Being Defined) " + str(self.arg_ls_val) + "\n"

class ProgDefinedTerm(ProgTerm):
    '''
    A program term, with the specification of parameter variable list.
    This is the program signature, so there is no methods "eval" or "arg_apply"
    '''
    def __init__(self, prog_seq : dts.Term, arg_ls : dts.Term):
        if not isinstance(prog_seq, dts.Term) or not isinstance(arg_ls, dts.Term):
            raise ValueError()
        if prog_seq.type != type_prog_stt:
            raise RuntimeErrorWithLog("The term '" + str(prog_seq) + "' is not a program statement sequence.")
        arg_ls_val = val_qvarls(arg_ls)
        
        super().__init__(arg_ls)
        self._prog_seq : dts.Term = prog_seq
        self._arg_ls : dts.Term = arg_ls
        self._all_qvarls : QvarlsTerm = arg_ls_val.join(self.prog_seq_val.all_qvarls)
    
    @property
    def prog_seq_val(self) -> ProgSttSeqTerm:
        return val_prog_stt_seq(self._prog_seq)

    @property
    def all_qvarls(self) -> QvarlsTerm:
        return self._all_qvarls

    @property
    def arg_ls_val(self) -> QvarlsTerm:
        return val_qvarls(self._arg_ls)

    def __eq__(self, other) -> bool:
        if isinstance(other, ProgDefinedTerm):
            return self.prog_seq_val == other.prog_seq_val and self._arg_ls == other._arg_ls
        else:
            raise NotImplemented

    def __str__(self) -> str:
        return "\nprogram " + str(self._arg_ls) + " : \n" + self.prog_seq_val.str_content("\t") + "\n"

def val_prog_defined(term : dts.Term) -> ProgDefinedTerm:
    if not isinstance(term, dts.Term):
        raise ValueError()
    if term.type != type_prog:
        raise ValueError()

    if isinstance(term, ProgDefinedTerm):
        return term
    elif isinstance(term, dts.Var):
        val = term.val
        if not isinstance(val, ProgDefinedTerm):
            raise Exception()
        return val
    else:
        raise Exception()
