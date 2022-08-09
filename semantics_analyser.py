# ------------------------------------------------------------
# semantics_analyser.py
#
# semantics analyser for nondeterministic quantum programs
#
# verification include: 
#   - whether the variables are predefined
#   - whether the unitary/measurement referred in the program exists in the folder
#   - whether the unitary/measurement provided is valid
#   - whether the unitary/measurement matches the variable lists
#
# ------------------------------------------------------------

import numpy as np
import NQPV_la

# check the semantics of prog. load and return the operators
def check(prog : dict):
    if prog == None:
        print("The input abstract syntax tree is invalid.")
        return None

    unitary_dict = {}
    measure_dict = {}

    if check_iter(prog['qvar'], prog['sequence'], unitary_dict, measure_dict) :
        return (unitary_dict, measure_dict)
    else:
        return None
    
#check whether the variables in check_ls are predefined in var_ls
def check_variable(var_ls : list, check_ls : list):
    for var in check_ls:
        if var not in var_ls:
            print("variable '" + var + "' not defined in qvar.")
            return False
    return True

def check_unitary(id, unitary_dict):
    if id in unitary_dict:
        return True
    else:
        try:
            loaded = np.load("./unitary/" + id + ".npy")
        except:
            print("unitary '" + id +".npy' not found")
            return False

        # check for valid unitary
        if not NQPV_la.check_unity(loaded, id):
            return False

        unitary_dict[id] = loaded

        return True

def check_unitary_dim(unitary, unitary_dict, var_ls):
    if (len(var_ls) * 2 == len(unitary_dict[unitary].shape)):
        return True
    else:
        print("The dimensions of unitary '" + unitary + "' and qvars " + str(var_ls) + " do not match.")
        return False


def check_measure(id, measure_dict):
    if id in measure_dict:
        return True
    else:
        try:
            loaded = np.load("./measure/"+ id + ".npy")
        except:
            print("measurement '" + id +".npy' not found")
            return False

        # check for valid measurement
        if not NQPV_la.check_measure(loaded, id):
            return False
    
        measure_dict[id] = loaded

        return True

def check_measure_dim(measure, measure_dict, var_ls):
    # + 1 is for the extra dimension of 0-result and 1-result
    if (len(var_ls) * 2 + 1 == len(measure_dict[measure].shape)):
        return True
    else:
        print("The dimensions of measurement '" + measure + "' and qvars " + str(var_ls) + " do not match.")
        return False


def check_iter(var_ls : list, sequence : list, unitary_dict : dict, measure_dict : dict):
    for sentence in sequence:
        if sentence[0] == 'SKIP':
            pass
        elif sentence[0] == 'ABORT':
            pass
        elif sentence[0] == 'INIT':
            # check the variables
            if not check_variable(var_ls, sentence[1]):
                return False
        elif sentence[0] == 'UNITARY':
            # check the variables
            if not check_variable(var_ls, sentence[1]):
                return False
            # check the unitary existence
            if not check_unitary(sentence[2], unitary_dict):
                return False
            # check whether the dimension matches
            if not check_unitary_dim(sentence[2], unitary_dict, sentence[1]):
                return False

        elif sentence[0] == 'IF':
            # check the variables
            if not check_variable(var_ls, sentence[2]):
                return False
            # check the measure existence
            if not check_measure(sentence[1], measure_dict):
                return False
            # check whether the dimension matches
            if not check_measure_dim(sentence[1], measure_dict, sentence[2]):
                return False
            # check the two subprograms
            if not check_iter(var_ls, sentence[3], unitary_dict, measure_dict):
                return False
            if not check_iter(var_ls, sentence[4], unitary_dict, measure_dict):
                return False
        
        elif sentence[0] == 'WHILE':
            # check the variables
            if not check_variable(var_ls, sentence[2]):
                return False
            # check the measure existence
            if not check_measure(sentence[1], measure_dict):
                return False
            # check whether the dimension matches
            if not check_measure_dim(sentence[1], measure_dict, sentence[2]):
                return False
            # check the subprogram
            if not check_iter(var_ls, sentence[3], unitary_dict, measure_dict):
                return False
        
        elif sentence[0] == 'NONDET_CHOICE':
            # check the two subprograms
            if not check_iter(var_ls, sentence[1], unitary_dict, measure_dict):
                return False
            if not check_iter(var_ls, sentence[2], unitary_dict, measure_dict):
                return False
        
        else:
            raise Exception("Unknown program structure.")

    # after the examination of all programs in the sequence
    return True
