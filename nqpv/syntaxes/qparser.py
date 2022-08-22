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


from .qlexer import tokens, lexer

from .pos_info import PosInfo

from ..semantics import qprog_nondet, qprog_proof_outline, qprog_std
from ..semantics.qVar import QvarLs
from ..semantics.qPre import QPredicate
from ..semantics.opt_env import OptEnv
from ..semantics.opt_qvar_pair import OptQvarPair

from ..logsystem import LogSystem


# program declaration section
def p_prog(p):
    'prog : predicate sequence predicate'
    p[0] = qprog_proof_outline.QProofOutline(p[1], p[2], p[3])

def p_sequence_append(p):
    'sequence : sequence SEMICOLON sentence'
    p[0] = qprog_std.QProgSequence.append(p[1], p[3])

def p_sequence_form(p):
    'sequence : sentence'
    p[0] = qprog_std.QProgSequence(p[1])


def p_sentence(p):
    '''
    sentence : skip
        | abort
        | init
        | unitary
        | if
        | while
        | nondet_choice
        | predicate sentence
    '''
    if isinstance(p[1], QPredicate):
        p[0] = p[2]
        p[0].pres = qprog_nondet.Preconditions.insert_front(p[0].pres, p[1])
    else:
        p[0] = p[1]

def p_nondet_choice(p):
    'nondet_choice : nondet_choice_pre sequence RBRAKET'
    p[0] = qprog_nondet.QProgNondet.append(p[1], p[2])

def p_nondet_choice_append(p):
    '''
    nondet_choice_pre : nondet_choice_pre sequence NONDET_CHOICE
    '''
    p[0] = qprog_nondet.QProgNondet.append(p[1], p[2])

def p_nondet_choice_start(p):
    '''
    nondet_choice_pre : LBRAKET sequence NONDET_CHOICE
    '''
    p[0] = qprog_nondet.QProgNondet(qprog_std.Preconditions([]), p[2])
    

def p_if(p):
    'if : IF ID id_ls THEN sequence ELSE sequence END'
    opt = OptEnv.use_opt(p[2], PosInfo(p.slice[2].lineno))
    p[0] = qprog_std.QProgIf(qprog_std.Preconditions([]), opt, p[3], p[5], p[7], PosInfo(p.slice[1].lineno))

def p_while(p):
    'while : predicate_inv WHILE ID id_ls DO sequence END'
    opt = OptEnv.use_opt(p[3], PosInfo(p.slice[3].lineno))
    p[0] = qprog_std.QProgWhile(qprog_std.Preconditions([]), p[1], opt, p[4], p[6], PosInfo(p.slice[2].lineno))


def p_skip(p):
    'skip : SKIP'
    p[0] = qprog_std.QProgSkip(qprog_std.Preconditions([]), PosInfo(p.slice[1].lineno))

def p_abort(p):
    'abort : ABORT'
    p[0] = qprog_std.QProgAbort(qprog_std.Preconditions([]), PosInfo(p.slice[1].lineno))

def p_unitary(p):
    '''unitary : id_ls MUL_EQ ID
                | ID MUL_EQ ID'''
    opt = OptEnv.use_opt(p[3], PosInfo(p.slice[3].lineno))
    if isinstance(p[1], QvarLs):
        p[0] = qprog_std.QProgUnitary(qprog_std.Preconditions([]), opt, p[1], PosInfo(p.slice[2].lineno))
    else:
        p[0] = qprog_std.QProgUnitary(qprog_std.Preconditions([]), opt, QvarLs(p[1], PosInfo(p.slice[1].lineno)), PosInfo(p.slice[2].lineno))


def p_init(p):
    '''init : id_ls ASSIGN ZERO
            | ID ASSIGN ZERO'''
    if isinstance(p[1], QvarLs):
        p[0] = qprog_std.QProgInit(qprog_std.Preconditions([]), p[1], PosInfo(p.slice[2].lineno))
    else:
        p[0] = qprog_std.QProgInit(qprog_std.Preconditions([]), QvarLs(p[1], PosInfo(p.slice[1].lineno)), PosInfo(p.slice[2].lineno))

#define the invariants
def p_inv_end(p):
    'predicate_inv : predicate_inv_pre RBRACE'
    p[0] = p[1]

def p_inv_append(p):
    'predicate_inv_pre : predicate_inv_pre ID id_ls'
    opt = OptEnv.use_opt(p[2], PosInfo(p.slice[2].lineno))
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate.append(p[1], optPair)


def p_inv_start(p):
    'predicate_inv_pre : LBRACE INV COLON ID id_ls'
    opt = OptEnv.use_opt(p[4], PosInfo(p.slice[4].lineno))
    optPair = OptQvarPair(opt, p[5], "hermitian predicate")
    p[0] = QPredicate(optPair)


#define the quantum predicates
def p_predicate_end(p):
    'predicate : predicate_pre RBRACE'
    p[0] = p[1]

def p_predicate_append(p):
    'predicate_pre : predicate_pre ID id_ls'
    opt = OptEnv.use_opt(p[2], PosInfo(p.slice[2].lineno))
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate.append(p[1], optPair)

def p_predicate_start(p):
    'predicate_pre : LBRACE ID id_ls'
    opt = OptEnv.use_opt(p[2], PosInfo(p.slice[2].lineno))
    optPair = OptQvarPair(opt, p[3], "hermitian predicate")
    p[0] = QPredicate(optPair)

# define the list of quantum variables
def p_id_ls_end(p):
    'id_ls : id_ls_pre RSBRAKET'
    p[0] = p[1]

def p_id_ls_append(p):
    'id_ls_pre : id_ls_pre ID'
    p[0] = QvarLs.append(p[1], p[2], PosInfo(p.slice[2].lineno))

def p_id_ls_start(p):
    'id_ls_pre : LSBRAKET ID'
    p[0] = QvarLs(p[2], PosInfo(p.slice[2].lineno))

def p_error(p):
    if p is not None:
        LogSystem.channels["error"].append("Syntax error in input: '" + str(p.value) + "'." + str(PosInfo(p.lineno)))


# Build the lexer
parser = yacc.yacc()