# ------------------------------------------------------------
# NQPV_parser.py
#
# parser for nondeterministic quantum programs
# ------------------------------------------------------------

import ply.yacc as yacc

from .NQPV_lexer import tokens, lexer

from .NQPV_ast import *

# program declaration section
def p_prog(p):
    'prog : QVAR id_ls predicates_ls sequence predicates_ls'
    p[0] = {
        'qvar' : p[2],
        'pre-cond' : p[3],
        'sequence' : p[4],
        'post-cond' : p[5]
    }

# prog to code
def prog_to_code(p, prefix):
    r = prefix + "qvar "+ vls_to_code(p['qvar']) +"\n\n"
    r += prefix + "{ " + predicate_to_code(p['pre-cond']) + " }\n\n"
    r += sequence_to_code(p['sequence'], prefix) + "\n\n"
    r += prefix + "{ " + predicate_to_code(p['post-cond']) + " }\n"
    return r

def p_sequence_form(p):
    'sequence : sentence'
    p[0] = [p[1]]

def p_sequence_append(p):
    'sequence : sequence SEMICOLON sentence'
    p[0] = p[1] + [p[3]]


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
    'nondet_choice : LBRAKET sequence NONDET_CHOICE sequence RBRAKET'
    p[0] = NondetStruct(p)

def p_if(p):
    'if : IF ID id_ls THEN sequence ELSE sequence END'
    p[0] = IfStruct(p)

def p_while(p):
    'while : inv_ls WHILE ID id_ls DO sequence END'
    p[0] = WhileStruct(p)


def p_skip(p):
    'skip : SKIP'
    p[0] = SkipStruct(p)

def p_abort(p):
    'abort : ABORT'
    p[0] = AbortStruct(p)

def p_unitary(p):
    '''unitary : id_ls MUL_EQ ID
                | ID MUL_EQ ID'''
    p[0] = UnitaryStruct(p)

def p_init(p):
    '''init : id_ls ASSIGN ZERO
            | ID ASSIGN ZERO'''
    p[0] = InitStruct(p)

#define the invariants
def p_inv_end(p):
    'inv_ls : inv_pre RBRACE'
    p[0] = p[1]

def p_inv_append(p):
    'inv_pre : inv_pre ID id_ls'
    p[0] = p[1] + [(p[2], p[3])]

def p_inv_start(p):
    'inv_pre : LBRACE INV COLON ID id_ls'
    p[0] = [(p[4], p[5])]


#define the quantum predicates
def p_predicates_end(p):
    'predicates_ls : predicates_pre RBRACE'
    p[0] = p[1]

def p_predicates_append(p):
    'predicates_pre : predicates_pre ID id_ls'
    p[0] = p[1] + [(p[2], p[3])]

def p_predicates_start(p):
    'predicates_pre : LBRACE ID id_ls'
    p[0] = [(p[2], p[3])]

# define the list of quantum variables
def p_id_ls_end(p):
    'id_ls : id_ls_pre RSBRAKET'
    p[0] = p[1]

def p_id_ls_append(p):
    'id_ls_pre : id_ls_pre ID'
    p[0] = p[1] + [p[2]]

def p_id_ls_start(p):
    'id_ls_pre : LSBRAKET ID'
    p[0] = [p[2]]

# Error rule for syntax errors

from .tools import err

error_info = ""
silent = False

def p_error(p):
    global error_info, silent
    cur_info = "(line " + str(p.lineno) + ")\tSyntax error in input: '" + str(p.value) + "'. \n"
    error_info += err(cur_info, silent)


# Build the lexer
parser = yacc.yacc()