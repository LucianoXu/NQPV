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
# id_env.py
#
# provide the environment of all identifiers
# ------------------------------------------------------------    

class IdEnv:
    id_opt : set[str] = set()
    id_qvar : set[str] = set()


    # the number postfix for automatic namings
    _auto_naming_num = 0

    # the prefix for automaitc namings
    _auto_naming_prefix = "OP"


    @staticmethod
    def opt_auto_name() -> str:
        '''
        Get a unique name of operators, which has not been used in the library.
        '''
        r = IdEnv._auto_naming_prefix + str(IdEnv._auto_naming_num)
        IdEnv._auto_naming_num += 1
        while r in IdEnv.id_opt or r in IdEnv.id_qvar:
            r = IdEnv._auto_naming_prefix + str(IdEnv._auto_naming_num)
            IdEnv._auto_naming_num += 1
        return r
    