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
# logsystem.py
#
# Provide the error/information log and report system.
# This system shall be used by all modules in this project to store informations.
# Other modules will transform information through different channels in LogSystem.channel_dict.
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict
from io import TextIOWrapper

class LogSystem:

    channels : Dict[str, LogSystem] = {}

    def __init__(self, name : str, end : str = "\n"):
        '''
        create a new channel

        name: channel name
        '''

        # the list to save all kinds of logs (not only string)
        self.logs : List[Any] = []
        # how to end an item when output
        if not isinstance(end, str):
            raise Exception("invalid input")
        self.end : str = end

        LogSystem.channels[name] = self

        

    @property
    def empty(self) -> bool:
        return len(self.logs) == 0

    def append(self, data : Any) -> None:
        self.logs.append(data)

    def get_front(self, pfile : None | TextIOWrapper = None, cmd_print : bool = False, drop : bool = True) -> str:
        if drop:
            result : str =  str(self.logs.pop(0)) + self.end
        else:
            result : str = self.logs[0]
        
        if pfile is not None:
            pfile.write(result)

        if cmd_print:
            print(result, end = "")

        return result

    def get_back(self, pfile : None | TextIOWrapper = None, cmd_print : bool = False, drop : bool = True) -> str:
        if drop:
            result : str =  str(self.logs.pop(len(self.logs)-1)) + self.end
        else:
            result : str = self.logs[len(self.logs)-1]
        
        if pfile is not None:
            pfile.write(result)

        if cmd_print:
            print(result, end = "")

        return result

    
    def summary(self, pfile : None | TextIOWrapper = None, cmd_print : bool = False, drop : bool = True) -> str:
        '''
        Conclude and return all the informations. Clean self.logs afterwards.
        pfile: the file pointer to write this summary
        '''

        result : str = ""
        for info in self.logs:
            result += str(info) + self.end

        if drop:
            self.logs.clear()
        
        if pfile is not None:
            pfile.write(result)

        if cmd_print:
            print(result, end = "")

        return result

    def single(self, data : Any, pfile : None | TextIOWrapper = None, cmd_print : bool = False) -> str:
        '''
        push in the information, polish it, pop out and write to file/print out immediately.
        '''
        self.append(data)
        return self.get_back(pfile, cmd_print, True)




    

