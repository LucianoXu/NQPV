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
# define the settings of this verifier
# ------------------------------------------------------------

from . import semantics

class Settings:
    version : str = "0.1"
    
    @staticmethod
    def EPS() -> float:
        return semantics.qLA.Precision.EPS()  # type: ignore

    @staticmethod
    def set_EPS(eps : float) -> None:
        semantics.qLA.Precision.set_EPS(eps)  # type: ignore
    