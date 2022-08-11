# ------------------------------------------------------------
# backward_transformer.py
#
# backward_transformer for nondeterministic quantum programs
# it calculates the weakest (liberal) precondition of a given program abstract syntax tree
# ------------------------------------------------------------

import NQPV_la
from set_order import sqsubseteq

def wlp_verify(prog : dict, operators : dict):
    '''
    calculates the weakest liberal precondition
    prog: the given abstract syntax tree
    return: the weakest liberal precondition (a set of hermitian operators)
    '''
    qvar = prog['qvar']

    #prepare the hermitian operators
    input_post = [NQPV_la.hermitian_extend(qvar, operators['herm'][tuple[0]], tuple[1]) for tuple in prog['post-cond']]
    input_pre = [NQPV_la.hermitian_extend(qvar, operators['herm'][tuple[0]], tuple[1]) for tuple in prog['pre-cond']]

    calculated_pre = wlp_iter(prog['sequence'], prog['qvar'], input_post, operators)

    if calculated_pre is not None:
        if sqsubseteq(input_pre, calculated_pre):
            print("Partial Correctness Verified.")
            return True
    
    print("Partial Correctness Verification fails.")
    return False

def wlp_iter(sequence: list, qvar: list, postcond: list, operators: dict):
    '''
    input:
        sequence: sequence of program sentences
        qvar: list of all quantum variables
        postcond: the post condition, in the cylinder extension form
    output:
        weakest liberal precondition, the result
    '''
    cur_postcond = postcond
    # transform in the reverse order
    for i in range(len(sequence)-1, -1, -1):
        sentence = sequence[i]
        if sentence[0] == 'SKIP':
            pass

        elif sentence[0] == 'ABORT':
            cur_postcond = [NQPV_la.eye_tensor(len(qvar))]

        elif sentence[0] == 'INIT':
            cur_postcond = [NQPV_la.hermitian_init(qvar, H, sentence[1])
                            for H in cur_postcond]

        elif sentence[0] == 'UNITARY':
            Ud = NQPV_la.dagger(operators['unitary'][sentence[2]])
            cur_postcond = [NQPV_la.hermitian_contract(qvar, H, sentence[1], Ud)
                            for H in cur_postcond]

        elif sentence[0] == 'IF':
            temp = []
            for H in cur_postcond:
                pre0 = wlp_iter(sentence[3], qvar, [H], operators)
                if pre0 is None:
                    return None
                pre1 = wlp_iter(sentence[4], qvar, [H], operators)
                if pre1 is None:
                    return None

                for H0 in pre0:
                    for H1 in pre1:
                        temp.append(
                            NQPV_la.hermitian_contract(qvar, H0, sentence[2],
                             operators['measure'][sentence[1]][0]) + 
                            NQPV_la.hermitian_contract(qvar, H1, sentence[2],
                             operators['measure'][sentence[1]][1])
                        )

            cur_postcond = temp
        
        elif sentence[0] == 'WHILE':
            # Note: in this step, the weakest liberal precondition is partially determined by the given invariant
            temp = []

            #prepare the hermitian operators
            inv = [NQPV_la.hermitian_extend(qvar, operators['herm'][tuple[0]], tuple[1]) for tuple in sentence[1]]

            for H in cur_postcond:
                proposed_pre = []
                # check whether it is a valid invariant
                for Hinv in inv:
                    proposed_pre.append(
                        NQPV_la.hermitian_contract(qvar, H, sentence[3],
                         operators['measure'][sentence[2]][0]) +
                        NQPV_la.hermitian_contract(qvar, Hinv, sentence[3],
                         operators['measure'][sentence[2]][1])
                    )
                calculated_pre = wlp_iter(sentence[4], qvar, proposed_pre, operators)
                if sqsubseteq(inv, proposed_pre):
                    temp += proposed_pre
                else:
                    print("The given invariant '" + str(sentence[1]) + "' is invalid.")
                    return None

            cur_postcond = temp

        
        elif sentence[0] == 'NONDET_CHOICE':
            pre0 = wlp_iter(sentence[1], qvar, cur_postcond, operators)
            if pre0 is None:
                return None
            pre1 = wlp_iter(sentence[2], qvar, cur_postcond, operators)
            if pre1 is None:
                return None
            cur_postcond = pre0 + pre1

        else:
            raise Exception("Unknown program structure.")

    return cur_postcond
