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

from nqpv.vsystem.log_system import RuntimeErrorWithLog

from .qvarls_term import QvarlsTerm
from .opt_pair_term import OptPairTerm
from . import qpre_term
from .qpre_term import QPreTerm
from ..var_scope import VarScope


from .proof_hint_term import AbortHintTerm, IfHintTerm, InitHintTerm, NondetHintTerm, ProofHintTerm, ProofSeqHintTerm, QPreHintTerm, SkipHintTerm, UnionHintTerm, UnitaryHintTerm, WhileHintTerm
from .proof_term import AbortProofTerm, IfProofTerm, InitProofTerm, NondetProofTerm, ProofSeqTerm, ProofSttTerm, ProofDefinedTerm, QPreProofTerm, SkipProofTerm, UnionProofTerm, UnitaryProofTerm, WhileProofTerm


def construct_proof(hint : ProofHintTerm, pre : QPreTerm, post : QPreTerm, 
                    arg_ls : QvarlsTerm, scope : VarScope) -> ProofDefinedTerm:
    '''
    construct a proof term from this hint
    '''
    if not isinstance(pre, QPreTerm) or not isinstance(post, QPreTerm)\
            or not isinstance(arg_ls, QvarlsTerm) or not isinstance(scope, VarScope):
        raise ValueError()

    # need to check whether arg_ls covers the pre and the post
    arg_ls_val = arg_ls
    if not arg_ls_val.cover(pre.all_qvarls) or \
            not arg_ls_val.cover(post.all_qvarls):
        raise RuntimeErrorWithLog("The argument list '" + str(arg_ls) + "' must cover that of the precondition and the postcondition.")

    # calculate the proof statements
    proof_stts = wp_calculus(hint, post, scope)

    try:
        QPreTerm.sqsubseteq(pre, proof_stts.pre, scope)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("The precondition of this proof does not hold.")

    return ProofDefinedTerm(pre, hint, proof_stts, post, arg_ls)

def wp_calculus(hint : ProofHintTerm, post : QPreTerm, scope : VarScope) -> ProofSttTerm:
    '''
    calculate the weakest precondition, of a program given by proof_hint with respect to the post condition
    return a proof statement for this
    '''
    scope.report("wp calculus : " + str(hint.label))
    scope.report("{ ? }")
    scope.report(str(hint))
    scope.report(str(post) + "\n")
    
    if isinstance(hint, SkipHintTerm):
        return SkipProofTerm(post, post)
        
    elif isinstance(hint, AbortHintTerm):
        pre = qpre_term.qpre_I(post.all_qvarls, scope)
        return AbortProofTerm(pre, post)

    elif isinstance(hint, InitHintTerm):
        pre = qpre_term.qpre_init(post, hint.qvarls, scope)
        return InitProofTerm(pre, post, hint._qvarls)

    elif isinstance(hint, UnitaryHintTerm):
        pre = qpre_term.qpre_contract(post, hint.opt_pair.dagger(), scope)
        return UnitaryProofTerm(pre, post, hint._opt_pair)
    
    elif isinstance(hint, IfHintTerm):
        if len(post.opt_pairs) == 1:            

            P1 = wp_calculus(hint.P1_val, post, scope)
            P0 = wp_calculus(hint.P0_val, post, scope)

            pre = qpre_term.qpre_mea_proj_sum(P0.pre, P1.pre, hint.opt_pair, scope)
            return IfProofTerm(pre, post, hint._opt_pair, P1, P0)

        else:
            # break the set using (Union) rule
            proof_ls : List[ProofSttTerm]= []
            union_pre = QPreTerm(())
            for pair in post.opt_pairs:
                this_post = QPreTerm((pair,))

                P1 = wp_calculus(hint.P1_val, this_post, scope)
                P0 = wp_calculus(hint.P0_val, this_post, scope)
                this_pre = qpre_term.qpre_mea_proj_sum(P0.pre, P1.pre, hint.opt_pair, scope)
                union_pre = union_pre.union(this_pre)
                proof_ls.append(IfProofTerm(this_pre, this_post, hint._opt_pair, P1, P0))
            
            return UnionProofTerm(union_pre, post, tuple(proof_ls))
        
    elif isinstance(hint, WhileHintTerm):

        if len(post.opt_pairs) == 1:            
            proposed_pre = qpre_term.qpre_mea_proj_sum(post, hint.inv, hint.opt_pair, scope)
            P = wp_calculus(hint.P, proposed_pre, scope)
            try:
                QPreTerm.sqsubseteq(hint.inv, P.pre, scope)
            except:
                raise RuntimeErrorWithLog("The predicate '" + str(hint._inv) + "' is not a valid loop invariant.")  

            return WhileProofTerm(proposed_pre, post, hint._inv, hint._opt_pair, P)
        else:
            # break the set using (Union) rule
            proof_ls : List[ProofSttTerm]= []
            union_pre = QPreTerm(())
            for pair in post.opt_pairs:
                this_post = QPreTerm((pair,))

                proposed_pre = qpre_term.qpre_mea_proj_sum(this_post, hint.inv, hint.opt_pair, scope)
                P = wp_calculus(hint.P, proposed_pre, scope)
                try:
                    QPreTerm.sqsubseteq(hint.inv, P.pre, scope)
                except:
                    raise RuntimeErrorWithLog("The predicate '" + str(hint._inv) + "' is not a valid loop invariant.")  

                union_pre = union_pre.union(proposed_pre)
                proof_ls.append(WhileProofTerm(proposed_pre, this_post, hint._inv, hint._opt_pair, P))
            
            return UnionProofTerm(union_pre, post, tuple(proof_ls))

    elif isinstance(hint, NondetHintTerm):
        proof_stts = []
        pre = QPreTerm(())
        for item in hint._proof_hints:
            new_proof_stt = wp_calculus(item, post, scope)
            proof_stts.append(new_proof_stt)
            pre = pre.union(new_proof_stt.pre)
        
        return NondetProofTerm(pre, post, tuple(proof_stts))
    
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
                # different tactics for subproofs and proof hints
                if isinstance(item, ProofSeqHintTerm):
                    subhint = item.get_proof_hint(len(item._proof_hints)-1)
                    if isinstance(subhint, QPreHintTerm):
                        item_post = subhint.qpre
                    else:
                        raise RuntimeErrorWithLog("The postcondition of proof hint '" + str(item) + "' cannot be automatically deduced.")

                    new_proof_stt = wp_calculus(item, item_post, scope)
                    proof_stts.append(new_proof_stt)
                    post_cal = post_cal.union(item_post)
                    pre_cal = pre_cal.union(new_proof_stt.pre)

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
            item = hint._proof_hints[i]
            proof_stts.insert(0, wp_calculus(item, cur_post, scope))
            cur_post = proof_stts[0].pre
        
        return ProofSeqTerm(cur_post, post, tuple(proof_stts))
    
    else:
        raise Exception()
