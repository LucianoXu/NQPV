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
# opt_kernel.py
#
# quantum linear algebra tools needed in this verifier
# ------------------------------------------------------------
from __future__ import annotations
from typing import Any, List, Tuple

import numpy as np


from ..log_system import LogSystem

# the class to set the precision
class Precision:
    _EPS : float = 1e-7
    _SDP_precision : float = 1e-9

    @staticmethod
    def EPS() -> float:
        return Precision._EPS

    @staticmethod
    def SDP_precision() -> float:
        return Precision._SDP_precision

    @staticmethod
    def set_EPS(eps : float) -> None:
        if eps <= 0.:
            raise Exception("illegal machine precision.")
        Precision._EPS = eps

    @staticmethod
    def set_SDP_precision(precision : float) -> None:
        if precision <= 0.:
            raise Exception("illegal machine precision.")
        Precision._SDP_prercision = precision
    

def np_eps_equal(a : np.ndarray, b : np.ndarray) -> bool:
    '''
    check whether two tensors a and b are equal, according to maximum norm.
    '''
    if a.shape != b.shape :
        return False

    diff = np.max(np_complex_norm(a - b))  # type: ignore
    return diff < Precision.EPS()

def np_complex_norm(m : np.ndarray) -> np.ndarray:
    '''
    calculate the element wise norm
    '''
    return np.sqrt(m.real * m.real + m.imag * m.imag)


def check_unity(m : np.ndarray) -> bool:
    '''
    check whether tensor m is unitary
    m: tensor of shape (2,2,...,2), with the row indices in front of the column indices
    '''

    if len(m.shape) % 2 == 1:
        #LogSystem.channels["error"].append("The dimension is invalid for an unitary operator.")
        return False

    for dim in m.shape:
        if dim != 2:
            #LogSystem.channels["error"].append("The dimension is invalid for an unitary operator.")
            return False
    
    # calculate the dim for matrix
    dim_m : int = 2**(len(m.shape)//2)
    matrix = m.reshape((dim_m, dim_m))

    # check the equality of U^dagger @ U and I

    if not np_eps_equal(matrix @ np.transpose(np.conj(matrix)), np.eye(dim_m)):
        #LogSystem.channels["error"].append("The operator is not unitary.")
        return False
    return True


def check_hermitian_predicate(m : np.ndarray) -> bool:
    '''
    check whether tensor m is hermitian and 0 <= m <= I
    m: tensor of shape (2,2,...,2), with the row indices in front of the column indices
    '''

    if len(m.shape) % 2 == 1:
        #LogSystem.channels["error"].append("The dimension is invalid for an Hermitian predicate.")
        return False

    for dim in m.shape:
        if dim != 2:
            #LogSystem.channels["error"].append("The dimension is invalid for an Hermitian predicate.")
            return False
    
    # calculate the dim for matrix
    dim_m = 2**(len(m.shape)//2)
    matrix = m.reshape((dim_m, dim_m))

    # check the equivalence of U^dagger @ U and I
    if not np_eps_equal(matrix, np.transpose(np.conj(matrix))):
        #LogSystem.channels["error"].append("The operator is not a Hermitian operator.")
        return False

    # check 0 <= matrix <= I
    e_vals = np.linalg.eigvals(matrix)
    if np.any(e_vals < 0 - Precision.EPS()) or np.any(e_vals > 1 + Precision.EPS()):
        #LogSystem.channels["error"].append("The requirement 0 <= Predicate <= I is not satisfied.")
        return False
        
    return True


def check_measure(m : np.ndarray) -> bool:
    '''
    check whether tensor m is a valid measurement
    m: tensor of shape (2,2,...,2), with the row indices in front of the column indices. 
        The first index of m corresponds to measurement result 0 or 1.
    '''
        
    if len(m.shape) % 2 == 0:
        #LogSystem.channels["error"].append("The dimension is invalid for a measurement set.")
        return False

    for dim in m.shape:
        if dim != 2:
            #LogSystem.channels["error"].append("The dimension is invalid for a measurement set.")
            return False
    
    # calculate the dim for matrix
    dim_m = 2**((len(m.shape)-1)//2)

    # pick out M0 and M1
    m0 = m[0].reshape((dim_m, dim_m))
    m1 = m[1].reshape((dim_m, dim_m))

    # check the equivalence of U^dagger @ U and I
    if not np_eps_equal(m0.conj().transpose() @ m0 + m1.conj().transpose() @ m1, np.eye(dim_m)):
        #LogSystem.channels["error"].append("This tensor does not satisfy the normalization requirement of a measurement set.")
        return False
    return True

def eye_tensor(qubitn : int) -> np.ndarray:
    '''
    return the identity matrix of 'qubitn' qubits, in the form of a (2,2,2,...) tensor, row indices in the front.
    '''
    return np.eye(2**qubitn).reshape((2,)*qubitn*2)

def dagger(M : np.ndarray) -> np.ndarray:
    '''
    for a tensor M with shape (2,2,2,...), return M^dagger
    Note: M should have been already checked
    '''
    nM = len(M.shape)//2
    trans = list(range(nM, nM*2)) + list(range(0, nM))
    return np.conjugate(M).transpose(trans)

################################### operation with qvars
def hermitian_contract(qvar: Tuple[str,...], H : np.ndarray, qvar_act : Tuple[str,...], M : np.ndarray) -> np.ndarray:
    '''
    conduct the transformation M.H.M^dagger and return the result hermitian operator
    qvar: name sequence of qubits in H
    qvar_act: name sequence of qubits in M

    Note: the operators H and M should have been checked already

    [index sequence of tensor H (and M)]

            qvar == [q1, q2, q3, ... , qn]

              n  n+1 n+2 n+3     2n-2 2n-1
              |   |   |   |  ...  |   |
             ---------------------------
            | q1  q2  q3     ...      qn|
             ---------------------------
              |   |   |   |  ...  |   |
              0   1   2   3      n-2 n-1

    '''
    nH = len(qvar)
    nM = len(qvar_act)
    # decide the indices for contraction. note that M^dagger is accessed by its conjugate and the same index list iM_ls
    iM_ls = list(range(nM, 2*nM))
    iH_left_ls = [qvar.index(v) for v in qvar_act]
    iH_right_ls = [i + nH for i in iH_left_ls]

    # decide the rearrangements, since the standard rearrangement is not what we want
    count_rem_MH = 0
    count_rem_HMd = nH
    rearrange_MH = []
    rearrange_HMd = []
    for i in range(nH):
        if i in iH_left_ls:
            rearrange_MH.append(2*nH-nM + qvar_act.index(qvar[i]))
        else:
            rearrange_MH.append(count_rem_MH)
            count_rem_MH += 1
        if i + nH in iH_right_ls:
            rearrange_HMd.append(2*nH-nM + qvar_act.index(qvar[i - nH]))
        else:
            rearrange_HMd.append(count_rem_HMd)
            count_rem_HMd += 1

    rearrange_MH = rearrange_MH + list(range(nH - nM, 2*nH - nM))
    rearrange_HMd = list(range(nH)) + rearrange_HMd

    # conduct the contraction and rearrange the indices
    temp1 = np.tensordot(H, M, (iH_left_ls, iM_ls)).transpose(rearrange_MH)
    temp2 = np.tensordot(temp1, np.conjugate(M), (iH_right_ls, iM_ls)).transpose(rearrange_HMd)
    return temp2    

def hermitian_init(qvar: Tuple[str,...], H : np.ndarray, qvar_init: Tuple[str,...]) -> np.ndarray:
    '''
    initialize hermitian operator H at variables 'qvar_init'
    '''
    P0 = np.array([[1., 0.],
                    [0., 0.]])
    P1 = np.array([[0., 0.],
                    [1., 0.]])
    # initialize all the variables in order
    tempH = H
    for var in qvar_init:
        a = hermitian_contract(qvar, tempH, (var,), P0)
        b = hermitian_contract(qvar, tempH, (var,), P1)
        tempH = a + b
    
    return tempH

def tensor_to_matrix(t : np.ndarray) -> np.ndarray:
    nM = len(t.shape)//2
    ndim = 2**nM
    return t.reshape((ndim, ndim))


def hermitian_extend(qvar: Tuple[str,...], H : np.ndarray, qvar_H: Tuple[str,...]) -> np.ndarray:
    '''
    extend the given hermitian operator, according to all variables qvar, and return
    '''
    nAll = len(qvar)
    nH = len(qvar_H)
    m_I = eye_tensor(nAll - nH)

    temp = np.tensordot(H, m_I, ([],[]))

    # rearrange the indices
    count_ext = 0
    r_left = []
    r_right = []
    for i in range(nAll):
        if qvar[i] in qvar_H:
            pos = qvar_H.index(qvar[i])
            r_left.append(pos)
            r_right.append(nH + pos)
        else:
            r_left.append(2*nH + count_ext)
            r_right.append(nAll + nH + count_ext)
            count_ext += 1
    
    return temp.transpose(r_left + r_right)


def get_opt_qnum(m : np.ndarray) -> int:
    if not isinstance(m, np.ndarray):
        raise Exception("unexpected situation")
    
    for dim in m.shape:
        if dim != 2:
            raise Exception("unexpected situation")

    if len(m.shape) % 2 == 1:
        return (len(m.shape) - 1)//2
    else:
        return len(m.shape)//2
