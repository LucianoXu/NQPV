
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
# venv.py
#
# description for environments
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from .var_env import Value, VarEnv
from .settings import Settings
from .syntax import ast
from .log_system import RuntimeErrorWithLog

class VEnv:
    def __init__(self, parent_env : VEnv | None):
        self.parent : VEnv | None = parent_env

        if parent_env is None:
            self.settings = Settings(None)
            self.var_env = VarEnv()
        else:
            self.settings = Settings(parent_env.settings)
            self.var_env = VarEnv()
    
    def get_var(self, key : str) -> Value:
        '''
        get the variable in the environment
        return None if not found
        '''
        # first search in the local environment
        if key in self.var_env.vars:
            return self.var_env[key]
        elif self.parent is not None:
            r = self.parent.get_var(key)
            return r
        else:
            raise RuntimeErrorWithLog("The variable '" + key + "' is not defined.")

    def refresh(self) -> None:
        self.settings.apply()

    def env_inject(self, env : VEnv) -> None:
        self.var_env.var_env_inject(env.var_env)
        self.settings = Settings(env.settings)

    def var_env_inject(self, var_env : VarEnv) -> None:
        self.var_env.var_env_inject(var_env)