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

import numpy as np
import NQPV_la

#check whether the variables in check_ls are predefined in var_ls
def check_variable(var_ls : list, check_ls : list):
    for var in check_ls:
        if var not in var_ls:
            print("variable '" + var + "' not defined in qvar.")
            return False
    return True

def check_unitary(id, unitary_dict, var_ls):
    if id in unitary_dict:
        pass
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

    # check the dimension informaion
    if (len(var_ls) * 2 == len(unitary_dict[id].shape)):
        return True
    else:
        print("The dimensions of unitary '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False



def check_measure(id, measure_dict, var_ls):
    if id in measure_dict:
        pass
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

    # check the dimension information
    # + 1 is for the extra dimension of 0-result and 1-result
    if (len(var_ls) * 2 + 1 == len(measure_dict[id].shape)):
        return True
    else:
        print("The dimensions of measurement '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False


def check_hermitian(id, herm_dict, var_ls):
    # check whether the hermitian is suitable

    if id in herm_dict:
        pass
    else:
        try:
            loaded = np.load("./" + id + ".npy")
        except:
            print("hermitian operator '" + id +".npy' not found")
            return False

        # check for valid unitary
        if not NQPV_la.check_hermitian_predicate(loaded, id):
            return False

        herm_dict[id] = loaded

    # check the dimension informaion
    if (len(var_ls) * 2 == len(herm_dict[id].shape)):
        return True
    else:
        print("The dimensions of hermitian '" + id + "' and qvars " + str(var_ls) + " do not match.")
        return False


# check the semantics of prog. load and return the operators
def check(prog : dict):
    if prog == None:
        print("The input abstract syntax tree is invalid.")
        return None

    unitary_dict = {}
    measure_dict = {}
    herm_dict = {}
    
    # check the pre-condition and post-condition
    for herm_tuple in prog['pre-cond']:
        if not check_variable(prog['qvar'], herm_tuple[1]):
            return False
        if not check_hermitian(herm_tuple[0], herm_dict, herm_tuple[1]):
            return False
    for herm_tuple in prog['post-cond']:
        if not check_variable(prog['qvar'], herm_tuple[1]):
            return False
        if not check_hermitian(herm_tuple[0], herm_dict, herm_tuple[1]):
            return False

    if check_iter(prog['qvar'], prog['sequence'], unitary_dict, measure_dict, herm_dict) :
        return (unitary_dict, measure_dict)
    else:
        return None
    

def check_iter(var_ls : list, sequence : list, unitary_dict : dict, measure_dict : dict, herm_dict : dict):
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
            # check the unitary
            if not check_unitary(sentence[2], unitary_dict, sentence[1]):
                return False

        elif sentence[0] == 'IF':
            # check the variables
            if not check_variable(var_ls, sentence[2]):
                return False
            # check the measure existence
            if not check_measure(sentence[1], measure_dict, sentence[2]):
                return False
            # check the two subprograms
            if not check_iter(var_ls, sentence[3], unitary_dict, measure_dict, herm_dict):
                return False
            if not check_iter(var_ls, sentence[4], unitary_dict, measure_dict, herm_dict):
                return False
        
        elif sentence[0] == 'WHILE':
            # check the hermitian operators
            for herm_tuple in sentence[1]:
                if not check_variable(var_ls, herm_tuple[1]):
                    return False
                if not check_hermitian(herm_tuple[0], herm_dict, herm_tuple[1]):
                    return False
            # check the variables
            if not check_variable(var_ls, sentence[3]):
                return False
            # check the measure existence
            if not check_measure(sentence[2], measure_dict, sentence[3]):
                return False
            # check the subprogram
            if not check_iter(var_ls, sentence[4], unitary_dict, measure_dict, herm_dict):
                return False
        
        elif sentence[0] == 'NONDET_CHOICE':
            # check the two subprograms
            if not check_iter(var_ls, sentence[1], unitary_dict, measure_dict, herm_dict):
                return False
            if not check_iter(var_ls, sentence[2], unitary_dict, measure_dict, herm_dict):
                return False
        
        else:
            raise Exception("Unknown program structure.")

    # after the examination of all programs in the sequence
    return True
