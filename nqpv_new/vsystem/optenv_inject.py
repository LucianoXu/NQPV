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

from nqpv_new.vsystem.content.opt.opt_kernel import get_opt_qnum

from .log_system import LogSystem
from .var_env import VType, Value, VarEnv
from .venv import VEnv

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

def get_opt_env() -> VarEnv:
    '''
    return the var environment containing the operators
    '''
    r = VarEnv()
    type_right = VType("operator", ())
    for id in optlib:
        type_left = VType("operator", (get_opt_qnum(optlib[id]),))
        r.assign_var(id, type_left, Value(type_right, optlib[id]))
    return r


'''
def optload_inject(folder_path : str) -> bool:
    return whether the optload has been successfully done.
    try:
        
        for item in os.listdir(folder_path):
            new_path = os.path.join(folder_path, item)
            if os.path.isfile(new_path):
                if item.endswith(".npy"):
                    id = item[:-4]
                    if id in opt_env.OptEnv.lib:
                        LogSystem.channels["warning"].append("The operator '" + id + "' appeared more than once.")
                    else:
                        opt_env.OptEnv.append(np.load(new_path), id, False)
            elif os.path.isdir(new_path):
                if not optload_inject(new_path):
                    return False
                    
        return True

    except:
        LogSystem.channels["error"].append("Error occured while loading operatiors in the folder " + folder_path + ".")
        return False
'''




