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
# qparser.py
#
# parser for nondeterministic quantum programs
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List

import ply.yacc as yacc

from nqpv.semantics.optEnv import OptEnv




from .qlexer import tokens, lexer

from ..semantics import qprogStd, qprogNondet, qProofOutline
from ..semantics.qVar import QvarLs
from ..semantics.qPre import QPredicate
from ..semantics.optQvarPair import OptQvarPair

from ..logsystem import LogSystem

# Error rule for syntax errors

channel = "syntax"


# program declaration section
def p_prog(p):
    'prog : predicate sequence predicate'
    p[0] = qProofOutline.QProofOutline(p[1], p[2], p[3])

def p_sequence_append(p):
    'sequence : sequence SEMICOLON sentence'
    p[0] = qprogStd.QProgSequence.append(p[1], p[3])

def p_sequence_form(p):
    'sequence : sentence'
    p[0] = qprogStd.QProgSequence(p[1])


def p_sentence(p):
    '''
    sentence : skip
        | abort
        | init
        | unitary
        | if
        | while
        | nondet_choice
    '''
    p[0] = p[1]

def p_nondet_choice(p):
    'nondet_choice : nondet_choice_pre sequence RBRAKET'
    p[0] = qprogNondet.QProgNondet.append(p[1], p[2])

def p_nondet_choice_append(p):
    '''
    nondet_choice_pre : nondet_choice_pre sequence NONDET_CHOICE
    '''
    p[0] = qprogNondet.QProgNondet.append(p[1], p[2])

def p_nondet_choice_start(p):
    '''
    nondet_choice_pre : LBRAKET sequence NONDET_CHOICE
    '''
    p[0] = qprogNondet.QProgNondet(qprogStd.Preconditions([]), p[2])
    

def p_if(p):
    'if : IF ID id_ls THEN sequence ELSE sequence END'
    opt = OptEnv.get_opt(p[2])
    p[0] = qprogStd.QProgIf(qprogStd.Preconditions([]), opt, p[3], p[5], p[7])

def p_while(p):
    'while : predicate_inv_pre WHILE ID id_ls DO sequence END'
    opt = OptEnv.get_opt(p[3])
    p[0] = qprogStd.QProgWhile(qprogStd.Preconditions([]), p[1], opt, p[4], p[6])


def p_skip(p):
    'skip : SKIP'
    p[0] = qprogStd.QProgSkip(qprogStd.Preconditions([]))

def p_abort(p):
    'abort : ABORT'
    p[0] = qprogStd.QProgAbort(qprogStd.Preconditions([]))

def p_unitary(p):
    '''unitary : id_ls MUL_EQ ID
                | ID MUL_EQ ID'''
    opt = OptEnv.get_opt(p[3])
    if isinstance(p[1], QvarLs):
        p[0] = qprogStd.QProgUnitary(qprogStd.Preconditions([]), opt, p[1])
    else:
        p[0] = qprogStd.QProgUnitary(qprogStd.Preconditions([]), opt, QvarLs(p[1]))


def p_init(p):
    '''init : id_ls ASSIGN ZERO
            | ID ASSIGN ZERO'''
    if isinstance(p[1], QvarLs):
        p[0] = qprogStd.QProgInit(qprogStd.Preconditions([]), p[1])
    else:
        p[0] = qprogStd.QProgInit(qprogStd.Preconditions([]), QvarLs(p[1]))

#define the invariants
def p_inv_end(p):
    'predicate_inv : predicate_inv_pre RBRACE'
    p[0] = p[1]

def p_inv_append(p):
    'predicate_inv_pre : predicate_inv_pre ID id_ls'
    opt = OptEnv.get_opt(p[2])
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate.append(p[1], optPair)


def p_inv_start(p):
    'predicate_inv_pre : LBRACE INV COLON ID id_ls'
    opt = OptEnv.get_opt(p[4])
    optPair = OptQvarPair(opt, p[5], "hermitian predicate")
    p[0] = QPredicate(optPair)


#define the quantum predicates
def p_predicate_end(p):
    'predicate : predicate_pre RBRACE'
    p[0] = p[1]

def p_predicate_append(p):
    'predicate_pre : predicate_pre ID id_ls'
    opt = OptEnv.get_opt(p[2])
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate.append(p[1], optPair)

def p_predicate_start(p):
    'predicate_pre : LBRACE ID id_ls'
    opt = OptEnv.get_opt(p[2])
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate(optPair)

# define the list of quantum variables
def p_id_ls_end(p):
    'id_ls : id_ls_pre RSBRAKET'
    p[0] = p[1]

def p_id_ls_append(p):
    'id_ls_pre : id_ls_pre ID'
    p[0] = QvarLs.append(p[1], p[2])

def p_id_ls_start(p):
    'id_ls_pre : LSBRAKET ID'
    p[0] = QvarLs(p[2])

def p_error(p):
    if p is not None:
        LogSystem.channels[channel].append("(line " + str(p.lineno) + ")\tSyntax error in input: '" + str(p.value) + "'.")


# Build the lexer
parser = yacc.yacc()