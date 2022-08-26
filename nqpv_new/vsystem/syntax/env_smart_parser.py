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
# env_smart_parser.py
#
# the smart parser which can detect EOF error
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List

from .ast import AstEnv
from .vparser import parser
from ..log_system import RuntimeErrorWithLog

def parse(code : str) -> AstEnv:
    try:
        r = parser.parse(code)
        if r is None:
            raise RuntimeErrorWithLog("unexpected end of code")
        return r
        
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Code parsering failed.")