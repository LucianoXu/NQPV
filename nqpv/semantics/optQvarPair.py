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
# optQvarPair.py
#
# The description for paired operators and quantum variables
# ------------------------------------------------------------



from __future__ import annotations
from typing import Any, List, Dict

import numpy as np

from .qLA import eye_tensor
from .optEnv import Operator, OptEnv
from .qVar import QvarLs

from ..logsystem import LogSystem

# channel of this module
channel : str = "semantics"

def check_unitary_qvls(opt : Operator, qvls : QvarLs) -> bool:

    # check the dimension informaion
    if (len(qvls) * 2 == len(opt.data.shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of unitary '" + opt.id + "' and qvars " + str(qvls) + " do not match.")
        return False


def check_measure_qvls(opt : Operator, qvls : QvarLs) -> bool:

    # check the dimension information
    # + 1 is for the extra dimension of 0-result and 1-result
    if (len(qvls) * 2 + 1 == len(opt.data.shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of measurement '" + opt.id + "' and qvars " + str(qvls) + " do not match.")
        return False


def check_hermitian_predicate_qvls(opt : Operator, qvls : QvarLs) -> bool:
    # check the dimension informaion
    if (len(qvls) * 2 == len(opt.data.shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of hermitian '" + opt.id + "' and qvars " + str(qvls) + " do not match.")
        return False

PairCheck = {
    'unitary' : check_unitary_qvls,
    'hermitian predicate' : check_hermitian_predicate_qvls,
    'measurement' : check_measure_qvls,
}

class OptQvarPair:
    
    def __new__(cls, opt : Operator | None, qvls : QvarLs | None, type : str = ""):
        if type not in PairCheck and type != "":
            raise Exception("Unknown type")

        # check whether the operator is valid
        if opt is None:
            LogSystem.channels[channel].append("The operator here is invalid.")
            return None

        # check whether qvls is valid
        if qvls is None:
            LogSystem.channels[channel].append("The quantum variables here is invalid.")
            return None


        instance = super().__new__(cls)
        instance.opt = opt
        instance.qvls = qvls
        instance.tags = {}

        # check the required property
        if type != "":
            if not instance.check_property(type):
                LogSystem.channels[channel].append(
                    "The operator variable pair '" + str(instance) + "' does not satisfy the property '" + type + "'."
                    )
                return None

        return instance

    def __init__(self, opt : Operator | None, qvls : QvarLs | None, type : str = ""):
        '''
        <may return None if construction failes>
        '''
        self.opt : Operator
        self.qvls : QvarLs
        self.tags : Dict[str, bool]
    
    def check_property(self, property : str) -> bool:
        '''
        check whether this pair has the specified property
        property : a string, must be one key of OptProperty
        '''
        if property in self.tags:
            return self.tags[property]

        # check whether the opt operator has the claimed property
        if not self.opt.check_property(property):
            self.tags[property] = False
            return False

        # check whether the opt operator and the qvls variable list match with each other.
        if not PairCheck[property](self.opt, self.qvls):
            self.tags[property] = False
            return False

        self.tags[property] = True
        return True
    
    def __str__(self) -> str:
        return str(self.opt) + str(self.qvls)