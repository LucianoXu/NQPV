# ------------------------------------------------------------
# NQPV_lexer.py
#
# tokenizer for nondeterministic quantum programs
# ------------------------------------------------------------
import ply.lex as lex

reserved = {
    'skip': 'SKIP',
    'abort' : 'ABORT',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do' : 'DO',
    'end' : 'END',
    'qvar' : 'QVAR',
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