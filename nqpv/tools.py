# ------------------------------------------------------------
# tools.py
#
# define the tools used in this verifier
# ------------------------------------------------------------

ver_label = "0.1"

def err(txt, silent):
    if not silent:
        print(txt, end='')
    return txt


def msg(txt, silent, p_output):
    # message the text in the cmd and write in the output file
    if not silent:
        print(txt, end='')
    if p_output is not None:
        p_output.write(txt)

def lineno_added(txt):
    '''
    Add an line number in front of each line
    '''
    line_no = 1
    r = str(line_no) + '\t\t' + txt
    line_no += 1

    i = 0
    while i < len(r):
        if r[i] == '\n':
            r = r[:i+1] + str(line_no) + '\t\t' + r[i+1:]
            line_no += 1
        i += 1

    return r
