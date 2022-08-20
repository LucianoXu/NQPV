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

import os
import numpy as np

from .optlib_inject import optlib_inject, optload_inject

from .logsystem import LogSystem

from .tools import lineno_added
from .settings import Settings

from .syntaxes import *
from .syntaxes import qlexer, qparser 


# report channel
channel = "main"
channel_cmd = "cmd"
channel_witness = "witness"
channel_syntax = "syntax"
channel_semantics = "semantics"

def verifiy_reset(run_path : str) -> bool:
    # clean up the error info
    
    if channel not in LogSystem.channels:
        LogSystem(channel)
    LogSystem.channels[channel].summary()
    
    if channel_cmd not in LogSystem.channels:
        LogSystem(channel_cmd)
    LogSystem.channels[channel_cmd].summary()

    if channel_witness not in LogSystem.channels:
        LogSystem(channel_witness)
    LogSystem.channels[channel_witness].summary()

    if channel_syntax not in LogSystem.channels:
        LogSystem(channel_syntax)
    LogSystem.channels[channel_syntax].summary()

    if channel_semantics not in LogSystem.channels:
        LogSystem(channel_semantics)
    LogSystem.channels[channel_semantics].summary()

    optlib_inject()

    if not optload_inject(run_path):
        return False
    
    return True


def verify(folder_path, total_correctness = False, preserve_pre = False, opt_in_output = False, save_opt = False):

    if total_correctness:
        print("total correctness not supported yet")
        return

    if not verifiy_reset(os.getcwd()):
        LogSystem.channels[channel].summary(None, True, True)
        return


    ch_cmd = LogSystem.channels[channel_cmd]

    ch_cmd.append("\n= Nondeterministic Quantum Program Verifier Output = \n")
    ch_cmd.append("Version: " + Settings.version + "\n")

    # Prompt the running path
    ch_cmd.append("running path: " + os.getcwd() +"\n")

    print(ch_cmd.summary(drop=False))
    
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

    ch_cmd.summary(p_output)

    ch_cmd.single("folder path: "+ folder_path + "\n", p_output, True)

    if total_correctness:
        ch_cmd.single("property to verify: Total Correctness\n", p_output, True)
    else:
        ch_cmd.single("property to verify: Partial Correctness\n", p_output, True)

    ch_cmd.single("intermediate preconditions preserved: "+("Yes" if preserve_pre else "No") + "\n", p_output, True)
    ch_cmd.single("show operators in this output: " + ("Yes" if opt_in_output else "No") + "\n", p_output, True)
    ch_cmd.single("operators saved in running paht: "+ ("Yes" if save_opt else "No") + "\n", p_output, True)

    ch_cmd.single("--------------------------------------------", p_output, True)
    ch_cmd.single("<prog>\n", p_output, True)
    ch_cmd.single(lineno_added(prog_str), p_output, True)
    ch_cmd.single("\n--------------------------------------------\n", p_output, True)

    # check whether the file is empty
    if prog_str == "":
        ch_cmd.single("Program file '" + os.path.join(folder_path, 'prog.nqpv') + "' is empty.", p_output, True)
        p_output.close()
        return

    # syntactic analysis, produce the abstract syntax tree
    ch_cmd.single("syntactic and semantic analysis ...\n", None, True)
    ast = qparser.parser.parse(prog_str)
    if not LogSystem.channels[channel_syntax].empty or not LogSystem.channels[channel_semantics].empty:
        LogSystem.channels[channel_semantics].summary(p_output, True, True)
        LogSystem.channels[channel_syntax].summary(p_output, True, True)
        p_output.close()
        return
    ch_cmd.single("syntactic and semantic analysis passed.\n", p_output, True)

    # start verification
    ch_cmd.single("verification starts, calculating weakest (liberal) preconditions...\n", p_output, True)

    print(ast)

    print(ast.proof_check())

    LogSystem.channels[channel_semantics].summary(p_output, True, True)

    LogSystem.channels[channel_witness].summary(p_output, True, True)

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