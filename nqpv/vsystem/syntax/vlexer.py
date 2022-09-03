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
# vlexer.py
#
# tokenizer
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List

import ply.lex as lex

from nqpv.vsystem.log_system import LogSystem

from .pos_info import PosInfo


reserved = {
    # for vsystem
    'import': 'IMPORT',
    'def'   : 'DEF',
    'axiom' : 'AXIOM',
    'show'  : 'SHOW',

    # inner calculation methods
    'wp'    : 'WP',

    # keywords for type
    'operator'  : 'OPERATOR',
    'scope' : 'SCOPE',
    'program'   : 'PROGRAM',
    'proof' : 'PROOF',

    # for programs and verifications
    'skip'  : 'SKIP',
    'abort' : 'ABORT',
    'if'    : 'IF',
    'then'  : 'THEN',
    'else'  : 'ELSE',
    'while' : 'WHILE',
    'do'    : 'DO',
    'end'   : 'END',
    'inv'   : 'INV',
}

# List of token names.
tokens = [
    'ID',
    'INIT',
    'ASSIGN',
    'MUL_EQ',
    'ELLIPSIS'
 ] + list(reserved.values())

# Regular expression rules for simple tokens
t_INIT = r':=0'
t_ASSIGN = r':='
t_MUL_EQ = r'\*='
t_ELLIPSIS = r'\.\.\.'

literals = ['.', ',', ';', '#', ':', '[', ']', '(', ')', '{', '}']


# use // or /* */ to comment
def t_COMMENT(t):
    r'(/\*(.|\n)*?\*/)|(//.*)'
    for c in t.value:
        if c == '\n':
            t.lexer.lineno += 1

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


def t_error(t):
    LogSystem.channels["error"].append("Syntax Error. Illegal character '" + t.value[0] + "'." + str(PosInfo(t.lineno)))
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()