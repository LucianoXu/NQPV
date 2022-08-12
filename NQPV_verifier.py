# ------------------------------------------------------------
# NQPV_verifier.py
#
# method 'verify' provides the user interface of the whole verifier
# ------------------------------------------------------------

import os
import numpy as np

from tools import msg, ver_label, lineno_added

from NQPV_ast import *
import NQPV_lexer, NQPV_parser, NQPV_la

import semantics_analyser
from semantics_analyser import check
import backward_transformer
from backward_transformer import wlp_verify

def verifiy_reset():
    # clean up the error info
    NQPV_lexer.error_info = ""
    NQPV_lexer.silent = True
    NQPV_parser.error_info = ""
    NQPV_parser.silent = True
    semantics_analyser.error_info = ""
    semantics_analyser.silent = True
    backward_transformer.error_info = ""
    backward_transformer.silent = True


def verify(folder_path, silent = False, total_correctness = False, preserve_pre = False, opt_in_output = False, save_opt = False):

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

    msg("intermediate preconditions preservved: "+("Yes" if preserve_pre else "No") + "\n\n", silent, p_output)
    msg("show operators in this output: " + ("Yes" if opt_in_output else "No") + "\n\n", silent, p_output)
    msg("operators saved in running paht: "+ ("Yes" if save_opt else "No") + "\n\n", silent, p_output)

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

    v_result = wlp_verify(ast, pinfo, preserve_pre)

    if backward_transformer.error_info != "":
        msg(backward_transformer.error_info, False, p_output)

    # declare the result
    if v_result:
        msg("Verification Result: Property holds.\n\n", silent, p_output)
    else:
        # check whether there is while structures
        if pinfo['while_exists']:
            msg("Verification Result: Property cannot be determined. A suitable loop invariant may be sufficient.\n\n", silent, p_output)
        else:
            msg("Verification Result: Property does not hold.\n\n", silent, p_output)

    # show the proof outline
    
    print("(proof outline shown in 'output.txt)\n\n", end='')
    msg("--------------------------------------------\n", True, p_output)
    msg("<prog proof outline> \n\n", True, p_output)
    msg(lineno_added(NQPV_parser.prog_to_code(ast, "")), True, p_output)



    # show the operators in the output
    if opt_in_output:

        # prompt that the operator output is hidden in cmd
        if not silent:
            print("(operators shown in 'output.txt')\n\n", end='')
        
        msg("\n\n--------------------------------------------\n", True, p_output)
        msg("<unitary operators> \n\n", True, p_output)

        for id in pinfo['unitary']:
            msg(id + "\n", True, p_output)
            msg(str(NQPV_la.tensor_to_matrix(pinfo['unitary'][id])), True, p_output)
            msg("\n\n", True, p_output)
        
        msg("--------------------------------------------\n", True, p_output)

        msg("<Hermitian operators> \n\n", True, p_output)

        for id in pinfo['herm']:
            msg(id + "\n", True, p_output)
            msg(str(NQPV_la.tensor_to_matrix(pinfo['herm'][id])), True, p_output)
            msg("\n\n", True, p_output)
        
        msg("--------------------------------------------\n", True, p_output)

        msg("<measurement operators> \n\n", True, p_output)

        for id in pinfo['measure']:
            msg(id + " RESULT0 \n", True, p_output)
            msg(str(NQPV_la.tensor_to_matrix(pinfo['measure'][id][0])), True, p_output)
            msg("\n\n", True, p_output)
            msg(id + " RESULT1 \n", True, p_output)
            msg(str(NQPV_la.tensor_to_matrix(pinfo['measure'][id][1])), True, p_output)
            msg("\n\n", True, p_output)
        
        msg("--------------------------------------------\n", True, p_output)

        if preserve_pre:
            msg("<Hermitians for intermediate preconditions> \n\n", True, p_output)

            for id in pinfo['im_pre-cond']:
                msg(id + "\n", True, p_output)
                msg(str(NQPV_la.tensor_to_matrix(pinfo['im_pre-cond'][id])), True, p_output)
                msg("\n\n", True, p_output)
            
            msg("--------------------------------------------\n", True, p_output)

    # save the related operaters
    if save_opt:
        print("Saving operators...\n\n", end='')

        for id in pinfo['unitary']:
            print("unitary: " + id + ".npy ... ", end='')
            np.save(folder_path + id + ".npy", pinfo['unitary'][id])
            print("done\n", end = '')
        for id in pinfo['measure']:
            print("measurement: " + id + ".npy ... ", end='')
            np.save(folder_path + id + ".npy", pinfo['measure'][id])
            print("done\n", end = '')
        for id in pinfo['herm']:
            print("Hermitian Operator: " + id + ".npy ... ", end='')
            np.save(folder_path + id + ".npy", pinfo['herm'][id])
            print("done\n", end = '')
        for id in pinfo['im_pre-cond']:
            print("Hermitian Operator: " + id + ".npy ... ", end='')
            np.save(folder_path + id + ".npy", pinfo['im_pre-cond'][id])
            print("done\n", end = '')


    # close the output file
    p_output.close()
