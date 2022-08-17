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
# NQPV_opt.py
#
# provides methods to create and verify 
# ------------------------------------------------------------

import numpy as np
from . import NQPV_la

# transform m to the (2,2,2,...) form
def to_shape_2(m):
    # check whether m already satisfies the requirements
    flag = True
    for dim in m.shape:
        if dim != 2:
            flag = False
            break
    if flag:
        return m
    
    if len(m.shape) == 2:
        if m.shape[0] != m.shape[1]:
            return None
        qubitn = int(np.log2(m.shape[0]))
        if m.shape[0] != 2**qubitn:
            return None
        return m.reshape((2,) * qubitn * 2)

    else:
        return None

# transform m to the (2,2,2,...) form (for measurements)
def to_shape_3(m):
    # check whether m already satisfies the requirements
    flag = True
    for dim in m.shape:
        if dim != 2:
            flag = False
            break
    if flag:
        return m
    
    if len(m.shape) == 3:
        if m.shape[1] != m.shape[2]:
            return None
        qubitn = int(np.log2(m.shape[1]))
        if m.shape[1] != 2**qubitn:
            return None
        return m.reshape((2,) * (qubitn * 2 + 1))

    else:
        return None


def save_unitary(path, id, unitary):
    m = to_shape_2(unitary)
    if m is None:
        print("The shape of the given tensor is invalid.")
        return False
    
    if not NQPV_la.check_unity(m, id):
        print("The given tensor is not unitary.")
        return False
    
    if path[-1] == '/' or path[-1] == '\\':
        path = path[:-1]
    
    np.save(path + "/" + id + ".npy", m)
    return True

def save_hermitian(path, id, herm):
    m = to_shape_2(herm)
    if m is None:
        print("The shape of the given tensor is invalid.")
        return False
    
    if not NQPV_la.check_hermitian_predicate(m, id):
        print("The given tensor is not a valid Hermitian predicate.")
        return False
    
    if path[-1] == '/' or path[-1] == '\\':
        path = path[:-1]
    
    np.save(path + "/" + id + ".npy", m)
    return True

def save_measurement(path, id, measure):
    m = to_shape_3(measure)
    if m is None:
        print("The shape of the given tensor is invalid.")
        return False
    
    if not NQPV_la.check_measure(m, id):
        print("The given tensor is not a valid measurement.")
        return False
    
    if path[-1] == '/' or path[-1] == '\\':
        path = path[:-1]
    
    np.save(path + "/" + id + ".npy", m)
    return True

