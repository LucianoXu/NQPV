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
# NQPV_verifier.py
#
# method 'verify' provides the user interface of the whole verifier
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Dict
from io import TextIOWrapper

import os
import numpy as np

from .optlib_inject import optlib_inject, optload_inject

from .logsystem import LogSystem

from .tools import lineno_added
from .settings import Settings

from .syntaxes import *
from .syntaxes import qlexer, qparser 


def verifiy_reset(folder_path : str) -> bool:
    # clean up the error info
        
    LogSystem("info").summary()
    LogSystem("warning", "Warning: ").summary()
    LogSystem("error", "Error: ").summary()
    LogSystem("witness").summary()
    optlib_inject()

    if not optload_inject(folder_path):
        return False
    
    return True

def channel_check(pfile : TextIOWrapper | None, title : str = "") -> bool:
    '''
    summrize the channel "error", "warning" and "info" in order
    If there is no error, return True. else return False.
    '''

    # begin the title
    LogSystem.channels["info"].single(title, pfile, True)

    num_error = len(LogSystem.channels["error"])
    LogSystem.channels["error"].summary(pfile, True, True)
    num_warning = len(LogSystem.channels["warning"])
    LogSystem.channels["warning"].summary(pfile, True, True)
    LogSystem.channels["info"].summary(pfile, True, True)

    # summrize the number
    LogSystem.channels["info"].single("Error (" + str(num_error) + "), Warning (" + str(num_warning) + ")",
        pfile, True)

    return num_error == 0

    



def verify(folder_path, total_correctness = False, preserve_pre = False, opt_in_output = False, save_opt = False):

    if total_correctness:
        print("total correctness not supported yet")
        return

    if not verifiy_reset(os.path.join(os.getcwd(), folder_path)):
        channel_check(None)
        return


    ch_info = LogSystem.channels["info"]

    ch_info.append("\n= Nondeterministic Quantum Program Verifier Output = \n")
    ch_info.append("Version: " + Settings.version + "\n")

    # Prompt the running path
    ch_info.append("running path: " + os.getcwd() +"\n")

    ch_info.summary(None, True, False)
    
    try:
        p_prog = open(os.path.join(folder_path,'prog.nqpv'), 'r')
        prog_str = p_prog.read()
        p_prog.close()
    except:
        print("Error: program file '" + os.path.join(folder_path,'prog.nqpv') + "' not found.")
        return

    
    # create the output file
    try:
        p_output = open(os.path.join(folder_path, 'output.txt'), 'w')
    except:
        print("Error: cannot create output file '" + os.path.join(folder_path, 'output.txt') + "'.")
        return

    # add the beginning of output.txt

    ch_info.summary(p_output)

    ch_info.single("folder path: "+ folder_path + "\n", p_output, True)

    if total_correctness:
        ch_info.single("property to verify: Total Correctness\n", p_output, True)
    else:
        ch_info.single("property to verify: Partial Correctness\n", p_output, True)

    ch_info.single("intermediate preconditions preserved: "+("Yes" if preserve_pre else "No") + "\n", p_output, True)
    ch_info.single("show operators in this output: " + ("Yes" if opt_in_output else "No") + "\n", p_output, True)
    ch_info.single("operators saved in running paht: "+ ("Yes" if save_opt else "No") + "\n", p_output, True)

    ch_info.single("--------------------------------------------", p_output, True)
    ch_info.single("<prog>\n", p_output, True)
    ch_info.single(lineno_added(prog_str), p_output, True)
    ch_info.single("\n--------------------------------------------\n", p_output, True)

    # check whether the file is empty
    if prog_str == "":
        ch_info.single("Program file '" + os.path.join(folder_path, 'prog.nqpv') + "' is empty.", p_output, True)
        p_output.close()
        return

    # syntactic analysis, produce the abstract syntax tree
    ch_info.single("syntactic and semantic analysis ...\n", None, True)
    ast = qparser.parser.parse(prog_str)
    if not channel_check(p_output):
        p_output.close()
        return
    ch_info.single("syntactic and semantic analysis passed.\n", p_output, True)

    # start verification
    ch_info.single("verification starts, calculating weakest (liberal) preconditions...\n", p_output, True)


    print(ast.proof_check())

    print(ast)
    
    channel_check(p_output)

    return


    v_result = wlp_verify(ast, pinfo, preserve_pre)

    if not LogSystem.channels[channel].empty:
        LogSystem.channels[channel].summary(p_output, True)

    # declare the result
    if v_result:
        ch_cmd.single("Verification Result: Property holds.\n", p_output, True)
    else:
        # check whether there is while structures
        if pinfo['while_exists']:
            ch_cmd.single("Verification Result: Property cannot be determined. A suitable loop invariant may be sufficient.\n", p_output, True)
        else:
            ch_cmd.single("Verification Result: Property does not hold.\n", p_output, True)

    if not LogSystem.channels[channel_witness].empty:
        LogSystem.channels[channel_witness].summary(p_output, True)

    # show the proof outline
    
    ch_cmd.single("(proof outline shown in 'output.txt)\n", None, True)
    ch_cmd.single("--------------------------------------------", p_output, True)
    ch_cmd.single("<prog proof outline> \n", p_output, True)
    ch_cmd.single(lineno_added(qparser.prog_to_code(ast, "")), p_output, True)



    # show the operators in the output
    if opt_in_output:

        # prompt that the operator output is hidden in cmd
        print("(operators shown in 'output.txt')\n\n", end='')
        
        ch_cmd.single("\n--------------------------------------------", p_output, True)
        ch_cmd.single("<unitary operators> \n", p_output, True)

        for id in pinfo['unitary']:
            ch_cmd.single(id ,p_output, True)
            ch_cmd.single(str(qLA.tensor_to_matrix(pinfo['unitary'][id])), p_output, True)
            ch_cmd.single("\n", p_output, True)
        
        ch_cmd.single("--------------------------------------------", p_output, True)

        ch_cmd.single("<Hermitian operators> \n", p_output, True)

        for id in pinfo['herm']:
            ch_cmd.single(id, p_output, True)
            ch_cmd.single(str(qLA.tensor_to_matrix(pinfo['herm'][id])), p_output, True)
            ch_cmd.single("\n", p_output, True)
        
        ch_cmd.single("--------------------------------------------", p_output, True)

        ch_cmd.single("<measurement operators> \n", p_output, True)

        for id in pinfo['measure']:
            ch_cmd.single(id + " RESULT0 ", p_output, True)
            ch_cmd.single(str(qLA.tensor_to_matrix(pinfo['measure'][id][0])), p_output, True)
            ch_cmd.single("\n", p_output, True)
            ch_cmd.single(id + " RESULT1 ", p_output, True)
            ch_cmd.single(str(qLA.tensor_to_matrix(pinfo['measure'][id][1])), p_output, True)
            ch_cmd.single("\n", p_output, True)
        
        ch_cmd.single("--------------------------------------------", p_output, True)

        if preserve_pre:
            ch_cmd.single("<Hermitians for intermediate preconditions> \n", p_output, True)

            for id in pinfo['im_pre-cond']:
                ch_cmd.single(id, p_output, True)
                ch_cmd.single(str(qLA.tensor_to_matrix(pinfo['im_pre-cond'][id])), p_output, True)
                ch_cmd.single("\n", p_output, True)
            
            ch_cmd.single("--------------------------------------------", p_output, True)

    # save the related operaters
    if save_opt:
        ch_cmd.single("Saving operators...\n", None, True)

        for id in pinfo['unitary']:
            ch_cmd.single("unitary: " + id + ".npy ... ", None, True)
            np.save(folder_path + "/" + id + ".npy", pinfo['unitary'][id])
            ch_cmd.single("done\n", None, True)
        for id in pinfo['measure']:
            ch_cmd.single("measurement: " + id + ".npy ... ", None, True)
            np.save(folder_path + "/" + id + ".npy", pinfo['measure'][id])
            ch_cmd.single("done\n", None, True)
        for id in pinfo['herm']:
            ch_cmd.single("Hermitian Operator: " + id + ".npy ... ", None, True)
            np.save(folder_path + "/" + id + ".npy", pinfo['herm'][id])
            ch_cmd.single("done\n", None, True)
        if preserve_pre:
            for id in pinfo['im_pre-cond']:
                ch_cmd.single("Hermitian Operator: " + id + ".npy ... ", None, True)
                np.save(folder_path + "/" + id + ".npy", pinfo['im_pre-cond'][id])
                ch_cmd.single("done\n", None, True)


    # close the output file
    p_output.close()
