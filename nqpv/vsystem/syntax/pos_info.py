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
# pos_info.py
#
# the class to preserve position information
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List

class PosInfo:
    def __init__(self, data : int | PosInfo | None = None):
        '''
        lineno = None means there is no position information
        '''
        # check for copy construction
        if isinstance(data, PosInfo):
            self.lineno = data.lineno
        elif isinstance(data, int) or data is None:
            self.lineno : int | None = data
        else:
            raise Exception()

    @staticmethod
    def str(pos : PosInfo | None) -> str:
        if pos is not None:
            return str(pos)
        else:
            return ""

    def __str__(self) -> str:
        if self.lineno is None:
            return ""
        else:
            return " (line " + str(self.lineno) + ") "