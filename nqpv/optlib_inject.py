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
# optlib_inject.py
#
# create the commonly used unitary gates and measurements
# load the tensors in the run path folder
# ------------------------------------------------------------

from genericpath import isdir
import os

from .logsystem import LogSystem
from .semantics import optEnv

import numpy as np

# channel of report
channel = "main"

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
    
    "Zero" : np.zeros((2,2)),

    "P0" : np.array([[1., 0.],
                    [0., 0.]]),

    "P1" : np.array([[0., 0.],
                    [0., 1.]]),

    "Pp" : np.array([[0.5, 0.5],
                    [0.5, 0.5]]),

    "Pm" : np.array([[0.5, -0.5],
                    [-0.5, 0.5]]),
}

def optlib_inject() -> None:
    '''
    inject the commonly used operators into the optEnv
    '''
    for id in optlib:
        optEnv.OptEnv.append(optlib[id], id, False)

def optload_inject(run_path : str) -> bool:
    '''
    return whether the optload has been successfully done.
    '''
    try:
        
        for item in os.listdir(run_path):
            new_path = os.path.join(run_path, item)
            if os.path.isfile(new_path):
                if item.endswith(".npy"):
                    id = item[:-4]
                    if id in optEnv.OptEnv.lib:
                        LogSystem.channels[channel].append("Warning: the operator '" + id + "' appeared more than once.")
                    else:
                        optEnv.OptEnv.append(np.load(new_path), id, False)
            elif os.path.isdir(new_path):
                if not optload_inject(new_path):
                    return False
                    
        return True

    except:
        LogSystem.channels[channel].append("Error occured while loading operatiors in the folder " + run_path + ".")
        return False





