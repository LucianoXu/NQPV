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
# vparser.py
#
# parser
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List

import ply.yacc as yacc

from .pos_info import PosInfo
from .vlexer import tokens, lexer
from . import ast

from ..log_system import LogSystem, RuntimeErrorWithLog

# program declaration section
def p_env(p):
    '''
    env     : cmd
            | env ';' cmd
    '''
    if isinstance(p[1], ast.AstEnv):
        p[0] = ast.AstEnv(p[1].pos, p[1].cmd_ls + [p[3]])
    else:
        p[0] = ast.AstEnv(p[1].pos, [p[1]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_cmd(p):
    '''
    cmd     : definition
            | example
            | axiom
    '''
    p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_definition(p):
    '''
    definition  : DEF id AS type BY expression END
                | DEF opt_get AS type BY expression END
    '''
    p[0] = ast.AstDefinition(PosInfo(p.slice[1].lineno), p[2], p[4], p[6])

    if p[0] is None:
        raise Exception("unexpected situation")


def p_example(p):
    '''
    example : EXAMPLE BY expression END
    '''
    p[0] = ast.AstExample(PosInfo(p.slice[1].lineno), p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_axiom(p):
    '''
    axiom   : AXIOM id AS predicate PROGRAM qvar_ls predicate END
    '''
    p[0] = ast.AstAxiom(PosInfo(p.slice[1].lineno), p[2], p[4], p[5], p[6], p[7])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_type(p):
    '''
    type    : OPT_GET
            | OPERATOR qvar_ls
            | PROGRAM qvar_ls
            | PROOF qvar_ls
            | predicate PROGRAM qvar_ls predicate
    '''
    if p[1] == "opt_get":
        label = "opt_get"
    elif p[1] == "operator":
        label = "operator"
    elif p[1] == "program":
        label = "program"
    elif p[1] == "proof":
        label = "proof"
    else:
        label = "proof_limited" # proof limited to the specified Hoare triple


    if len(p) == 5:
        p[0] = ast.AstType(p[1].pos, label, (p[1], p[2], p[3], p[4]))
    elif len(p) == 3:
        p[0] = ast.AstType(PosInfo(p.slice[1].lineno), label, (p[1], p[2]))
    elif len(p) == 2:
        p[0] = ast.AstType(PosInfo(p.slice[1].lineno), label, (p[1],))
    else:
        raise Exception("unexpected situation")

    if p[0] is None:
        raise Exception("unexpected situation")

def p_expression(p):
    '''
    expression  : env expression
                | PROGRAM ':' prog
                | PROOF ':' proof
                | WP ':' proof
    '''
    if len(p) == 3:
        p[0] = p[2]
        p[0].env = p[1]
    else:
        p[0] = ast.AstExpression(PosInfo(p.slice[1].lineno), p[1], p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_opt_get(p):
    '''
    opt_get  : opt_get_pre ELLIPSIS ']'
    '''
    p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_opt_get_pre(p):
    '''
    opt_get_pre  : '[' id
                    |   opt_get_pre id
    '''
    if p[1] == '[':
        p[0] = ast.AstOptGetLs(PosInfo(p.slice[1].lineno), [p[2]])
    else:
        p[0] = ast.AstOptGetLs(p[1].pos, p[1].data + [p[2]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_qvar_ls(p):
    '''
    qvar_ls : qvar_ls_pre ']'
    '''
    p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_qvar_ls_pre(p):
    '''
    qvar_ls_pre : '[' id
                | qvar_ls_pre id
    '''
    if p[1] == '[':
        p[0] = ast.AstQvarLs(PosInfo(p.slice[1].lineno), [p[2]])
    else:
        p[0] = ast.AstQvarLs(p[1].pos, p[1].data + [p[2]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_predicate(p):
    '''
    predicate   : predicate_pre '}'
    '''
    p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_predicate_pre(p):
    '''
    predicate_pre   : '{' id qvar_ls
                    | predicate_pre id qvar_ls
    '''
    if p[1] == '{':
        p[0] = ast.AstPredicate(PosInfo(p.slice[1].lineno), [(p[2], p[3])])
    else:
        p[0] = ast.AstPredicate(p[1].pos, p[1].data + [(p[2], p[3])])

    if p[0] is None:
        raise Exception("unexpected situation")


def p_prog(p):
    '''
    prog    : statement
            | prog ';' statement
    '''
    if len(p) == 2:
        p[0] = ast.AstProg(p[1].pos, [p[1]])
    else:
        p[0] = ast.AstProg(p[1].pos, p[1].data + [p[3]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_statement(p):
    '''
    statement : skip
                | abort
                | init
                | unitary
                | if
                | while
                | nondet
                | id qvar_ls
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ast.AstSubprog(p[1].pos, p[1], p[2])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_skip(p):
    '''
    skip    : SKIP
    '''
    p[0] = ast.AstSkip(PosInfo(p.slice[1].lineno))

    if p[0] is None:
        raise Exception("unexpected situation")

def p_abort(p):
    '''
    abort   : ABORT
    '''
    p[0] = ast.AstAbort(PosInfo(p.slice[1].lineno))

    if p[0] is None:
        raise Exception("unexpected situation")

def p_init(p):
    '''
    init    : id INIT
            | qvar_ls INIT
    '''
    if isinstance(p[1], ast.AstQvarLs):
        p[0] = ast.AstInit(p[1].pos, p[1])
    else:
        qvar_ls = ast.AstQvarLs(p[1].pos, [p[1]])
        p[0] = ast.AstInit(qvar_ls.pos, qvar_ls)

    if p[0] is None:
        raise Exception("unexpected situation")

def p_unitary(p):
    '''
    unitary : id MUL_EQ id
            | qvar_ls MUL_EQ id
    '''
    if isinstance(p[1], ast.AstQvarLs):
        p[0] = ast.AstUnitary(p[1].pos, p[3], p[1])
    else:
        qvar_ls = ast.AstQvarLs(p[1].pos, [p[1]])
        p[0] = ast.AstUnitary(qvar_ls.pos, p[3], qvar_ls)

    if p[0] is None:
        raise Exception("unexpected situation")

def p_if(p):
    '''
    if      : IF id qvar_ls THEN prog ELSE prog END
    '''
    p[0] = ast.AstIf(PosInfo(p.slice[1].lineno), p[2], p[3], p[5], p[7])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_while(p):
    '''
    while   : WHILE id qvar_ls DO prog END
    '''
    p[0] = ast.AstWhile(PosInfo(p.slice[1].lineno), p[2], p[3], p[5])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_nondet(p):
    '''
    nondet  : nondet_pre '#' prog ')'
    '''
    p[0] = ast.AstNondet(p[1].pos, p[1].data + p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_nondet_pre(p):
    '''
    nondet_pre  : '(' prog
                | nondet_pre '#' prog
    '''
    if len(p) == 3:
        p[0] = ast.AstNondet(PosInfo(p.slice[1].lineno), [p[2]])
    else:
        p[0] = ast.AstNondet(p[1].pos, p[1].data + p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_proof(p):
    '''
    proof   : proof_mid ';' predicate
    '''
    p[0] = ast.AstProof(p[1].pos, p[1].data + [p[3]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_proof_mid(p):
    '''
    proof_mid   : proof_statement
                | proof_mid ';' proof_statement
    '''
    if len(p) == 2:
        p[0] = ast.AstProof(p[1].pos, [p[1]])
    else:
        p[0] = ast.AstProof(p[1].pos, p[1].data + [p[3]])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_proof_statement(p):
    '''
    proof_statement : id qvar_ls
                    | skip
                    | abort
                    | init
                    | unitary
                    | if_proof
                    | while_proof
                    | nondet_proof
                    | predicate
    '''
    if isinstance(p[1], ast.AstID):
        p[0] = ast.AstSubproof(p[1].pos, p[1], p[2])
    else:
        p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_if_proof(p):
    '''
    if_proof    : IF id qvar_ls THEN proof_mid ELSE proof_mid END
    '''
    p[0] = ast.AstIfProof(PosInfo(p.slice[1].lineno), p[2], p[3], p[5], p[7])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_while_proof(p):
    '''
    while_proof : inv WHILE id qvar_ls DO prog END
    '''
    p[0] = ast.AstWhileProof(p[1].pos, p[1], p[2], p[3], p[5])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_nondet_proof(p):
    '''
    nondet_proof  : nondet_proof_pre '#' proof_mid ')'
    '''
    p[0] = ast.AstNondetProof(p[1].pos, p[1].data + p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_nondet_proof_pre(p):
    '''
    nondet_proof_pre  : '(' proof_mid
                | nondet_proof_pre '#' proof_mid
    '''
    if len(p) == 3:
        p[0] = ast.AstNondetProof(PosInfo(p.slice[1].lineno), [p[2]])
    else:
        p[0] = ast.AstNondetProof(p[1].pos, p[1].data + p[3])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_inv(p):
    '''
    inv     : inv_pre '}'
    '''
    p[0] = p[1]

    if p[0] is None:
        raise Exception("unexpected situation")

def p_inv_pre(p):
    '''
    inv_pre : '{' INV ':' id qvar_ls
            | inv_pre id qvar_ls
    '''
    if p[1] == '{':
        p[0] = ast.AstInv(PosInfo(p.slice[1].lineno), [(p[4], p[5])])
    else:
        p[0] = ast.AstInv(p[1].pos, p[1].data + [(p[2], p[3])])

    if p[0] is None:
        raise Exception("unexpected situation")

def p_id (p):
    '''
    id      : ID
    '''
    p[0] = ast.AstID(PosInfo(p.slice[1].lineno), p[1])
    
    if p[0] is None:
        raise Exception("unexpected situation")

def p_error(p):
    if p is None:
        raise RuntimeErrorWithLog("unexpected end of fild")
    raise RuntimeErrorWithLog("Syntax error in input: '" + str(p.value) + "'.", PosInfo(p.lineno))


# Build the lexer
parser = yacc.yacc()