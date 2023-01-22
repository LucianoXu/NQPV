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
from __future__ import annotations

import os

from nqpv.vsystem.opt_kernel import get_opt_qnum, check_measure

from .log_system import RuntimeErrorWithLog
from .var_scope import VarScope
from .content.opt_term import OperatorTerm, MeasureTerm

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

mealib = {
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
}

def get_opt_env() -> VarScope:
    '''
    return the var environment containing the operators
    '''

    scope = VarScope("opt_library", None)
    for id in optlib:
        scope[id] = OperatorTerm(optlib[id])
    for id in mealib:
        scope[id] = MeasureTerm(mealib[id])
    return scope



def optload(path : str) -> OperatorTerm | MeasureTerm:
    try:
        m = np.load(path)
        if check_measure(m):
            return MeasureTerm(m)
        else:
            return OperatorTerm(m)
        

    except:
        raise RuntimeErrorWithLog("Cannot load the operatior at '" + path + "'. (filename extension is needed)")

def optsave(opt : OperatorTerm | MeasureTerm, path : str) -> None:
    try:
        if isinstance(opt, OperatorTerm):
            np.save(path, opt.m)
        elif isinstance(opt, MeasureTerm):
            np.save(path, opt.m)
        else:
            raise ValueError()
    
    except:
        raise RuntimeErrorWithLog("Cannot save the operator '" + str(opt) + "' at the position '" + path + "'.")
