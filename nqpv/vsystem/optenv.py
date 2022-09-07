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
# optenv_inject.py
#
# inject the commonly used unitary gates and measurements
# load the tensors in the run path folder
# ------------------------------------------------------------

import os
from nqpv import dts

from nqpv.vsystem.content.opt_kernel import get_opt_qnum

from .log_system import LogSystem, RuntimeErrorWithLog
from .content.opt_term import type_operator
from .content.scope_term import ScopeTerm
from .content.opt_term import OperatorTerm

import numpy as np

# the operation library
optlib = {
    # unitary
    "I" : np.array(
        [[1., 0.],
        [0., 1.]]
    ),
    
    "X" : np.array(
        [[0., 1.],
        [1., 0.]]
    ),

    "Y" : np.array(
        [[0., -1.j],
        [1.j, 0.]]
    ),

    "Z" : np.array(
        [[1., 0.],
        [0., -1.]]
    ),

    "H" : np.array(
        [[1., 1.],
        [1., -1.]]
    )/np.sqrt(2),

    "CX" : np.array(
        [[1., 0., 0., 0.],
        [0., 1., 0., 0.],
        [0., 0., 0., 1.],
        [0., 0., 1., 0.]]
    ).reshape((2,2,2,2)),

    "CH" : np.array(
        [[1., 0., 0., 0.],
        [0., 1., 0., 0.,],
        [0., 0., 1./np.sqrt(2), 1./np.sqrt(2)],
        [0., 0., 1./np.sqrt(2), -1./np.sqrt(2)]]
    ).reshape((2,2,2,2)),

    "SWAP" : np.array(
        [[1., 0., 0., 0.],
        [0., 0., 1., 0.],
        [0., 1., 0., 0.],
        [0., 0., 0., 1.]]
    ).reshape((2,2,2,2)),

    "CCX" : np.array(
        [[1., 0., 0., 0., 0., 0., 0., 0.],
        [0., 1., 0., 0., 0., 0., 0., 0.],
        [0., 0., 1., 0., 0., 0., 0., 0.],
        [0., 0., 0., 1., 0., 0., 0., 0.],
        [0., 0., 0., 0., 1., 0., 0., 0.],
        [0., 0., 0., 0., 0., 1., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 1.],
        [0., 0., 0., 0., 0., 0., 1., 0.]]
    ).reshape((2,2,2,2,2,2)),
    
    # measurements

    "M01" : np.array(
        [[[1., 0.],
        [0., 0.]],

        [[0., 0.],
        [0., 1.]]]
    ),

    "M10" : np.array(
        [[[0., 0.],
        [0., 1.]],

        [[1., 0.],
        [0., 0.]]]
    ),

    "Mpm" : np.array(
        [[[0.5, 0.5],
        [0.5, 0.5]],

        [[0.5, -0.5],
        [-0.5, 0.5]]]
    ),

    "Mmp" : np.array(
        [[[0.5, -0.5],
        [-0.5, 0.5]],

        [[0.5, 0.5],
        [0.5, 0.5]]]
    ),

    "MEq01_2" : np.array(
        [[[0., 0., 0., 0.],
         [0., 1., 0., 0.],
         [0., 0., 1., 0.],
         [0., 0., 0., 0.]],

         [[1., 0., 0., 0.],
         [0., 0., 0., 0.],
         [0., 0., 0., 0.],
         [0., 0., 0., 1.]]]
    ).reshape((2,2,2,2,2)),

    # hermitian operators
    "Idiv2" : np.array(
        [[1., 0.],
        [0., 1.]]
    )/2,

    "Zero" : np.zeros((2,2)),

    "P0" : np.array(
        [[1., 0.],
        [0., 0.]]
    ),

    "P0div2" : np.array(
        [[1., 0.],
        [0., 0.]]
    )/2,

    "P1" : np.array(
        [[0., 0.],
        [0., 1.]]
    ),

    "P1div2" : np.array(
        [[0., 0.],
        [0., 1.]]
    )/2,

    "Pp" : np.array(
        [[0.5, 0.5],
        [0.5, 0.5]]
    ),

    "Ppdiv2" : np.array(
        [[0.5, 0.5],
        [0.5, 0.5]]
    )/2,

    "Pm" : np.array(
        [[0.5, -0.5],
        [-0.5, 0.5]]
    ),

    "Pmdiv2" : np.array(
        [[0.5, -0.5],
        [-0.5, 0.5]]
    )/2,

    # 2 qubits equal on the 01 basis
    "Eq01_2" : np.array(
        [[1., 0., 0., 0.],
        [0., 0., 0., 0.],
        [0., 0., 0., 0.],
        [0., 0., 0., 1.]]
    ).reshape((2,2,2,2)),
    
    # 2 qubits not equal on the 01 basis
    "Neq01_2" : np.array(
        [[0., 0., 0., 0.],
        [0., 1., 0., 0.],
        [0., 0., 1., 0.],
        [0., 0., 0., 0.]]
    ).reshape((2,2,2,2)),

    # 3 qubits equal on the 01 basis
    "Eq01_3" : np.array(
        [[1., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 0., 0., 1.]]
    ).reshape((2,2,2,2,2,2)),
}

def get_opt_env() -> ScopeTerm:
    '''
    return the var environment containing the operators
    '''
    scope = ScopeTerm("opt_library", None)
    for id in optlib:
        scope[id] = OperatorTerm(optlib[id])
    return scope



def optload(path : str) -> OperatorTerm:
    try:
        return OperatorTerm(np.load(path))

    except:
        raise RuntimeErrorWithLog("Cannot load the operatior at '" + path + "'. (filename extension is needed)")


def optsave(opt : dts.Var, path : str) -> None:
    try:
        if opt.type != type_operator:
            raise RuntimeErrorWithLog("The variable '" + str(opt) + "' is not an operator.")
        opt_val = opt.eval()
        if not isinstance(opt_val, OperatorTerm):
            raise Exception()
        np.save(path, opt_val.m)
    
    except:
        raise RuntimeErrorWithLog("Cannot save the operator '" + str(opt) + "' at the position '" + path + "'.") 

