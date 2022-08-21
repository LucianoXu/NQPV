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
# opt_env.py
#
# provide the environment of operators
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict

import numpy as np

from . import qLA
from .qLA import np_eps_equal, Precision
from ..id_env import IdEnv

from ..syntaxes.pos_info import PosInfo
from ..logsystem import LogSystem

# description of all operator properties in consideration
opt_property = {
    'unitary' : qLA.check_unity,
    'hermitian predicate' : qLA.check_hermitian_predicate,
    'measurement' : qLA.check_measure,
}    

class OperatorData:
    '''
    The class for a particular operator, including the property tags (unitary, Hermitian and so on)
    '''
    def __init__(self, m : np.ndarray, id : str = ""):
        # the data
        self.data : np.ndarray = m
        # assign the id
        self.id = id
        # the tags of this operator
        self.tags : Dict[str, bool] = {}

    def check_property(self, property : str) -> bool:
        '''
        check whether this operator has the specified property
        property : a string, must be one key of opt_property
        '''
        if property in self.tags:
            return self.tags[property]
        
        if property not in opt_property:
            raise Exception("Unknown Property.")
        
        result = opt_property[property](self.data)
        self.tags[property] = result
        return result
    
    def __str__(self) -> str:
        return self.id
    
    @property
    def full_str(self) -> str:
        '''
        The information of operator name, checked property and data.
        '''
        r = self.id
        for tag in self.tags:
            if self.tags[tag]:
                r += " <" + tag + ">"
        r += "\n"
        r += str(self.data)
        return r

class Operator:
    '''
    operator data with position information
    '''
    def __init__(self, opt : OperatorData, pos : PosInfo | None):
        self.data : OperatorData = opt
        self.pos : PosInfo | None = pos
    
    def __str__(self) -> str:
        return str(self.data)

class OptEnv:

    # the library of all Operators
    lib : Dict[str, OperatorData] = {}

    @staticmethod
    def append(m : np.ndarray, proposed_name : str = "", repeat_detect = True) -> str:
        '''
        append the operator m to the operator environment, and return the actual name of the appended operator
        Actual name may be different from the proposed name due to coincidence of operators.

        proposed_name : if "", then a default name will be used.
        repeat detect : whether to detect repeat operators when appending new operators
        '''
        if repeat_detect:
            for id in OptEnv.lib:
                if np_eps_equal(OptEnv.lib[id].data, m, Precision.EPS()):
                    return id
        
        # decide the name
        if proposed_name == "":
            # auto
            name = IdEnv.opt_auto_name()

        else:
            # proposed
            if proposed_name in OptEnv.lib or proposed_name in IdEnv.id_qvar:
                raise Exception("The id has been used in the operator environment.")

            name = proposed_name

        # append in the library
        OptEnv.lib[name] = OperatorData(m, name)
        IdEnv.id_opt_add(name)
        return name
    
    @staticmethod
    def use_opt(id : str, pos : PosInfo | None) -> Operator | None:
        if id not in OptEnv.lib:
            LogSystem.channels["error"].append("The operator '" + id + "' does not exist in the operator environment." + PosInfo.str(pos))
            return None
        # register this use
        IdEnv.id_opt_used_add(id)

        return Operator(OptEnv.lib[id], pos)
