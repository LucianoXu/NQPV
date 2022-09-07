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
# proof_tactis.py
#
# define the tacits for proof automatic generation
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv import dts
from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm, type_qvarls, val_qvarls
from .opt_pair_term import OptPairTerm, type_opt_pair, val_opt_pair
from . import qpre_term
from .qpre_term import QPreTerm, type_qpre, val_qpre
from .scope_term import ScopeTerm


from .proof_hint_term import AbortHintTerm, IfHintTerm, InitHintTerm, NondetHintTerm, ProofHintTerm, ProofSeqHintTerm, QPreHintTerm, SkipHintTerm, SubproofHintTerm, UnionHintTerm, UnitaryHintTerm, WhileHintTerm, val_proof_hint
from .proof_term import AbortProofTerm, IfProofTerm, InitProofTerm, NondetProofTerm, ProofSeqTerm, ProofSttTerm, ProofTerm, ProofDefinedTerm, QPreProofTerm, SkipProofTerm, SubproofTerm, UnionProofTerm, UnitaryProofTerm, WhileProofTerm


def construct_proof(hint : ProofHintTerm, pre : dts.Term, post : dts.Term, arg_ls : dts.Term, scope : ScopeTerm) -> ProofTerm:
    '''
    construct a proof term from this hint
    '''
    if not isinstance(pre, dts.Term) or not isinstance(post, dts.Term)\
            or not isinstance(arg_ls, dts.Term) or not isinstance(scope, ScopeTerm):
        raise ValueError()
    pre_val = val_qpre(pre)
    post_val = val_qpre(post)

    # need to check whether arg_ls covers the pre and the post
    arg_ls_val = val_qvarls(arg_ls)
    if not arg_ls_val.cover(pre_val.all_qvarls) or \
            not arg_ls_val.cover(post_val.all_qvarls):
        raise RuntimeErrorWithLog("The argument list '" + str(arg_ls) + "' must cover that of the precondition and the postcondition.")

    # calculate the proof statements
    proof_stts = wp_calculus(hint, post_val, scope)

    try:
        QPreTerm.sqsubseteq(pre_val, proof_stts.pre_val, scope)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("The precondition of this proof does not hold.")

    return ProofDefinedTerm(pre, hint, proof_stts, post, arg_ls)

def wp_calculus(hint : ProofHintTerm, post : QPreTerm, scope : ScopeTerm) -> ProofSttTerm:
    '''
    calculate the weakest precondition, of a program given by proof_hint with respect to the post condition
    return a proof statement for this
    '''
    if isinstance(hint, SkipHintTerm):
        return SkipProofTerm(post, post)
        
    elif isinstance(hint, AbortHintTerm):
        post_val = val_qpre(post)
        pre = qpre_term.qpre_I(post_val.all_qvarls, scope)
        return AbortProofTerm(pre, post)

    elif isinstance(hint, InitHintTerm):
        post_val = val_qpre(post)
        pre = qpre_term.qpre_init(post_val, hint.qvarls_val, scope)
        return InitProofTerm(pre, post, hint._qvarls)

    elif isinstance(hint, UnitaryHintTerm):
        post_val = val_qpre(post)        
        pre = qpre_term.qpre_contract(post_val, hint.opt_pair_val.dagger(), scope)
        return UnitaryProofTerm(pre, post, hint._opt_pair)
    
    elif isinstance(hint, IfHintTerm):
        post_val = val_qpre(post)

        if len(post_val.opt_pairs) == 1:            

            P1 = wp_calculus(hint.P1_val, post, scope)
            P0 = wp_calculus(hint.P0_val, post, scope)

            pre = qpre_term.qpre_mea_proj_sum(P0.pre_val, P1.pre_val, hint.opt_pair_val, scope)
            return IfProofTerm(pre, post, hint._opt_pair, P1, P0)

        else:
            # break the set using (Union) rule
            proof_ls : List[ProofSttTerm]= []
            union_pre = QPreTerm(())
            for pair in post_val.opt_pairs:
                pair_val = val_opt_pair(pair)

                P1 = wp_calculus(hint.P1_val, QPreTerm((pair_val,)), scope)
                P0 = wp_calculus(hint.P0_val, QPreTerm((pair_val,)), scope)
                pre = qpre_term.qpre_mea_proj_sum(P0.pre_val, P1.pre_val, hint.opt_pair_val, scope)
                union_pre = union_pre.union(pre)
                proof_ls.append(IfProofTerm(pre, post, hint._opt_pair, P1, P0))
            
            return UnionProofTerm(union_pre, post, tuple(proof_ls))
        
    elif isinstance(hint, WhileHintTerm):
        post_val = val_qpre(post)

        if len(post_val.opt_pairs) == 1:            
            proposed_pre = qpre_term.qpre_mea_proj_sum(post_val, hint.inv_val, hint.opt_pair_val, scope)
            P = wp_calculus(hint.P_val, proposed_pre, scope)
            try:
                QPreTerm.sqsubseteq(hint.inv_val, P.pre_val, scope)
            except:
                raise RuntimeErrorWithLog("The predicate '" + str(hint._inv) + "' is not a valid loop invariant.")  

            return WhileProofTerm(proposed_pre, post, hint._inv, hint._opt_pair, P)
        else:
            # break the set using (Union) rule
            proof_ls : List[ProofSttTerm]= []
            union_pre = QPreTerm(())
            for pair in post_val.opt_pairs:
                pair_val = val_opt_pair(pair)

                proposed_pre = qpre_term.qpre_mea_proj_sum(QPreTerm((pair_val,)), hint.inv_val, hint.opt_pair_val, scope)
                P = wp_calculus(hint.P_val, proposed_pre, scope)
                try:
                    QPreTerm.sqsubseteq(hint.inv_val, P.pre_val, scope)
                except:
                    raise RuntimeErrorWithLog("The predicate '" + str(hint._inv) + "' is not a valid loop invariant.")  

                union_pre = union_pre.union(proposed_pre)
                proof_ls.append(WhileProofTerm(proposed_pre, post, hint._inv, hint._opt_pair, P))
            
            return UnionProofTerm(union_pre, post, tuple(proof_ls))

    elif isinstance(hint, NondetHintTerm):
        proof_stts = []
        pre = QPreTerm(())
        for item in hint._proof_hints:
            item_val = val_proof_hint(item)
            new_proof_stt = wp_calculus(item_val, post, scope)
            proof_stts.append(new_proof_stt)
            pre = pre.union(new_proof_stt.pre_val)
        
        return NondetProofTerm(pre, post, tuple(proof_stts))
    
    elif isinstance(hint, SubproofHintTerm):
        cor = hint.subproof_val.arg_ls_val.get_sub_correspond(hint.arg_ls_val)
        pre_sub = hint.subproof_val.pre_val.qvar_subsitute(cor)
        post_sub = hint.subproof_val.post_val.qvar_subsitute(cor)

        try:
            QPreTerm.sqsubseteq(post_sub, post, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The subproof statement '" + str(hint._subproof) + "' cannot be put here.")
        
        return SubproofTerm(pre_sub, post, hint._subproof, hint._arg_ls)
    
    elif isinstance(hint, QPreHintTerm):
        try:
            QPreTerm.sqsubseteq(hint._qpre, post, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The condition hint '" + str(post) + "' does not hold.")
        
        return QPreProofTerm(hint._qpre, post, hint._qpre)

    elif isinstance(hint, UnionHintTerm):
        proof_stts = []
        pre_cal = QPreTerm(())
        post_cal = QPreTerm(())
        for item in hint._proof_hints:
            try:
                item_val = val_proof_hint(item)
                # different tactics for subproofs and proof hints
                if isinstance(item_val, ProofSeqHintTerm):
                    subhint = item_val.get_proof_hint(len(item_val._proof_hints)-1)
                    if isinstance(subhint, SubproofHintTerm):
                        item_post = subhint.subproof_val.post_val
                    elif isinstance(subhint, QPreHintTerm):
                        item_post = subhint.qpre_val
                    else:
                        raise RuntimeErrorWithLog("The postcondition of proof hint '" + str(item) + "' cannot be automatically deduced.")

                    new_proof_stt = wp_calculus(item_val, item_post, scope)
                    proof_stts.append(new_proof_stt)
                    post_cal = post_cal.union(item_post)
                    pre_cal = pre_cal.union(new_proof_stt.pre_val)

            except RuntimeErrorWithLog:
                raise RuntimeErrorWithLog("The proof '" + str(item) + "' in the union proof does not hold.")
        
        try:
            QPreTerm.sqsubseteq(post_cal, post, scope)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The postcondition and the (Union) proof hint do not fit.")

        return UnionProofTerm(pre_cal, post_cal, tuple(proof_stts))
    
    elif isinstance(hint, ProofSeqHintTerm):
        # backward transformation
        proof_stts : List[ProofSttTerm] = []
        cur_post = post
        for i in range(len(hint._proof_hints)-1, -1, -1):
            item_val = val_proof_hint(hint._proof_hints[i])
            proof_stts.insert(0, wp_calculus(item_val, cur_post, scope))
            cur_post = proof_stts[0].pre_val
        
        return ProofSeqTerm(cur_post, post, tuple(proof_stts))
    
    else:
        raise Exception()
