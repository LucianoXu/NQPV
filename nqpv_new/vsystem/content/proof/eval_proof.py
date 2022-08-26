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
# eval_proof.py
#
# evaluate the program proofs, invocated by the kernel
# ------------------------------------------------------------

from __future__ import annotations
from typing import Any, List, Dict, Tuple

from nqpv_new.vsystem.content.opt import opt_kernel
from nqpv_new.vsystem.syntax.pos_info import PosInfo

from ...var_env import VType, Value, VarEnv
from ...settings import Settings
from ...syntax import ast
from ...log_system import RuntimeErrorWithLog
from ...venv import VEnv

from .proof import QPredicateProof, QProof, QSkipProof, QAbortProof, QInitProof, QSubproof, QUnitaryProof, QIfProof, QWhileProof
from ..predicate.qpredicate import QPredicate, sqsubseteq
from .nondet_proof import QNondetProof

from ..content_tools import opt_qvarls_check

def get_predicate(venv : VEnv, qvar_seq : Tuple[str,...], ast_pre : ast.AstPredicate | ast.AstInv) -> QPredicate:
    '''
    get the predicate
    '''
    pre_pairs = []
    for pair in ast_pre.data:
        opt_qvarls_check(venv, pair[0], "hermitian predicate", pair[1])
        pre_pairs.append((pair[0].id, [id.id for id in pair[1].data]))

    return QPredicate(ast_pre.pos, pre_pairs)


def eval_predicate(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_pre : ast.AstPredicate | ast.AstInv):
    '''
    get the predicate proof
    '''
    try:
        ext = post.full_extension(venv, qvar_seq)
        pre = get_predicate(venv, qvar_seq, ast_pre).full_extension(venv, qvar_seq)

        # check the connectivity
        sqsubseteq(pre, ext, venv)

        pre = QPredicate(PosInfo(), pre.pairs)

        return QPredicateProof(ast_pre.pos, pre, ext)

    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'predicate' proof.", ast_pre.pos)

def eval_skip(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstSkip):
    ext = post.full_extension(venv, qvar_seq)
    pre = QPredicate(PosInfo(), ext.pairs)
    return QSkipProof(ast_stt.pos, pre, ext)

def eval_abort(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstAbort):
    ext = post.full_extension(venv, qvar_seq)
    zero = opt_kernel.eye_tensor(len(qvar_seq))
    zero_name = venv.var_env.auto_name()
    venv.var_env.assign_var(
        zero_name, VType("operator", (len(qvar_seq),)),
        Value(VType("operator", (len(qvar_seq),)), zero)
    )
    pre = QPredicate(PosInfo(), [(zero_name, list(qvar_seq))] )
    return QAbortProof(ast_stt.pos, pre, ext)

def eval_init(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstInit):
    id_ls = [id.id for id in ast_stt.qvar_ls.data]
    ext = post.full_extension(venv, qvar_seq)
    pre_pairs = []
    for pair in ext.pairs:
        new_opt = opt_kernel.hermitian_init(
            qvar_seq, 
            venv.get_var(pair[0]).data,
            tuple(id_ls)
        )
        new_name = venv.var_env.auto_name()
        venv.var_env.assign_var(
            new_name, VType("operator", (len(qvar_seq),)),
            Value(VType("operator", (len(qvar_seq),)), new_opt)
        )
        pre_pairs.append((new_opt, list(qvar_seq)))

    pre = QPredicate(PosInfo(), pre_pairs)
    return QInitProof(ast_stt.pos, pre, ext, id_ls)

def eval_unitary(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstUnitary):
    try:
        id_ls = [id.id for id in ast_stt.qvar_ls.data]
        ext = post.full_extension(venv, qvar_seq)
        opt_qvarls_check(venv, ast_stt.opt, "unitary", ast_stt.qvar_ls)
        pre_pairs = []
        for pair in ext.pairs:
            new_opt = opt_kernel.hermitian_contract(
                qvar_seq,
                venv.get_var(pair[0]).data,
                tuple(id_ls),
                opt_kernel.dagger(venv.get_var(ast_stt.opt.id).data)
            )
            new_name = venv.var_env.auto_name()
            venv.var_env.assign_var(
                new_name, VType("operator", (len(qvar_seq),)),
                Value(VType("operator", (len(qvar_seq),)), new_opt)
            )
            pre_pairs.append((new_opt, list(qvar_seq)))

        pre = QPredicate(PosInfo(), pre_pairs)
        return QUnitaryProof(ast_stt.qvar_ls.pos, pre, ext, id_ls, ast_stt.opt.id)

    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'unitary transform' proof.", ast_stt.pos)
    
def eval_if(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstIfProof):
    try:
        id_ls = [id.id for id in ast_stt.qvar_ls.data]
        ext = post.full_extension(venv, qvar_seq)
        opt_qvarls_check(venv, ast_stt.opt, 'measurement', ast_stt.qvar_ls)

        P1 = eval_proof(venv, qvar_seq, ext, ast_stt.proof1)
        P0 = eval_proof(venv, qvar_seq, ext, ast_stt.proof0)

        pre_pairs = []
        # Note: here we have "set" as postconditions
        for pair1 in P1.pre.pairs:
            for pair0 in P0.pre.pairs:
                
                new_opt = opt_kernel.hermitian_contract(
                    qvar_seq,
                    venv.get_var(pair0[0]).data,
                    tuple(id_ls),
                    venv.get_var(ast_stt.opt.id).data[0]
                ) + opt_kernel.hermitian_contract(
                    qvar_seq,
                    venv.get_var(pair1[0]).data,
                    tuple(id_ls),
                    venv.get_var(ast_stt.opt.id).data[1]
                )

                new_name = venv.var_env.auto_name()
                venv.var_env.assign_var(
                    new_name, VType("operator", (len(qvar_seq),)),
                    Value(VType("operator", (len(qvar_seq),)), new_opt)
                )
                pre_pairs.append((new_opt, list(qvar_seq)))
        
        pre = QPredicate(PosInfo(), pre_pairs)
        return QIfProof(ast_stt.pos, pre, ext, ast_stt.opt.id, id_ls, P1, P0)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'if' proof.", ast_stt.pos)

def eval_while(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstWhileProof):
    try:
        id_ls = [id.id for id in ast_stt.qvar_ls.data]
        ext = post.full_extension(venv, qvar_seq)
        opt_qvarls_check(venv, ast_stt.opt, 'measurement', ast_stt.qvar_ls)


        inv_pre = get_predicate(venv, qvar_seq, ast_stt.inv)

        pre_pairs = []
        # Note: here we have "set" as postconditions
        for pair_inv in inv_pre.pairs:
            for pair_post in ext.pairs:
                
                new_opt = opt_kernel.hermitian_contract(
                    qvar_seq,
                    venv.get_var(pair_post[0]).data,
                    tuple(id_ls),
                    venv.get_var(ast_stt.opt.id).data[0]
                ) + opt_kernel.hermitian_contract(
                    qvar_seq,
                    venv.get_var(pair_inv[0]).data,
                    tuple(id_ls),
                    venv.get_var(ast_stt.opt.id).data[1]
                )

                new_name = venv.var_env.auto_name()
                venv.var_env.assign_var(
                    new_name, VType("operator", (len(qvar_seq),)),
                    Value(VType("operator", (len(qvar_seq),)), new_opt)
                )
                pre_pairs.append((new_opt, list(qvar_seq)))
        
        pre = QPredicate(PosInfo(), pre_pairs)

        # check whether it is a legal loop invariant
        try:
            P = eval_proof(venv, qvar_seq, ext, ast_stt.proof)
            QPredicateProof(PosInfo(), inv_pre, P.pre)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("Invalid loop invariant.")

        return QWhileProof(ast_stt.pos, pre, ext, inv_pre, ast_stt.opt.id, id_ls, P)

    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'while' proof.", ast_stt.pos)

def eval_nondet(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstNondetProof):
    try:
        ext = post.full_extension(venv, qvar_seq)
        subproofs : List[QProof] = []
        for ast_proof in ast_stt.data:
            subproofs.append(eval_proof(venv, qvar_seq, ext, ast_proof))
        
        pre_pairs = []
        for proof in subproofs:
            pre_pairs += proof.pre.pairs
        
        pre = QPredicate(PosInfo(), pre_pairs)
        return QNondetProof(ast_stt.pos, pre, ext, subproofs)

    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'nondeterministic choice' proof.", ast_stt.pos)

def eval_subproof(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate, ast_stt : ast.AstSubproof):
    try:
        ext = post.full_extension(venv, qvar_seq)
        subproof =  venv.get_var(ast_stt.subproof.id)
        if subproof.vtype.type != "proof":
            raise RuntimeErrorWithLog("The variable '" + ast_stt.subproof.id + "' is not a proof.", ast_stt.pos)
        if subproof.get_property("qnum") != len(ast_stt.qvar_ls):
            raise RuntimeErrorWithLog(            
            "The proof '" + str(ast_stt.subproof.id) + "' operates on " + str(subproof.get_property("qnum")) +
            " qubits, while the quantum variable list has " + str(len(ast_stt.qvar_ls)) + " qubits.", ast_stt.subproof.pos
        )
        id_ls = [id.id for id in ast_stt.qvar_ls.data]

        # substitute the variables
        new_subproof_data = subproof.data.substitute(id_ls)
        new_name = venv.var_env.auto_name()
        venv.var_env.assign_var(
            new_name, VType("proof", (len(id_ls),)),
            Value(VType("proof", (len(id_ls),)), new_subproof_data)
        )
        new_subproof = venv.get_var(new_name)

        # check whether this subproof can be put in here
        try:
            sub_ext = new_subproof.data.post.full_extension(venv, qvar_seq)
            sub_pre = new_subproof.data.pre.full_extension(venv, qvar_seq)
            eval_predicate(venv, qvar_seq, sub_pre, sub_ext)
        except RuntimeErrorWithLog:
            raise RuntimeErrorWithLog("The proof '" + str(new_subproof) + "' can not be connected.", new_subproof.data.pos)


        return QSubproof(ast_stt.pos, new_subproof.data.pre, ext, ast_stt.subproof.id, id_ls)
    except RuntimeErrorWithLog:
        raise RuntimeErrorWithLog("Invalid 'subprogram' statement.", ast_stt.pos)

eval_dict = {
    ast.AstSkip : eval_skip,
    ast.AstAbort : eval_abort,
    ast.AstInit : eval_init,
    ast.AstUnitary : eval_unitary,
    ast.AstIfProof : eval_if,
    ast.AstWhileProof : eval_while,
    ast.AstNondetProof : eval_nondet,
    ast.AstSubproof : eval_subproof,
    ast.AstPredicate : eval_predicate,
}

def eval_proof(venv : VEnv, qvar_seq : Tuple[str,...], post : QPredicate | None, ast_proof : ast.AstProof) -> QProof:
    '''
    check the proof construction (in the backward direction)
    qvar_seq : the quantum var sequence in use
    post : None means the post condition is provided
    '''
    if post is None:
        if isinstance(ast_proof.data[-1], ast.AstPredicate):
            post = get_predicate(venv, qvar_seq, ast_proof.data[-1])
        else:
            raise Exception("unexpected situation")

    r = QProof(ast_proof.pos, post, post, [])

    for i in range(len(ast_proof.data)-1, -1, -1):
        proof_stt = ast_proof.data[i]

        if type(proof_stt) in eval_dict:
            cur_proof = eval_dict[type(proof_stt)](venv, qvar_seq, r.pre, proof_stt)  # type: ignore                

            # backward transformation
            r.statements.insert(0, cur_proof)
            r.pre = cur_proof.pre
        else:
            raise Exception("unexpected situation")
        
    return r
