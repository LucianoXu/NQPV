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
# NQPV_lexer.py
#
# tokenizer for nondeterministic quantum programs
# ------------------------------------------------------------
import ply.lex as lex

reserved = {
    'qvar' : 'QVAR',
    'skip': 'SKIP',
    'abort' : 'ABORT',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do' : 'DO',
    'end' : 'END',
    'inv' : 'INV'
}

# List of token names.
tokens = [
    'ID',
    'ASSIGN',
    'ZERO',
    'MUL_EQ',
    'SEMICOLON',
    'NONDET_CHOICE',
    'COLON',
    'LSBRAKET',
    'RSBRAKET',
    'LBRAKET',
    'RBRAKET',
    'LBRACE',
    'RBRACE'
 ] + list(reserved.values())

# Regular expression rules for simple tokens
t_ASSIGN = r':='
t_ZERO = r'0'
t_MUL_EQ = r'\*='
t_SEMICOLON = r';'
t_NONDET_CHOICE = r'[#]'
t_COLON = r':'
t_LSBRAKET = r'\['
t_RSBRAKET = r'\]'
t_LBRAKET = r'\('
t_RBRAKET = r'\)'
t_LBRACE = r'{'
t_RBRACE = r'}'

# use // to comment a line
def t_COMMENT(t):
    r'//.*'
    pass

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'ID')    # Check for reserved words
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule

from .tools import err

error_info = ""
silent = False

def t_error(t):
    global error_info, silent
    cur_info = "(line " + str(t.lineno) + ")\tSyntax Error. Illegal character '" + t.value[0] + "'. \n"
    error_info += err(cur_info, silent)
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

# test the lexer
if __name__ == '__main__':

    data = '''
    '''

    lexer.input(data)

    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)