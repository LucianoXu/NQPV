# ------------------------------------------------------------
# NQPV_parser.py
#
# parser for nondeterministic quantum programs
# ------------------------------------------------------------

import ply.yacc as yacc

from NQPV_lexer import tokens, lexer

# program declaration section
def p_prog(p):
    'prog : QVAR id_ls sequence'
    p[0] = {
        'qvar' : p[2],
        'sequence' : p[3]
    }

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
    'nondet_choice : LBRACE sequence NONDET_CHOICE sequence RBRACE'
    p[0] = ('NONDET_CHOICE', p[2], p[4])

def p_if(p):
    'if : IF ID id_ls THEN sequence ELSE sequence END'
    p[0] = ('IF', p[2], p[3], p[5], p[7])

def p_while(p):
    'while : WHILE ID id_ls DO sequence END'
    p[0] = ('WHILE', p[2], p[3], p[5])


def p_skip(p):
    'skip : SKIP'
    p[0] = ('SKIP',)

def p_abort(p):
    'abort : ABORT'
    p[0] = ('ABORT',)

def p_unitary(p):
    '''unitary : id_ls MUL_EQ ID
                | ID MUL_EQ ID'''
    if isinstance(p[1], list):
        p[0] = ('UNITARY', p[1], p[3])
    else:
        p[0] = ('UNITARY', [p[1]], p[3])

def p_init(p):
    '''init : id_ls ASSIGN ZERO
            | ID ASSIGN ZERO'''
    if isinstance(p[1], list): 
        p[0] = ('INIT', p[1])
    else:
        p[0] = ('INIT', [p[1]])

# define the list of quantum variables
def p_vars_end(p):
    'id_ls : id_ls_pre RSBRAKET'
    p[0] = p[1]

def p_vars_append(p):
    'id_ls_pre : id_ls_pre ID'
    p[0] = p[1] + [p[2]]

def p_vars_start(p):
    'id_ls_pre : LSBRAKET ID'
    p[0] = [p[2]]

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input: '" + str(p.value) + "' " + str(p))


# Build the lexer
parser = yacc.yacc()