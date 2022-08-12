# ------------------------------------------------------------
# NQPV_verifier.py
#
# method 'verify' provides the user interface of the whole verifier
# ------------------------------------------------------------

import os

from tools import msg, ver_label, lineno_added


import NQPV_lexer,NQPV_parser
import semantics_analyser
from semantics_analyser import check
from backward_transformer import wlp_verify

def verifiy_reset():
    # clean up the error info
    NQPV_lexer.error_info = ""
    NQPV_lexer.silent = True
    NQPV_parser.error_info = ""
    NQPV_parser.silent = True
    semantics_analyser.error_info = ""
    semantics_analyser.silent = True


def verify(folder_path, silent = False, total_correctness = False):

    verifiy_reset()

    msg("\n= Nondeterministic Quantum Program Verifier Output = \n\n", silent, None)

    msg("Version: " + ver_label + "\n\n", silent, None)

    # Prompt the running path
    msg("running path: " + os.getcwd() +"\n\n", silent, None)

    # detect the file
    if folder_path[-1] != '/':
        folder_path += '/'
    try:
        p_prog = open(folder_path + 'prog', 'r')
        prog_str = p_prog.read()
        p_prog.close()
    except:
        print("Error: program file '" + folder_path + "prog' not found.")
        return

    
    # create the output file
    try:
        p_output = open(folder_path + 'output.txt', 'w')
    except:
        print("Error: cannot create output file '" + folder_path + "output.txt'.")
        return

    # add the beginning of output.txt
    p_output.write("\n= Nondeterministic Quantum Program Verifier Output = \n\n")
    p_output.write("Version: " + ver_label + "\n\n")
    p_output.write("running path: " + os.getcwd() +"\n\n")

    msg("folder path: "+ folder_path + "\n\n", silent, p_output)

    if total_correctness:
        msg("property to verify: Total Correctness\n\n", silent, p_output)
    else:
        msg("property to verify: Partial Correctness\n\n", silent, p_output)

    msg("--------------------------------------------\n", silent, p_output)
    msg("<prog> \n\n", silent, p_output)
    msg(lineno_added(prog_str), silent, p_output)
    msg("\n\n--------------------------------------------\n\n", silent, p_output)

    
    # syntactic analysis, produce the abstract syntax tree
    msg("syntactic analysis ...\n\n", silent, None)
    ast = NQPV_parser.parser.parse(prog_str)
    if NQPV_lexer.error_info != "" or NQPV_parser.error_info != "":
        if NQPV_lexer.error_info != "":
            msg(NQPV_lexer.error_info, False, p_output)
        else:
            msg(NQPV_parser.error_info, False, p_output)
        msg("\nAbort: syntactic analysis not passed.\n", False, p_output)
        p_output.close()
        return
    msg("syntactic analysis passed.\n\n", silent, p_output)

    # semantic analysis
    msg("semantic analysis ...\n\n", silent, None)
    pinfo = check(ast, folder_path)
    if pinfo is None:
        # it means there is error in the semantic analysis
        msg(semantics_analyser.error_info, False, p_output)
        msg("\nAbort: semantic analysis not passed.\n", False, p_output)
        p_output.close()
        return
    msg("semantic analysis passed.\n\n", silent, p_output)


    # start verification

    msg("verification starts, calculating weakest (liberal) preconditions...\n\n", silent, None)

    v_result = wlp_verify(ast, pinfo)

    # declare the result
    if v_result:
        msg("\nVerification Result: Property holds.\n\n", silent, p_output)
    else:
        # check whether there is while structures
        if pinfo['while_exists']:
            msg("\nVerification Result: Property cannot be determined. A suitable loop invariant may be sufficient.\n\n", silent, p_output)
        else:
            msg("\nVerification Result: Property does not hold.\n\n", silent, p_output)

    # close the output file
    p_output.close()
