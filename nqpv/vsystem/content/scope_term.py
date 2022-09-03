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
# scope_term.py
#
# defines the (inductive) naming scope terms and their methods
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

fac = dts.TermFact()

scope_type = fac.axiom("env", fac.sort_term(0))

class ScopeTerm(dts.Term):

    auto_naming_no : int = 0
    auto_naming_prefix : str = "VAR"

    def __init__(self, label : str, parent_scope : dts.Term | None):
        if not (isinstance(parent_scope, dts.Term) or parent_scope is None) or not isinstance(label, str):
            raise ValueError()
        

        super().__init__(scope_type, None)

        if parent_scope is not None:
            if parent_scope.type != scope_type:
                raise ValueError()
            parent_scope = parent_scope.eval()
            if not isinstance(parent_scope, ScopeTerm):
                raise Exception("unexpecetd situation")
        self._parent_scope : ScopeTerm | None = parent_scope

        # the label of this environment
        self._label : str = label
        # dictionary to store all the variables in this environment
        # note: the dictionary is the local id, and the dict value (var) has a polished id
        self._vars : Dict[str, dts.Var] = {}

    @property
    def parent_scope(self) -> ScopeTerm | None:
        return self._parent_scope

    @property
    def scope_prefix(self) -> str:
        if self._parent_scope is None:
            return self._label + "."
        else:
            return self._parent_scope.scope_prefix + self._label + "."

    def __str__(self) -> str:
        return "<scope " + self.scope_prefix + ">"

    def __getitem__(self, key : str) -> dts.Var:
        if key in self._vars:
            return self._vars[key]
        elif self._parent_scope is not None:
            return self._parent_scope[key]
        else:
            raise RuntimeErrorWithLog("The variable '" + key + "' is not defined.")

    def __setitem__(self, key : str, value : dts.Term) -> None:
        '''
        Note: value will be packaged into a Var term, with the polished name
        also used to assign new variables
        '''
        if not isinstance(value, dts.Term):
            raise ValueError()
        
        if key in self._vars:
            raise RuntimeErrorWithLog("The variable '" + key + "' already exists in the scope '" + str(self.scope_prefix) + "'.")

        self._vars[key] = dts.Var(self.scope_prefix + key, value.type, value, key)

    def append(self, value : dts.Term) -> str:
        '''
        append the value into the scope, with an auto name
        return the auto name used
        '''
        name = self.auto_name()
        self[name] = value
        return name


    def remove_var(self, key : str) -> None:
        '''
        find the variable in this scope and remove it
        '''
        if key not in self._vars:
            raise RuntimeErrorWithLog("The variable '" + key + "' dost not exist in this scope, and can not be deleted.")
        self._vars.pop(key)

    def __contains__(self, key : str) -> bool:
        if key in self._vars:
            return True
        elif self._parent_scope is not None:
            return key in self._parent_scope
        else:
            return False

    def inject(self, var_env : ScopeTerm) -> None:
        '''
        inject the var environment to the current var environment
        (variables with the same name will be reassigned)
        '''
        for var in var_env._vars:
            self[var] = var_env[var].val
    
    def auto_name(self) -> str:
        '''
        return an auto name, which does not appear in this environment
        '''
        r = ScopeTerm.auto_naming_prefix + str(ScopeTerm.auto_naming_no)
        ScopeTerm.auto_naming_no += 1
        # ensure that the new name will not overlap any old name
        while r in self:
            r = ScopeTerm.auto_naming_prefix + str(ScopeTerm.auto_naming_no)
            ScopeTerm.auto_naming_no += 1
        return r
        
    def move_up(self, key : str) -> None:
        '''
        move the variable key to the higher scope
        variable of the same id will not be overwritten
        '''
        if self._parent_scope is None:
            raise RuntimeErrorWithLog("The scope '" + str(self) + "' does not have a parent scope.")
        
        if key not in self._vars:
            raise RuntimeErrorWithLog("The variable with id '" + key + "' does not exist in this particular scope.")
        
        self._parent_scope[key] = self._vars[key].val
        self._vars.pop(key)
        