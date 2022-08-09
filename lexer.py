# ------------------------------------------------------------
# lexer.py
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
    'end' : 'END'
}

# List of token names.
tokens = [
    'ID',   #identity
    'ASSIGN',
    'UNITARY',
    'SEQUENCE',
    'NONDET_CHOICE',
    'LSBRAKET',
    'RSBRAKET'
 ] + list(reserved.values())

# Regular expression rules for simple tokens
t_ASSIGN = r':='
t_UNITARY = r'\*='
t_SEQUENCE = r';'
t_NONDET_CHOICE = r'[#]'
t_LSBRAKET = r'\['
t_RSBRAKET = r'\]'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')    # Check for reserved words
    return t


# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

# Test it out
data = '''
ifandonlyif if if] while [#] jnj;end
'''

# Give the lexer some input
lexer.input(data)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break      # No more input
    print(tok)
