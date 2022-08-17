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
# semantics_analyser.py
#
# semantics analyser for nondeterministic quantum programs
#
# verification include: 
#   - whether the variables are predefined
#   - whether the unitary/measurement/hermitian operator referred in the program exists in the folder
#   - whether the unitary/measurement/hermitian operator provided is valid
#   - whether the unitary/measurement/hermitian operataor matches the variable lists
#
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Dict

from .logsystem import LogSystem

import numpy as np
from . import NQPV_la

# store the error information
channel : str = "main"

#check whether the variables in check_ls are predefined in var_ls
def check_variable(var_ls : List[str], check_ls : List[str]) -> bool:

    used_qvar = []
    for var in check_ls:
        # check whether the variable is defined in qvar
        if var not in var_ls:
            LogSystem.channels[channel].append("Error: variable '" + var + "' not defined in qvar")
            return False
        # check whether the variable has been used
        if var in used_qvar:
            LogSystem.channels[channel].append("Error: Variable '" + var + "' appeared more than once in the variable list "+str(check_ls) + ".")
            return False
        used_qvar.append(var)
    return True

def check_unitary(id : str, unitary_dict : Dict[str,np.ndarray], var_ls : List[str], run_path : str, lib_path : str) -> bool:
    if id in unitary_dict:
        pass
    else:
        try:
            loaded = np.load(lib_path + "/unitary/" + id + ".npy")
        except:
            try:
                loaded = np.load(run_path + "/" + id + ".npy")
            except:
                LogSystem.channels[channel].append("Error: unitary '" + id +".npy' not found")
                return False

        # check for valid unitary
        if not NQPV_la.check_unity(loaded, id):
            return False

        unitary_dict[id] = loaded

    # check the dimension informaion
    if (len(var_ls) * 2 == len(unitary_dict[id].shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of unitary '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False



def check_measure(id : str, measure_dict : Dict[str,np.ndarray], var_ls : List[str], run_path : str, lib_path : str) -> bool:

    if id in measure_dict:
        pass
    else:
        try:
            loaded = np.load(lib_path + "/measure/" + id + ".npy")
        except:
            try:
                loaded = np.load(run_path + "/" + id + ".npy")
            except:
                LogSystem.channels[channel].append("Error: measurement '" + id +".npy' not found")
                return False

        # check for valid measurement
        if not NQPV_la.check_measure(loaded, id):
            return False
    
        measure_dict[id] = loaded

    # check the dimension information
    # + 1 is for the extra dimension of 0-result and 1-result
    if (len(var_ls) * 2 + 1 == len(measure_dict[id].shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of measurement '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False


def check_hermitian(id : str, herm_dict : Dict[str, np.ndarray], var_ls : List[str], run_path : str, lib_path : str) -> bool:
    # check whether the hermitian is suitable

    if id in herm_dict:
        pass
    else:
        try:
            loaded = np.load(lib_path + "/herm/" + id + ".npy")
        except:
            try:
                loaded = np.load(run_path + "/" + id + ".npy")
            except:
                LogSystem.channels[channel].append("Error: hermitian operator '" + id +".npy' not found")
                return False

        # check for valid unitary
        if not NQPV_la.check_hermitian_predicate(loaded, id):
            return False

        herm_dict[id] = loaded

    # check the dimension informaion
    if (len(var_ls) * 2 == len(herm_dict[id].shape)):
        return True
    else:
        LogSystem.channels[channel].append("Error: The dimensions of hermitian '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False


# check the semantics of prog. load and return the operators
def check(prog : Dict[str, Any], run_path : str, lib_path : str) -> None | Dict[str , Dict[str , np.ndarray]]:

    if prog == None:
        LogSystem.channels[channel].append("Error: The input abstract syntax tree is invalid.")
        return None

    # check the declared qvar, ensure the uniqueness
    if not check_variable(prog['qvar'], prog['qvar']):
        return None

    pinfo = {
        'unitary' : {},
        'measure' : {},
        'herm' : {},
        'while_exists' : False
    }
    
    # check the pre-condition and post-condition
    for herm_tuple in prog['pre-cond']:
        if not check_variable(prog['qvar'], herm_tuple[1]):
            return None
        if not check_hermitian(herm_tuple[0], pinfo['herm'], herm_tuple[1], run_path, lib_path):
            return None
    for herm_tuple in prog['post-cond']:
        if not check_variable(prog['qvar'], herm_tuple[1]):
            return None
        if not check_hermitian(herm_tuple[0], pinfo['herm'], herm_tuple[1], run_path, lib_path):
            return None

    if check_iter(prog['qvar'], prog['sequence'], pinfo, run_path, lib_path) :
        return pinfo
    else:
        return None
    

def check_iter(var_ls : list, sequence : list, pinfo : dict, run_path, lib_path):
    for sentence in sequence:
        if sentence.label == 'SKIP':
            pass
        elif sentence.label == 'ABORT':
            pass
        elif sentence.label == 'INIT':
            # check the variables
            if not check_variable(var_ls, sentence.vls):
                return False
        elif sentence.label == 'UNITARY':
            # check the variables
            if not check_variable(var_ls, sentence.vls):
                return False
            # check the unitary
            if not check_unitary(sentence.unitary, pinfo['unitary'], sentence.vls, run_path, lib_path):
                return False

        elif sentence.label == 'IF':
            # check the variables
            if not check_variable(var_ls, sentence.measure_vls):
                return False
            # check the measure existence
            if not check_measure(sentence.measure, pinfo['measure'], sentence.measure_vls, run_path, lib_path):
                return False
            # check the two subprograms
            if not check_iter(var_ls, sentence.S0, pinfo, run_path, lib_path):
                return False
            if not check_iter(var_ls, sentence.S1, pinfo, run_path, lib_path):
                return False
        
        elif sentence.label == 'WHILE':
            pinfo['while_exists'] = True
            # check the hermitian operators
            for herm_tuple in sentence.inv:
                if not check_variable(var_ls, herm_tuple[1]):
                    return False
                if not check_hermitian(herm_tuple[0], pinfo['herm'], herm_tuple[1], run_path, lib_path):
                    return False
            # check the variables
            if not check_variable(var_ls, sentence.measure_vls):
                return False
            # check the measure existence
            if not check_measure(sentence.measure, pinfo['measure'], sentence.measure_vls, run_path, lib_path):
                return False
            # check the subprogram
            if not check_iter(var_ls, sentence.S, pinfo, run_path, lib_path):
                return False
        
        elif sentence.label == 'NONDET_CHOICE':
            # check the subprograms
            for sub_sequence in sentence.S_ls:
                if not check_iter(var_ls, sub_sequence, pinfo, run_path, lib_path):
                    return False
        
        else:
            raise Exception("Unknown program structure.")

    # after the examination of all programs in the sequence
    return True
