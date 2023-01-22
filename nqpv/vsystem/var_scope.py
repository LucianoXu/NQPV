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

from nqpv.vsystem.log_system import RuntimeErrorWithLog
from nqpv.vsystem.settings import Settings


class VVar:
    '''
    the varibles for the verification system
    '''

    @property
    def str_type(self) -> str :
        '''
        This property returns the type of this variable.
        ( A more concise hint different from the complete string data. )
        '''
        return "Verification Varibale"

    def __init__(self):
        self.name : str = "temp_var"

class VarPath:
    '''
    the class of paths to indicate a variable in the system
    '''
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


class VarScope (VVar):


    cur_scope : VarScope | None = None


    @staticmethod
    def get_cur_scope() -> VarScope:
        if VarScope.cur_scope is None:
            raise Exception()
        return VarScope.cur_scope

    @staticmethod
    def cur_settings() -> Settings:
        return VarScope.get_cur_scope().settings

    def __init__(self, label : str, parent_scope : VarScope | None):
        if not (isinstance(parent_scope, VarScope) or parent_scope is None) or not isinstance(label, str):
            raise ValueError()

        super().__init__()

        # auto naming number for every scope
        self.auto_naming_no : int = 0

        self._parent_scope : VarScope | None = parent_scope

        # the label of this environment
        self._label : str = label

        # dictionary to store all the variables in this environment
        # note: the dictionary is the local id, and the dict value (var) has a polished id
        self._vars : Dict[str, VVar] = {}
        self.settings = Settings()

    @property
    def str_type(self) -> str:
        return "scope"
        
    @property
    def parent_scope(self) -> VarScope | None:
        return self._parent_scope

    @property
    def scope_prefix(self) -> str:
        if self._parent_scope is None:
            return self._label + "."
        else:
            return self._parent_scope.scope_prefix + self._label + "."

    def __str__(self) -> str:
        r = "<scope " + self.scope_prefix + ">\n"
        r += str(self.settings) + "\n"
        for key in self._vars:
            r += "\t" + key + "\t\t" + self._vars[key].str_type + "\n"
        return r

    def _search(self, label : str) -> VVar | None:
        if label in self._vars:
            return self._vars[label]
        elif self._parent_scope is not None:
            return self._parent_scope._search(label)
        # may found global itself (the global scope does not appear in the cases above)
        elif self._label == label:
            return self
        else:
            return None


    def __getitem__(self, key : VarPath | str) -> VVar:
        '''
        referring to a variable in an inductive way
        '''
        if isinstance(key, str):
            return self[VarPath((key,))]

        find_res = self._search(key.current)
        if find_res is not None:
            next_key = key.postfix()
            if next_key is None:
                # if the search is over
                return find_res
            else:
                if isinstance(find_res, VarScope):
                    # search in the next scope
                    return find_res[next_key]
                
        raise RuntimeErrorWithLog("The variable '" + str(key) + "' is not defined.")


    def __setitem__(self, key : str, value : VVar) -> None:
        '''
        Note: value will be packaged into a Var term, with the polished name
        also used to assign new variables
        '''        
        if not isinstance(value, VVar):
            raise ValueError()
        self._vars[key] = value
        value.name = key
    
    def _search_value(self, value : VVar, id_used : set[str]) -> str | None :
        '''
        Search whether this value has been stored. If yes, return the key; else return None.
        ( The search is limited to those variables that can be refered to without path specification. )

        id_used : preserve the searched ids in child scopes to avoid the references to overlapped old variables.
        '''
        if not isinstance(value, VVar):
            raise ValueError()

        for key in self._vars:
            if key in id_used:
                continue
            id_used.add(key)
            if self[key] == value:
                return key
        
        if self.parent_scope is None:
            return None
        else:
            return self.parent_scope._search_value(value, id_used)

    def append(self, value : VVar) -> str:
        '''
        check whether the value already exists in this environment.
        If yes, return the variable.
        If not, create a new variable with an auto name and return the name used.
        '''


        if not isinstance(value, VVar):
            raise ValueError()

        # the setting controls whether to check the existence of identical operators
        if self.settings.IDENTICAL_VAR_CHECK:
            search_res = self._search_value(value, set())
        else:
            search_res = None

        if search_res is None:
            name = self.auto_name()
            self[name] = value
            return name
        else:
            return search_res


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
                if isinstance(find_res, VarScope):
                    # search in the next scope
                    return next_key in find_res 
        return False

    def inject(self, var_env : VarScope) -> None:
        '''
        inject the var environment to the current var environment
        (variables with the same name will be reassigned)
        '''
        for var in var_env._vars:
            self[var] = var_env[var]
    
    def auto_name(self, naming_prefix = "VAR") -> str:
        '''
        return an auto name, which does not appear in this environment
        '''
        r = naming_prefix + str(self.auto_naming_no)
        self.auto_naming_no += 1
        # ensure that the new name will not overlap any current variable
        while r in self._vars:
            r = naming_prefix + str(self.auto_naming_no)
            self.auto_naming_no += 1
        return r

    def report(self, msg : str) -> None:
        if not self.settings.SILENT:
            print(msg)