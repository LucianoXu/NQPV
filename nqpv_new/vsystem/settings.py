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
# settings.py
#
# provides the settings of an environment
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict

class Settings:
    def __init__(self, parent : Settings | None):
        super().__init__()
        if parent is None:
            # use the default settings
            self.EPS : float = 1e-7
            self.SDP_precision : float = 1e-9
        else:
            self.EPS = parent.EPS
            self.SDP_precision = parent.SDP_precision
        
    def apply(self) -> None:
        '''
        apply the settings
        '''
        pass