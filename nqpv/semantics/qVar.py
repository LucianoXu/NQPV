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
# qvar.py
#
# Description of quantum variable list
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from ..id_env import IdEnv

from ..syntaxes.pos_info import PosInfo

from ..logsystem import LogSystem

class QvarLs:
    # list of all variables in consideration
    qvar : List[str] = []

    def __new__(cls, input_data : str | List[str] | QvarLs | None, pos : PosInfo | None):
        if input_data is None:
            LogSystem.channels["error"].append("The input for quantum variable list is invalid." + PosInfo.str(pos))
            return None

        # if is the whole qvar list or a first element
        elif isinstance(input_data, str):
            if input_data == "qvar":
                instance = super().__new__(cls)
                instance._data = "qvar"
                instance.pos = pos
                return instance
            else:
                instance = super().__new__(cls)
                instance._data = ()
                instance.pos = pos
                new_instance = QvarLs.append(instance, input_data, pos)
                return new_instance

        # if is a copy construction
        elif isinstance(input_data, QvarLs):
            if pos is not None:
                raise Exception("unexpected situation")
            instance = super().__new__(cls)
            instance._data = input_data._data
            instance.pos = input_data.pos
            return instance

        # if it is an empty list (initialization)
        elif input_data == []:
            instance = super().__new__(cls)
            instance._data = ()
            instance.pos = pos
            return instance
        else:
            raise Exception("unexpected situation")


    def __init__(self, input_data : str | QvarLs | None, pos : PosInfo | None):
        '''
        <may return None if construction failes>
        '''
        self._data : str | Tuple[str,...]
        self.pos : PosInfo | None
    
    @staticmethod
    def append(obj : QvarLs | None, append_id : str , pos : PosInfo | None) -> QvarLs | None:
        '''
        return a new QvarLs, in which the variable list is appended
        '''
        if obj is None:
            LogSystem.channels["error"].append("The quantum variable list is invalid." + PosInfo.str(pos))
            return None

        if obj._data == "qvar":
            LogSystem.channels["error"].append("Quantum variable list of 'qvar' cannot be appended." + PosInfo.str(pos))
            return None

        if append_id in obj._data:
            LogSystem.channels["error"].append("The same variable '" + append_id + 
                "' already appears in this list '" + str(obj._data) + "." + PosInfo.str(pos))
            return None
        
        if append_id not in QvarLs.qvar:
            # check whether this id has been used by operators
            if append_id in IdEnv.id_opt:
                LogSystem.channels["error"].append("The identifier '" + append_id + "' has been used by the operators." + PosInfo.str(pos))
                return None
            # append in the env
            QvarLs.qvar.append(append_id)
            IdEnv.id_qvar.add(append_id)

        if isinstance(obj._data, tuple):
            result = QvarLs(obj, None)
            result._data = obj._data + (append_id,)
            return result
        else:
            raise Exception("unexpected situation")


    @property
    def data(self) -> Tuple[str,...]:
        # check whether it refers to the whole qvar list
        if isinstance(self._data, str):
            return tuple(QvarLs.qvar)
        else:
            return self._data
    
    def __len__(self) -> int:
        return len(self.data)

    def __str__(self) -> str:

        if self._data == "qvar":
            return "[qvar]"
        else:
            r = "[" + self._data[0]
            for i in range(1, len(self._data)):
                r += " " + self._data[i]
            r += "]"
            return r

    def __eq__(self, other):
        if len(self.data) != len(other.data):
            return False
        for i in range(len(self.data)):
            if self.data[i] != other.data[i]:
                return False
        return True
    
    def isfull(self) -> bool:
        '''
        examine whether this qvar is the same with qvar
        '''
        if len(self.data) != len(QvarLs.qvar):
            return False
        for i in range(len(self.data)):
            if self.data[i] != QvarLs.qvar[i]:
                return False
        return True

    

    
