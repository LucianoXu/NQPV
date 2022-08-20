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
# qprogStd.py
#
# Define the structure framework for quantum programs, and provide the standard program.
# Standard Quantum Programs: skip, abort, init, unitary, if, while, sequence composition
# ------------------------------------------------------------


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Sequence

from . import qLA
from .qLA import dagger, hermitian_contract, hermitian_init
from .optEnv import Operator, OptEnv
from .qVar import QvarLs
from .optQvarPair import OptQvarPair
from .qPre import QPredicate

from ..logsystem import LogSystem
from ..tools import code_add_prefix

# channel of this module
channel : str = "semantics"

class QProg:

    def __new__(cls, pres : Preconditions | None):
        # data refers to the input from the yacc parser
        instance = super().__new__(cls)

        if pres is None:
            LogSystem.channels[channel].append("The preconditions provided here is invalid.")
            return None

        instance.pres = pres
        instance.post = None
        return instance

    def __init__(self, pres : Preconditions | None):
        self.label : str
        self.pres : Preconditions
        # this post condition is not specified by the user, but is given while weakest precondition calculus
        self.post : QPredicate | None
    
    def __str__(self) -> str:
        raise Exception("__str__ not implemented yet")
    
    def _pre_post_decorate(self, code : str) -> str:
        r = ""
        t_pre = str(self.pres)
        if t_pre != "":
            r += t_pre + "\n"
        r += code
        return r
    
    def _wp(self) -> QPredicate | None:
        '''
        calculate and return the weakest precondition
        return None if the inner proof outline does not hold.
        '''
        raise Exception("not implemented")
        

    def proof_check(self) -> bool:
        '''
        check the whole proof outline of this subprogram
        '''
        # check whether the post condition has been set
        if self.post is None:
            raise Exception("The post condition has not been set yet.")

        # calculate the weakest precondition
        wp = self._wp()
        if wp is None:
            return False

        # insert the weakest preconditon to the end of the preconditions
        inserted = Preconditions.append(self.pres, wp)
        if inserted is None:
            raise Exception("unexpected situation")

        self.pres = inserted
        
        # check the partial orders
        if not self.pres.proof_check():
            return False
        return True

class Preconditions:
    '''
    The class to contain the sequence of preconditions
    '''
    def __new__(cls, data : Preconditions | QPredicate | None | List):
        if data is None:
            LogSystem.channels[channel].append("The predicate provided here is invalid.")
            return None

        # check for copy construction
        if isinstance(data, Preconditions):
            instance = super().__new__(cls)
            instance.pres = data.pres
            return instance
        
        # check for empty Preconditions
        if data == []:
            instance = super().__new__(cls)
            instance.pres = []
            return instance
        if isinstance(data, QPredicate):
            instance = super().__new__(cls)
            instance.pres = [data]
            return instance
        
        raise Exception("invalid input")

    def __init__(self, data : Preconditions | QPredicate | None | List):
        super().__init__()
        self.pres : List[QPredicate]

    @staticmethod
    def append(obj : Preconditions | None, pre : QPredicate | None) -> Preconditions | None:
        if obj is None:
            LogSystem.channels[channel].append("The preconditions provided here is invalid.")
            return None

        if pre is None:
            LogSystem.channels[channel].append("The predicate provided here is invalid.")
            return None
        
        r = Preconditions(obj)
        r.pres.append(pre)
        return r

    def __str__(self) -> str:
        if len(self.pres) == 0:
            return ""
        r = str(self.pres[0])
        for i in range(1, len(self.pres)):
            r += "\n" + str(self.pres[i])
        return r
    
    def proof_check(self) -> bool:
        for i in range(len(self.pres)-1, 0, -1):
            if not QPredicate.sqsubseteq(self.pres[i-1], self.pres[i]):
                return False
        return True

    def get_pre(self) -> QPredicate:
        return self.pres[0]


##################### Implementations

class QProgSkip(QProg):
    def __new__(cls, pres: Preconditions | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None

        instance.label = "SKIP"
        return instance
    
    def __str__(self) -> str:
        return self._pre_post_decorate("skip")
    
    def _wp(self) -> QPredicate | None:
        return self.post

class QProgAbort(QProg):
    def __new__(cls, pres: Preconditions | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None

        instance.label = "ABORT"
        return instance

    def __str__(self) -> str:
        return self._pre_post_decorate("abort")

    def _wp(self) -> QPredicate | None:
        m = qLA.eye_tensor(len(QvarLs.qvar))
        name = OptEnv.append(m)
        opt = OptEnv.lib[name]
        return QPredicate(OptQvarPair(opt, QvarLs("qvar")))


class QProgInit(QProg):
    def __new__(cls, pres: Preconditions | None, qvls: QvarLs | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None

        if qvls is None:
            LogSystem.channels[channel].append("The quantum variable list provided here is invalid.")
            return None

        instance.label = "INIT"

        instance.qvls = qvls  # type: ignore

        return instance

    def __init__(self, pres: Preconditions | None, qvls: QvarLs | None):
        super().__init__(pres)
        self.qvls : QvarLs

    def __str__(self) -> str:
        return self._pre_post_decorate(str(self.qvls) + " := 0")
    
    def _wp(self) -> QPredicate | None:
        if self.post is None:
            raise Exception("unexpected situation")

        r = QPredicate([])
        for pair in self.post.opts:
            m = hermitian_init(pair.qvls.data, pair.opt.data, self.qvls.data)
            name = OptEnv.append(m)
            r = QPredicate.append(
                r,
                OptQvarPair(
                    OptEnv.lib[name], pair.qvls
                )
            )

        return r

class QProgUnitary(QProg):
    def __new__(cls, pres: Preconditions | None, m : Operator | None, qvls: QvarLs | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None

        if m is None or qvls is None:
            LogSystem.channels[channel].append("The operator or quantum variable list provided here is invalid.")
            return None

        instance.label = "UNITARY"

        # check whether a valid unitary pair can be constructed
        uPair =  OptQvarPair(m, qvls, "unitary")
        if uPair is None:
            LogSystem.channels[channel].append("The construction of unitary transformation fails.")
            return None

        instance.uPair = uPair  # type: ignore

        return instance
    
    def __init__(self, pres: Preconditions | None, m : Operator | None, qvls: QvarLs | None):
        super().__init__(pres)
        self.uPair : OptQvarPair

    def __str__(self) -> str:
        return self._pre_post_decorate(str(self.uPair.qvls) + " *= " + str(self.uPair.opt))

    def _wp(self) -> QPredicate | None:
        if self.post is None:
            raise Exception("unexpected situation")

        r = QPredicate([])
        for pair in self.post.opts:
            m = hermitian_contract(pair.qvls.data, pair.opt.data,
                self.uPair.qvls.data, dagger(self.uPair.opt.data))
            name = OptEnv.append(m)
            r = QPredicate.append(
                r,
                OptQvarPair(
                    OptEnv.lib[name], pair.qvls
                )
            )
                    
        return r

    
class QProgIf(QProg):
    def __new__(cls, pres: Preconditions | None, m : Operator | None, qvls: QvarLs | None, S1: QProgSequence | None, S0: QProgSequence | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None
        instance.label = "IF"

        if m is None or qvls is None or S1 is None or S0 is None:
            LogSystem.channels[channel].append("The components for 'is' here are invalid.")
            return None

        # check whether a valid unitary pair can be constructed
        mPair =  OptQvarPair(m, qvls, "measurement")
        if mPair is None:
            LogSystem.channels[channel].append("The construction of measurement fails.")
            return None

        instance.mPair = mPair  # type: ignore
        instance.S1 = S1   # type: ignore
        instance.S0 = S0   # type: ignore

        return instance
    
    def __init__(self, pres: Preconditions | None, m : Operator | None, qvls: QvarLs | None, S1: QProgSequence | None, S0: QProgSequence | None):
        super().__init__(pres)
        self.mPair : OptQvarPair
        self.S1 : QProgSequence
        self.S0 : QProgSequence

    def __str__(self) -> str:
        r = "if " + str(self.mPair) + " then\n"
        r += code_add_prefix(str(self.S1), "\t") + "\n"
        r += "else\n"
        r += code_add_prefix(str(self.S0), "\t") + "\n"
        r += "end"
        return self._pre_post_decorate(r)
    
    def _wp(self) -> QPredicate | None:
        if self.post is None:
            raise Exception("unexpected situation")
        
        self.S1.set_post(self.post)
        if not self.S1.proof_check():
            return None
        self.S0.set_post(self.post)
        if not self.S0.proof_check():
            return None
        
        pre1 = self.S1.get_pre()
        pre0 = self.S0.get_pre()

        r = QPredicate([])

        for pair0 in pre0.opts:
            for pair1 in pre1.opts:
                m = hermitian_contract(pair0.qvls.data, pair0.opt.data, 
                        self.mPair.qvls.data, self.mPair.opt.data[0]) +\
                    hermitian_contract(pair1.qvls.data, pair1.opt.data, 
                        self.mPair.qvls.data, self.mPair.opt.data[1])
                name = OptEnv.append(m)
                r = QPredicate.append(
                    r,
                    OptQvarPair(
                        OptEnv.lib[name], pair0.qvls
                    )
                )

        return r


class QProgWhile(QProg):
    def __new__(cls, pres: Preconditions | None, inv: QPredicate | None, m : Operator | None, qvls: QvarLs | None, S: QProgSequence | None):
        instance = super().__new__(cls, pres)
        if instance is None:
            return None

        instance.label = "WHILE"

        if inv is None or m is None or qvls is None or S is None:
            LogSystem.channels[channel].append("The components for 'while' here are invalid.")
            return None

        instance.inv = data[1]  # type: ignore
        # check whether a valid unitary pair can be constructed
        mPair =  OptQvarPair(m, qvls, "measurement")
        if mPair is None:
            LogSystem.channels[channel].append("The construction of measurement fails.")
            return None

        instance.mPair = mPair  # type: ignore
        instance.S = S   # type: ignore

        return instance
    
    def __init__(self, pres: Preconditions | None, inv: QPredicate | None, m : Operator | None, qvls: QvarLs | None, S: QProgSequence | None):
        super().__init__(pres)
        self.inv : QPredicate
        self.mPair : OptQvarPair
        self.S : QProgSequence

    def __str__(self) -> str:
        r = "while " + str(self.mPair) + "do\n"
        r += code_add_prefix(str(self.S), "\t") + "\n"
        r += "end"
        return self._pre_post_decorate(r)

    def _wp(self) -> QPredicate | None:
        if self.post is None:
            raise Exception("unexpected situation")

        inv_ext = self.inv.full_extension()

        this_pre = QPredicate([])

        for pair_post in self.post.opts:
            for pair_inv in inv_ext.opts:
                m = hermitian_contract(pair_post.qvls.data, pair_post.opt.data, 
                        self.mPair.qvls.data, self.mPair.opt.data[0]) +\
                    hermitian_contract(pair_inv.qvls.data, pair_inv.opt.data, 
                        self.mPair.qvls.data, self.mPair.opt.data[1])
                name = OptEnv.append(m)
                this_pre = QPredicate.append(
                    this_pre,
                    OptQvarPair(
                        OptEnv.lib[name], pair_post.qvls
                    )
                )

        if this_pre is None:
            raise Exception("unexcepted situation")
        
        self.S.set_post(this_pre)

        if not self.S.proof_check():
            return None
        
        # check whether it is a valid invariant
        if not QPredicate.sqsubseteq(inv_ext, self.S.get_pre()):
            LogSystem.channels[channel].append("This is not a valid loop invariant.")
            return None
        
        return this_pre




class QProgSequence:
    def __new__(cls, data : QProgSequence | QProg | None) :
        super().__new__(cls)
        if data is None:
            LogSystem.channels[channel].append("The program provided here is invalid.")
            return None

        # check for copy construction
        if isinstance(data, QProgSequence):
            instance = super().__new__(cls)
            instance.progs = data.progs
            return instance

        instance = super().__new__(cls)
        instance.progs = [data]
        return instance

    def __init__(self, data : QProgSequence | QProg | None):
        super().__init__()
        self.progs : List[QProg]
    
    def set_post(self, post : QPredicate) -> None:
        self.progs[-1].post = post

    def get_pre(self) -> QPredicate:
        return self.progs[0].pres.get_pre()

    @staticmethod
    def append(obj : QProgSequence | None, prog : QProg | None) -> QProgSequence | None:
        if obj is None:
            LogSystem.channels[channel].append("The program sequence provided here is invalid.")
            return None

        if prog is None:
            LogSystem.channels[channel].append("The program provided here is invalid.")
            return None
        
        r = QProgSequence(obj)
        r.progs.append(prog)
        return r

    def __str__(self) -> str:
        r = str(self.progs[0])
        for i in range(1, len(self.progs)):
            r += ";\n" + str(self.progs[i])
        return r

    def proof_check(self) -> bool:
        if self.progs[-1].post is None:
            raise Exception("unexpected situation")
        
        for i in range(len(self.progs)-1, -1, -1):
            if not self.progs[i].proof_check():
                return False
            
            if i > 0:
                self.progs[i-1].post = self.progs[i].pres.get_pre()
        
        return True


    