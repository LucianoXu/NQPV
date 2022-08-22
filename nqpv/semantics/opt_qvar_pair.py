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
# opt_qvar_pair.py
#
# The description for paired operators and quantum variables
# ------------------------------------------------------------



from __future__ import annotations
from typing import Any, List, Dict

import numpy as np

from .qLA import eye_tensor
from .opt_env import Operator, OptEnv
from .qVar import QvarLs

from ..syntaxes.pos_info import PosInfo
from ..logsystem import LogSystem

def check_unitary_qvls(opt : Operator, qvls : QvarLs) -> bool:

    # check the dimension informaion
    if (len(qvls) * 2 == len(opt.data.data.shape)):
        return True
    else:
        LogSystem.channels["error"].append("The dimensions of unitary '" + opt.data.id + 
        "' and quantum variable list " + str(qvls) + " do not match." + PosInfo.str(opt.pos))
        return False


def check_measure_qvls(opt : Operator, qvls : QvarLs) -> bool:

    # check the dimension information
    # + 1 is for the extra dimension of 0-result and 1-result
    if (len(qvls) * 2 + 1 == len(opt.data.data.shape)):
        return True
    else:
        LogSystem.channels["error"].append("The dimensions of measurement '" + opt.data.id + "' and quantum variable list "
         + str(qvls) + " do not match." + PosInfo.str(opt.pos))
        return False


def check_hermitian_predicate_qvls(opt : Operator, qvls : QvarLs) -> bool:
    # check the dimension informaion
    if (len(qvls) * 2 == len(opt.data.data.shape)):
        return True
    else:
        LogSystem.channels["error"].append("The dimensions of Hermitian operator '" + opt.data.id +
         "' and quantum variable list " + str(qvls) + " do not match." + PosInfo.str(opt.pos))
        return False

pair_check = {
    'unitary' : check_unitary_qvls,
    'hermitian predicate' : check_hermitian_predicate_qvls,
    'measurement' : check_measure_qvls,
}

class OptQvarPair:
    
    def __new__(cls, opt : Operator | None, qvls : QvarLs | None, type : str = "", origin : OptQvarPair | None = None):
        if type not in pair_check and type != "":
            raise Exception("Unknown type")

        # check whether the operator is valid
        if opt is None:
            LogSystem.channels["error"].append("The operator for the pair is invalid.")
            return None

        # check whether qvls is valid
        if qvls is None:
            LogSystem.channels["error"].append("The quantum variable list for the pair is invalid." + PosInfo.str(opt.pos))
            return None


        instance = super().__new__(cls)
        instance.opt = opt
        instance.qvls = qvls
        instance.pos = opt.pos
        instance.tags = {}
        instance.origin = origin

        # check the required property
        if type != "":
            if not instance.check_property(type):
                LogSystem.channels["error"].append(
                    "The operator variable pair '" + str(instance) + "' does not satisfy the required property '" + type + "'."
                    + PosInfo.str(opt.pos))
                return None

        return instance

    def __init__(self, opt : Operator | None, qvls : QvarLs | None, type : str = "", origin : OptQvarPair | None = None):
        '''
        <may return None if construction failes>
        '''
        self.opt : Operator
        self.qvls : QvarLs
        self.pos : PosInfo | None
        self.tags : Dict[str, bool]

        # this is the extension origin of this pair.
        self.origin : OptQvarPair | None
    
    def check_property(self, property : str) -> bool:
        '''
        check whether this pair has the specified property
        property : a string, must be one key of opt_property
        '''
        if property in self.tags:
            return self.tags[property]

        # check whether the opt operator has the claimed property
        if not self.opt.data.check_property(property):
            self.tags[property] = False
            return False

        # check whether the opt operator and the qvls variable list match with each other.
        if not pair_check[property](self.opt, self.qvls):
            self.tags[property] = False
            return False

        self.tags[property] = True
        return True
    
    def __str__(self) -> str:
        if self.origin is not None:
            return str(self.origin)
        else:
            return str(self.opt) + str(self.qvls)

    def __eq__(self, other) -> bool:
        return self.opt.data == other.opt.data and self.qvls == other.qvls