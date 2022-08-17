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
# NQPV_ast.py
#
# definitions of the abstract syntax tree of NQPV
# ------------------------------------------------------------

def vls_to_code(vls):
    r = "[" + vls[0]
    for i in range(1, len(vls)):
        r += " " + vls[i]
    r += "]"
    return r

def predicate_to_code(predicate):
    r = predicate[0][0] + vls_to_code(predicate[0][1])
    for i in range(1, len(predicate)):
        r += " " + predicate[i][0] + vls_to_code(predicate[i][1])
    return r

def precondition_to_code(precond):
    '''
    precond: a list of identifiers(string), each represents a hermitian operator on the whole Hilbert space
    '''
    r = precond[0] + "[qvar]"
    for i in range(1, len(precond)):
        r += " " + precond[i] + "[qvar]"
    return r

class SyntaxStruct:
    # structure label
    label = ""
    # line number in the source code
    lineno = 0
    # precondition
    pre_cond = []

    def to_code(self, prefix):
        r = ""
        # if annoted, add the preconditions
        if self.pre_cond != []:
            r += "\n"+ prefix + "{ " + precondition_to_code(self.pre_cond) +" }\n"
        r += self.sentence_to_code(prefix)
        return r
    
    def sentence_to_code(self, prefix):
        return ""
        
class InitStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "INIT"
        self.lineno = p.slice[2].lineno
        if isinstance(p[1], list):
            self.vls = p[1]
        else:
            self.vls = [p[1]]

    def sentence_to_code(self, prefix):
        return prefix + vls_to_code(self.vls) + " := 0"

class UnitaryStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "UNITARY"
        self.lineno = p.slice[2].lineno
        self.unitary = p[3]
        if isinstance(p[1], list):
            self.vls = p[1]
        else:
            self.vls = [p[1]]

    def sentence_to_code(self, prefix):
        return prefix + vls_to_code(self.vls) + " *= " + self.unitary

class AbortStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "ABORT"
        self.lineno = p.slice[1].lineno

    def sentence_to_code(self, prefix):
        return prefix + "abort"


class SkipStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "SKIP"
        self.lineno = p.slice[1].lineno

    def sentence_to_code(self, prefix):
        return prefix + "skip"

class IfStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "IF"
        self.lineno = p.slice[1].lineno
        self.measure = p[2]
        self.measure_vls = p[3]
        self.S1 = p[5]  # then - subclause
        self.S0 = p[7]  # else - subclause
    
    def sentence_to_code(self, prefix):
        r = prefix + "if " + self.measure + vls_to_code(self.measure_vls) + " then\n"
        r += sequence_to_code(self.S1, prefix + '\t') + "\n"
        r += prefix + "else\n"
        r += sequence_to_code(self.S0, prefix + '\t') + "\n"
        r += prefix + "end"
        return r



class WhileStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "WHILE"
        self.lineno = p.slice[2].lineno
        self.inv = p[1]
        self.measure = p[3]
        self.measure_vls = p[4]
        self.S = p[6]
    
    def sentence_to_code(self, prefix):
        r = prefix + "{ inv: " + predicate_to_code(self.inv) + " }\n"
        r += prefix + "while " + self.measure + vls_to_code(self.measure_vls) + " do\n"
        r += sequence_to_code(self.S, prefix + '\t') + "\n"
        r += prefix + "end"
        return r

class NondetStruct(SyntaxStruct):
    def __init__(self, p):
        self.label = "NONDET_CHOICE"
        self.lineno = p.slice[3].lineno
        self.S0 = p[2]
        self.S1 = p[4]
    
    def sentence_to_code(self, prefix):
        r = prefix + "(\n"
        r += sequence_to_code(self.S0, prefix + '\t') + "\n"
        r += prefix + "#\n"
        r += sequence_to_code(self.S1, prefix + '\t') + "\n"
        r += prefix + ")"
        return r


def sequence_to_code(sequence: list, prefix):
    r = sequence[0].to_code(prefix)
    for i in range(1, len(sequence)):
        r += ";\n" + sequence[i].to_code(prefix)
    return r