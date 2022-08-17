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
# tools.py
#
# define the tools used in this verifier
# ------------------------------------------------------------

ver_label = "0.1"

def lineno_added(txt):
    '''
    Add an line number in front of each line
    '''
    line_no = 1
    r = str(line_no) + '\t\t' + txt
    line_no += 1

    i = 0
    while i < len(r):
        if r[i] == '\n':
            r = r[:i+1] + str(line_no) + '\t\t' + r[i+1:]
            line_no += 1
        i += 1

    return r
