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

type_scope = fac.axiom("scope", fac.sort_term(0))

class VarPath:
    def __init__(self, path : Tuple[str,...], pointer : int = 0):
        if not isinstance(path, tuple):
            raise ValueError()
        for item in path:
            if not isinstance(item, str):
                raise ValueError()
        if len(path) == 0:
            raise ValueError()

        self.path : Tuple[str,...] = path
        self._pointer = pointer
    
    @property
    def current(self) -> str:
        return self.path[self._pointer]

    def postfix(self) -> VarPath | None:
        '''
        return the postfix VarPath (pointer starting from the next string)
        '''
        if self._pointer < len(self.path) - 1:
            return VarPath(self.path, self._pointer + 1)
        else:
            return None
    
    def __str__(self) -> str:
        r = str(self.path[0])
        for i in range(1, len(self.path)):
            r += "." + str(self.path[i])
        return r


class ScopeTerm(dts.Term):

    auto_naming_no : int = 0

    def __init__(self, label : str, parent_scope : dts.Term | None):
        if not (isinstance(parent_scope, dts.Term) or parent_scope is None) or not isinstance(label, str):
            raise ValueError()
        

        super().__init__(type_scope, None)

        if parent_scope is not None:
            if parent_scope.type != type_scope:
                raise ValueError()
            parent_scope = parent_scope.eval()
            if not isinstance(parent_scope, ScopeTerm):
                raise Exception()
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
        r = "<scope " + self.scope_prefix + ">\n"
        for key in self._vars:
            r += "\t" + key + "\t\t" + str(self._vars[key].type) + "\n"
        return r

    def _search(self, label : str) -> dts.Var | None:
        if label in self._vars:
            return self._vars[label]
        elif self._parent_scope is not None:
            return self._parent_scope._search(label)
        else:
            return None


    def __getitem__(self, key : VarPath | str) -> dts.Var:
        if isinstance(key, str):
            return self[VarPath((key,))]

        find_res = self._search(key.current)
        if find_res is not None:
            next_key = key.postfix()
            if next_key is None:
                # if the search is over
                return find_res
            else:
                if find_res.type == type_scope:
                    # search in the next scope
                    next_scope_val = find_res.val
                    if not isinstance(next_scope_val, ScopeTerm):
                        raise Exception()
                    return next_scope_val[next_key]
                
        raise RuntimeErrorWithLog("The variable '" + str(key) + "' is not defined.")


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

    def __contains__(self, key : VarPath | str) -> bool:
        if isinstance(key, str):
            return VarPath((key,)) in self

        find_res = self._search(key.current)
        if find_res is not None:
            next_key = key.postfix()
            if next_key is None:
                # if the search is over
                return True
            else:
                if find_res.type == type_scope:
                    # search in the next scope
                    next_scope_val = find_res.val
                    if not isinstance(next_scope_val, ScopeTerm):
                        raise Exception()
                    return next_key in next_scope_val 
        return False

    def inject(self, var_env : ScopeTerm) -> None:
        '''
        inject the var environment to the current var environment
        (variables with the same name will be reassigned)
        '''
        for var in var_env._vars:
            self[var] = var_env[var].val
    
    def auto_name(self, naming_prefix = "VAR") -> str:
        '''
        return an auto name, which does not appear in this environment
        '''
        r = naming_prefix + str(ScopeTerm.auto_naming_no)
        ScopeTerm.auto_naming_no += 1
        # ensure that the new name will not overlap any old name
        while r in self:
            r = naming_prefix + str(ScopeTerm.auto_naming_no)
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
        