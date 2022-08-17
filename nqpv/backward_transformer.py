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
# backward_transformer.py
#
# backward_transformer for nondeterministic quantum programs
# it calculates the weakest (liberal) precondition of a given program abstract syntax tree
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict

from .logsystem import LogSystem

from .NQPV_ast import *
from . import NQPV_la
from .set_order import sqsubseteq

# report channel
channel : str = "main"

def wlp_verify(prog : dict, pinfo : dict, preserve_pre) -> bool:
    '''
    calculates the weakest liberal precondition
    prog: the given abstract syntax tree
    pinfo: information about the program (operators and so on)
    preserve_pre: whether to preserve intermediate preconditions
    return: the weakest liberal precondition (a set of hermitian operators)
    '''
    qvar = prog['qvar']

    # prepare the hermitian operators
    input_post = [NQPV_la.hermitian_extend(qvar, pinfo['herm'][tuple[0]], tuple[1]) for tuple in prog['post-cond']]
    input_pre = [NQPV_la.hermitian_extend(qvar, pinfo['herm'][tuple[0]], tuple[1]) for tuple in prog['pre-cond']]

    # add the information for intermediate preconditions
    if preserve_pre:
        pinfo['im_pre-cond'] = {}
        pinfo['im_pre-cond-no'] = 0

    calculated_pre = wlp_iter(prog['sequence'], prog['qvar'], input_post, pinfo, preserve_pre)

    if calculated_pre is not None:
        if sqsubseteq(input_pre, calculated_pre):
            return True
    
    return False

def insert_im_precond(pinfo: dict, pre_m_ls : list):
    '''
    pre_m_ls: preconditions to be inserted
    return the newly created identifiers
    '''
    new_id_ls = []
    for pre in pre_m_ls:
        # create a valid id
        lb = 'PRE'+str(pinfo['im_pre-cond-no'])
        while lb in pinfo['unitary'] or \
            lb in pinfo['measure'] or \
            lb in pinfo['herm'] or\
            lb in pinfo['im_pre-cond']:

            pinfo['im_pre-cond-no'] += 1
            lb = 'PRE'+str(pinfo['im_pre-cond-no'])
        
        pinfo['im_pre-cond'][lb] = pre
        new_id_ls.append(lb)

    return new_id_ls
    


def wlp_iter(sequence: list, qvar: list, postcond: list, pinfo: dict, preserve_pre) -> None | List:
    '''
    input:
        sequence: sequence of program sentences
        qvar: list of all quantum variables
        postcond: the post condition, in the cylinder extension form
        preserve_pre: whether to preserve intermediate preconditions
    output:
        weakest liberal precondition, the result
    '''
    global error_info, silent

    cur_postcond = postcond
    # transform in the reverse order
    for i in range(len(sequence)-1, -1, -1):

        sentence = sequence[i]
        if sentence.label == 'SKIP':
            pass

        elif sentence.label == 'ABORT':
            cur_postcond = [NQPV_la.eye_tensor(len(qvar))]

        elif sentence.label == 'INIT':
            cur_postcond = [NQPV_la.hermitian_init(qvar, H, sentence.vls)
                            for H in cur_postcond]

        elif sentence.label == 'UNITARY':
            Ud = NQPV_la.dagger(pinfo['unitary'][sentence.unitary])
            cur_postcond = [NQPV_la.hermitian_contract(qvar, H, sentence.vls, Ud)
                            for H in cur_postcond]

        elif sentence.label == 'IF':
            temp = []
            for H in cur_postcond:
                # then - subclause
                pre1 = wlp_iter(sentence.S1, qvar, [H], pinfo, preserve_pre)
                if pre1 is None:
                    return None
                # else - subclause
                pre0 = wlp_iter(sentence.S0, qvar, [H], pinfo, preserve_pre)
                if pre0 is None:
                    return None

                for H0 in pre0:
                    for H1 in pre1:
                        temp.append(
                            NQPV_la.hermitian_contract(qvar, H0, sentence.measure_vls,
                             pinfo['measure'][sentence.measure][0]) + 
                            NQPV_la.hermitian_contract(qvar, H1, sentence.measure_vls,
                             pinfo['measure'][sentence.measure][1])
                        )

            cur_postcond = temp
        
        elif sentence.label == 'WHILE':
            # Note: in this step, the weakest liberal precondition is partially determined by the given invariant
            temp = []

            #prepare the hermitian operators
            inv = [NQPV_la.hermitian_extend(qvar, pinfo['herm'][tuple[0]], tuple[1]) for tuple in sentence.inv]

            for H in cur_postcond:
                proposed_pre = []
                # check whether it is a valid invariant
                for Hinv in inv:
                    proposed_pre.append(
                        NQPV_la.hermitian_contract(qvar, H, sentence.measure_vls,
                         pinfo['measure'][sentence.measure][0]) +
                        NQPV_la.hermitian_contract(qvar, Hinv, sentence.measure_vls,
                         pinfo['measure'][sentence.measure][1])
                    )
                calculated_pre = wlp_iter(sentence.S, qvar, proposed_pre, pinfo, preserve_pre)
                if calculated_pre is None:
                    return None

                if sqsubseteq(inv, calculated_pre):
                    temp += proposed_pre
                else:
                    LogSystem.channels[channel].append("(line "+str(sentence.lineno)+")\tFailure: The given invariant '" + predicate_to_code(sentence.inv) + "' is invalid.\n")
                    return None

            cur_postcond = temp

        
        elif sentence.label == 'NONDET_CHOICE':
            next_cur_postcond = []
            for sub_sequence in sentence.S_ls:
                pre = wlp_iter(sub_sequence, qvar, cur_postcond, pinfo, preserve_pre)
                if pre is None:
                    return None
                next_cur_postcond = next_cur_postcond + pre
            cur_postcond = next_cur_postcond

        else:
            raise Exception("Unknown program structure.")
        
        if preserve_pre:
            sentence.pre_cond = insert_im_precond(pinfo, cur_postcond)


    return cur_postcond
