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
# var_env.py
#
# provides the type system and variable environments
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from .log_system import RuntimeErrorWithLog
from .syntax import ast
from ..vsystem.content.opt import opt_kernel

vtype : set[str] = {
    "operator", 
    "opt_get", 
    "program", 
    "proof",
}

def v_check_unitary(value : Value) -> bool:
    if value.vtype.type != "operator":
        raise Exception("unexpected situation")
    return opt_kernel.check_unity(value.data)

def v_check_hermitian_predicate(value : Value) -> bool:
    if value.vtype.type != "operator":
        raise Exception("unexpected situation")
    return opt_kernel.check_hermitian_predicate(value.data)

def v_check_measurement(value : Value) -> bool:
    if value.vtype.type != "operator":
        raise Exception("unexpected situation")
    return opt_kernel.check_measure(value.data)

def v_get_qnum(value : Value) -> int:
    if value.vtype.type == "operator":
        return opt_kernel.get_opt_qnum(value.data)
    else:
        return value.vtype.data[0]

vproperty = {
    'unitary' : v_check_unitary,
    'hermitian predicate' : v_check_hermitian_predicate,
    'measurement' : v_check_measurement,
    'qnum' : v_get_qnum,
}

class VType:
    def __init__(self, type : str, data : Tuple):
        self.type : str = type
        self.data : Tuple = data
    
    def consistent(self, value : Value) -> bool:
        '''
        check whether the value is consistent with this type
        (mainly for assignment)
        '''
        if value.vtype.type != self.type:
            return False
        
        # if the program - proof correspondence should be check
        if value.vtype == "proof" and len(self.data) == 4:
            raise NotImplementedError()
        elif value.vtype == 'operator':
            return value.get_property("qnum") == self.data[0]
        else:
            return True

    def __str__(self) -> str:
        return self.type

    def clone(self) -> VType:
        r = VType(self.type, self.data)
        return r


class Value:

    def __init__(self, vtype: VType, data : Any):
        self.vtype : VType = vtype.clone()
        self.data : Any = data
        # property: used to store the verified properties
        self.properties : Dict[str, Any] = {}
    
    def assign_property(self, property : str, value : Any) -> None:
        '''
        assign a property without checking it
        it is mostly used in the internal calculation of weakest preconditions
        '''
        self.properties[property] = value

    def get_property(self, property : str) -> Any:
        '''
        check whether the value has the specified property
        '''
        if property in self.properties:
            return self.properties[property]
        if property not in vproperty:
            raise Exception("unexpected situation")

        r = vproperty[property](self)
        self.properties[property] = r
        return r

class VarEnv:

    auto_naming_no : int = 0
    auto_naming_prefix : str = "VAR"

    def __init__(self):
        # dictionary, from identity to the (type, data) pair
        self.vars : Dict[str, Value] = {}

    def __getitem__(self, key : str) -> Value:
        if key in self.vars:
            return self.vars[key]
        else:
            raise RuntimeErrorWithLog("The variable '" + key + "' is not defined.")

    def __setitem__(self, key : str, value : Any) -> None:
        self.vars[key] = value

    def var_env_inject(self, var_env : VarEnv) -> None:
        '''
        inject the var environment to the current var environment
        (variables with the same name will be reassigned)
        '''
        for var in var_env.vars:
            self[var] = var_env[var]
    
    def auto_name(self) -> str:
        '''
        return an auto name, which does not appear in this environment
        '''
        r = VarEnv.auto_naming_prefix + str(VarEnv.auto_naming_no)
        VarEnv.auto_naming_no += 1
        while r in self.vars:
            r = VarEnv.auto_naming_prefix + str(VarEnv.auto_naming_no)
            VarEnv.auto_naming_no += 1
        return r
    

    # TODO #41
    def assign_var(self, var : str | ast.AstOptGetLs, vtype : VType, data : Value) -> None:
        '''
        check whether the type is consistent, and conduct the assignment
        '''
        # type check
        if not vtype.consistent(data):
            raise RuntimeErrorWithLog("Left value type + '" + str(vtype) + 
                "' is inconsistent of rigth value type '" + str(data.vtype) +"'.")
        
        if vtype.type == 'opt_get':
            if isinstance(var, str):
                raise Exception("unexpected situation")
            
            raise NotImplementedError()
        
        else:
            if isinstance(var, ast.AstOptGetLs):
                raise Exception("unexpected situation")

            self.vars[var] = data
            self.vars[var].vtype = vtype.clone()
            

        