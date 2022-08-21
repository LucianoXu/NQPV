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

from .semantics.qVar import QvarLs
from .semantics.opt_env import OptEnv

from .optlib_inject import optlib_inject, optload_inject

from .logsystem import LogSystem

from .tools import lineno_added
from .settings import Settings

from .syntaxes import *
from .syntaxes import qlexer, qparser 

from .id_env import IdEnv


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

    num_witness = len(LogSystem.channels["witness"])
    LogSystem.channels["witness"].summary(pfile, True, True)

    # summrize the number
    summary = "Error (" + str(num_error) + "), Warning (" + str(num_warning) + ")"
    if num_witness > 0:
        summary += ", witness reported"
    LogSystem.channels["info"].single(summary, pfile, True)

    return num_error == 0

    



def verify(folder_path, total_correctness = False, opt_in_output = False, save_opt = False):

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
    
    ch_info.single("precision: " + str(Settings.EPS()) + "\n", p_output, True)

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
    if not channel_check(p_output, "Syntactic and Semantic Analysis:"):
        p_output.close()
        return

    # exhibit the sequence of quantum variables
    ch_info.single("\nQuantum Variable Sequence:\n" + str(QvarLs.qvar), p_output, True)

    # start verification
    ch_info.single("\n--------------------------------------------\n", p_output, True)
    ch_info.single("Verification Calculating ...\n", None, True)

    ast.proof_check()
    
    channel_check(p_output, "Verification Result:")


    # output the proof outline
    ch_info.single("\n(proof outline shown in 'output.txt)\n", None, True)
    ch_info.single("--------------------------------------------", p_output, False)
    ch_info.single("<prog proof outline> \n", p_output, False)
    ch_info.single(lineno_added(str(ast)), p_output, False)
    if opt_in_output:
        ch_info.single("(operators shown in 'output.txt')\n", None, True)
    ch_info.single("--------------------------------------------", p_output, False)


    # show the operators in the output
    if opt_in_output:

        ch_info.single("<operators mentioned> \n", p_output, False)

        for id in IdEnv.id_opt_used:
            ch_info.single(OptEnv.lib[id].full_str,p_output, False)
            ch_info.single("\n", p_output, False)
        
    # save the related operaters
    if save_opt:
        ch_info.single("Saving operators...\n", None, True)
        try:
            if not os.path.exists(os.path.join(folder_path, "opt_saved")):
                os.mkdir(os.path.join(folder_path, "opt_saved"))
            for id in IdEnv.id_opt_used:
                # ch_info.single(os.path.join(folder_path, id + ".npy")+" ... ", None, True)
                np.save(os.path.join(folder_path ,"opt_saved", id + ".npy"), OptEnv.lib[id].data)
        except:
            LogSystem.channels["error"].single("Operator Saving Fails.", p_output, True)


    # close the output file
    p_output.close()
