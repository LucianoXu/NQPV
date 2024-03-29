<!--
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
-->

# NQPV - Nondeterministic Quantum Program Verifier

**Version: 0.4b1**

NQPV is a verification assistant tool for the formal verification of nondeterministic quantum programs. Different form tools which are based on theorem provers, the goal of NQPV is to mitigate the overload of the user and help complete particular verification tasks efficiently.

## Install
NQPV is written in pure Python. It can be easily installed through PyPI. To do this, after installing Python3 and pip, open a command prompt and run this command:
```
pip install NQPV
```

Github repository: https://github.com/LucianoXu/NQPV. Example codes can be found there.

Dependence: this tool depends on the following python packages.
- ply
- numpy
- cvxpy

## Introduction
For a general introduction to the formal verification of quantum programs using Hoare logic, please refer to this article:

*Ying M. Floyd--hoare logic for quantum programs[J]. ACM Transactions on Programming Languages and Systems (TOPLAS), 2012, 33(6): 1-49.*

This assistant tool is an implementation of [not published yet], and please refer to this article for more detailed information. Briefly speaking, formal verification means to check whether particular properties hold for the given program, with the solid guarantee from mathematics. This tool, NQPV, mainly focuses on the partial correctness of quantum programs, which says that initial quantum states satisfying the precondition will also satisfy the postcondition when they terminate after the program computation. 

Here, the quantum programs in consideration consist of skip, abort, initialization, unitary transformation, if, while and nondeterministic choice. The conditions (or assertions) are represented by sets of proper Hermitian operators. These will be introduced in the following.

This tool does not depend on any existing proof assistants, and there are several pros and cons due to this approach. NQPV will not be as expressive as other verification tools that are based on proof assistants and can only deal with numerical operators. However, the proof hints from the user are the natural program code, and NQPV supports a high degree of automation.

To work with this verifier, an individual folder is needed, which contains the quantum program and the operators used in the program. The verifier will check the program's grammar and verify the correctness property automatically.


## NQPV : Hello World

Here is a hello-world example of NQPV. Create a new python script with the following content, and run the script **at the same folder**. In this example, the script creates a ".nqpv" file, indicating the verification description, which is later processed in the python script by the *verify* method.

**Important Note:** we strongly recommend running the python script in the same folder, meaning the current path of the command prompt is the same folder that the script is in. This is mainly for the consideration of file operation, since the *open* method in Python operates according to the command prompt path.

```Python
import nqpv

code = '''
def pf := proof [q] :
    { P0[q] };
    q *= X;
    { P1[q] }
end

show pf end
'''

fp = open("example.nqpv","w")
fp.write(code)
fp.close()

nqpv.entrance.verify("example.nqpv")
```

The expected output should be:
```

 (example, line 8)

proof [q] :
        { P0[q] };

        { P0[q] };
        [q] *= X;

        { P1[q] }

```
which is actually the output message of the *show* command. This example verifies the correctness formula
$$
\{\ket{0}_{q}\bra{0}\}\ q\ *= X\ \{\ket{1}_{q}\bra{1}\}
$$
by defining a corresponding proof term, and the automatically generated proof outlines are shown afterwards.


## Verification Language - Scopes and Commands

NQPV uses a language to organize and carry out the verification task. 

This language uses *variables* to store and represent essential items, such as quantum operators, programs or correctness proofs. Variables are stored and managed in *scopes*, which are also variables themselves. Therefore a scope can contain subscopes as its variables, forming a variable hierarchy. Variables use *identifiers* as their names, which follow the same rule as that in C or Python (regular expression: '[a-zA-Z_][a-zA-Z_0-9]*').

We use *commands* to manipulate the proof system.


### Scopes
A *Scope* is a variable environment containing the related program descriptions and calculation results.

When the verifier processes a *".npqv"* file, it opens up a global scope called *"global"*, which contains the preloaded operators variables. In a ".nqpv" file, with the command

```
show global end
```

the processing output should be something like 
```

 (prog, line 1) 
<scope global.>
EPS : 1e-07 ;
SDP precision : 1e-09 ;
SILENT : True ;
IDENTIVAL_VAR_CHECK : True ;
OPT_PRESERVING : True
        I               operator 1 qubit
        X               operator 1 qubit
        Y               operator 1 qubit
        Z               operator 1 qubit
        H               operator 1 qubit
        CX              operator 2 qubit
        CH              operator 2 qubit
        SWAP            operator 2 qubit
        CCX             operator 3 qubit
        Idiv2           operator 1 qubit
        Zero            operator 1 qubit
        P0              operator 1 qubit
        P0div2          operator 1 qubit
        P1              operator 1 qubit
        P1div2          operator 1 qubit
        Pp              operator 1 qubit
        Ppdiv2          operator 1 qubit
        Pm              operator 1 qubit
        Pmdiv2          operator 1 qubit
        Eq01_2          operator 2 qubit
        Neq01_2         operator 2 qubit
        Eq01_3          operator 3 qubit
        M01             measurement 1 qubit
        M10             measurement 1 qubit
        Mpm             measurement 1 qubit
        Mmp             measurement 1 qubit
        MEq01_2         measurement 2 qubit
        MEq10_2         measurement 2 qubit
        prog            scope

```
The description contains the local settings for the scope and the variables in the scope. In fact, the processing result of a ".npqv" file is also returned as a scope.

Variables of the local scope will overlap those in the global scope with the same name, which works just like that in C or Python. We can also refer to a variable by its path, such as:
```
show I end
show global.I end
```
will print the same result.

To better organize the proofs, we can also define scopes. For example, the example code of hello world can be rewritten as:
```
def hello_world :=
    def pf := proof [q] :
        { P0[q] };
        q *= X;
        { P1[q] }
    end
end

// Comment: the command in the next line is illegal.
// show pf end
show hello_world.pf end
```

### Commands
Commands are executed in a scope.

Currently, the commands in NQPV are separated into three groups:
- definition: including commands for defining different variables
- show: to show detailed information on variables
- save: to save a generated operator as a binary file
- setting: used to adjust the settings for verification

#### Command : **def**
The command **def** defines a variable. The syntax is :
```
def <identifier> := <expression> end
```
The name of the variable is determined by the *identifier*, and its value is determined by *expression*. There are several kinds of expression:
- proof hint: we will focus on it in the next section.
- loaded operator: the verifier loads a numpy ".npy" file as the operator value.
- scope: a new sub-scope will be defined.

**loaded operator**: example code. Of course, there should exist the binary file at the specified location. The location is relative to the ".nqpv" module file.
```
def Hpost := load "Hpost.npy" end
show Hpost end
```
**Note:** The numpy ndarray for quantum operators here are in a special form. For a $n$-qubit operator, the corresponding numpy object should be a $2n$ rank tensor, with distichous indices. What's more, the first $n$ indices correspond to the ket space, and the second $n$ indices correspond to the bra space. The qubit mapping is like this: high-address qubits are at the front. (It may be a little abstract, but you can show several preloaded standard operators to discover the restrain.)

**scope**: example code already shown in the last subsection.


#### Command : **show**
The usage of the *show* command is simple. It just outputs the expression. The syntax is:

```
show <expression> end
```

Example codes include:
```
show CX end
show global end
show
    proof [q] :
        { P0[q] };
        q *= X;
        { P1[q] }
end
```
#### Command : **save**
During a verification, predicates of intermediate weakest preconditions will be automatically generated and preserved in the scope. We can save the as numpy ".npy" binary files for later analysis.

The syntax is:
```
save <variable> at <address> end
```

An example code is:
```
def pf := 
    proof [q] :
        { P0[q] };
        q *= X;
        { P1[q] }
end

save VAR0 at "var0.npy" end
```

#### Command : **settings**
A scope contains the settings for the verification. There are three settings:
- EPS (float): controls the precision of equivalence between float numbers.
- SDP_PRECISION (float): controls the precision of the SDP solver.
- SILENT (**true** or **false**): controls whether the intermediate procedures are output during the verification. This is for the purpose of monitoring a time-consuming task.
- IDENTICAL_VAR_CHECK (**true** or **false**): controls whether identical variables (operators) are detected to keep the naming more informative. Default is on, and this function is especially time-consuming. Turn if off for verification of programs with large qubit numbers.
  
The syntax of **setting** is:
```
setting [EPS | SDP_PRECISION | SILENT] := <value> end
```
and this command will take effect immediately in the current scope. An example code:
```
// expl.nqpv
setting SILENT := false end
show global.expl end
def pf := proof [q] :
    { P0[q] };
    q *= X;
    { P1[q] }
end
```
And a verbose output of the procedure is provided.


## Quantum Program - Constructing the proof
The verification of program correctness is through the definition of a proof term. Here in NQPV, we do not need to provide proof of full details (like what is required in CoqQ or QHLProver). Instead, we write a *"proof hint"*, which briefly describes the correctness formula we want to proof and provides the required loop invariants.

In the following, we will explain the syntax of a proof hint.
If you found the formal description of the grammar hard to understand, you may refer to the examples for an intuitive idea.

The expression of a proof hint should be:

> proof_hint ::= proof [ id_ls ] : <br>
>  { herm_ls } <br>
> sequence <br>
> { herm_ls }

<!--
> $$
\begin{aligned}
 \mathrm{prog} ::=\ & \mathrm{qvar}\ [\ \mathrm{id\_ls}\ ]\\
    & \{\ \mathrm{herm\_ls} \}\\
    & \mathrm{sequence} \\
    & \{\ \mathrm{herm\_ls} \}
\end{aligned}
> $$
-->

The first line "proof [id_ls]" indicates all the quantum variables. The second and forth line indicates the pre and post conditions. The third line indicates the sequence of verification. 


"id_ls" is a list of one or more identifiers. 
> id_ls ::= <br>
> id <br>
> | id_ls id

<!--
> $$
\begin{aligned}
 \mathrm{id\_ls} ::=\ & \mathrm{id} \\
                    &|\ \mathrm{id\_ls}\quad \mathrm{id}
\end{aligned}
> $$
-->

"herm_ls" is a list of one or more operators.  
> herm_ls ::= <br>
> id [ id_ls ] <br>
> | herm_ls id [ id_ls ]


<!--
> $$
\begin{aligned}
 \mathrm{herm\_ls} ::=\ & \mathrm{id}\ [\ \mathrm{id\_ls}\ ]\\
                    &|\ \mathrm{herm\_ls}\quad  \mathrm{id}\ [\ \mathrm{id\_ls}\ ]
\end{aligned}
> $$
-->

"id [ id_ls ]" describes a particular operator, with the identifier list specifying the Hilbert space of the operator. For example, 
$$
\mathrm{P0}\ [\ \mathrm{q1}\ ]
$$
may refer to a Herimitian operator |0><0| on the space of variable q1, and 
$$
\mathrm{CX}\ [\ \mathrm{q2}\ \mathrm{q1}\ ]
$$
may refer to the controlled-X gate with q2 being the control and q1 being the target.

"sequence" is a list of verification tasks (programs or intermediate conditions), which are composed by sequential combination.

> sequence ::= <br>
> sentence <br>
> | sequence ; sentence

<!--
> $$
\begin{aligned}
 \mathrm{sequence} ::=\ & \mathrm{sentence}\\
                    &|\ \mathrm{sequence};\  \mathrm{sentence}
\end{aligned}
> $$
-->

And "sentence" is just a piece of verification task, which can be skip, abort, initialization, unitary transformation, if, while, nondeterministic choice. Besides, it can also be a quantum predicate (as the intermediate condition), or a former proof term.

> sentence ::= <br>
> skip <br>
> | abort <br>
> | [ id_ls ] := 0 <br>
> | [ id_ls ] *= id <br>
> | if id [ id_ls ] then sequence else sequence end <br>
> | { inv : herm_ls } while id [  id_ls ] do sequence end <br>
> | ( sequence \# sequence \# ... \# sequence) <br>
> | { herm_ls }

<!--
> $$
\begin{aligned}
 \mathrm{sentence} ::=\ & \mathrm{skip}\\
            &|\ \mathrm{abort}\\
            &|\ [\ \mathrm{id\_ls}\ ] := 0\\
            &|\ [\ \mathrm{id\_ls}\ ] *= \mathrm{id}\\
            &|\ \mathrm{if}\ \mathrm{id}\ [\ \mathrm{id\_ls}\ ]\ \mathrm{then}\  \mathrm{sequence}\ \mathrm{else}\ \mathrm{sequence}\ \mathrm{end}\\
            &|\ \{\ \mathrm{inv}:\ \mathrm{herm\_ls}\ \}\\
            &\quad \mathrm{while}\ \mathrm{id}\ [\ \mathrm{id\_ls}\ ]\ \mathrm{do}\ \mathrm{sequence}\ \mathrm{end}\\
            &|\ (\ \mathrm{sequence}\ \#\ \mathrm{sequence}\ )
\end{aligned}
> $$
-->

The last three rules of the grammar above correspond to the (multiple) nondeterministic choice, the use of former proof and the intermediate predicate, respectively.

## Program Verification Procedure

Here the syntactic analysis checks whether the content can be properly interpreted with the grammar. The semantic analysis afterwards checks whether there is any problem with the meaning of the verification task. It will mainly examine the following aspects:
- whether all operators mentioned can be found,
- whether there are repeat identifiers in some identifier list, and
- whether the qubit number of operators and identifier lists matches. For example, CX [ q1 ] or X [ q1 q2 ] will not be acceptable.

If there are syntactic or semantic errors, the verifier will stop there, providing the error information. 

The verification utilizes a technique called *backward predicate transformation*. If there are no while structures in the program, the whole calculation can be done automatically. That is, the weakest (liberal) precondition with respect to the given postcondition will be derived and compared with the desired precondition. Based on this, the verification tool will give a definite conclusion between the following two:
- Property holds.
- Property does not hold.

However, if there are while structures, the automatic calculation relies on the specified *loop invariant* from the user. The verifier will first check whether it is a valid loop invariant. If not, the verification will stop, and the failure will be reported. Otherwise, the corresponding precondition is derived, and the procedure continues. In this case, the verification result can be:
- Property holds.
- Property cannot be determined. A suitable loop invariant may be sufficient.

The tool can only give a definite conclusion if the property does hold.

## Examples
This section gives some examples of verification tasks. The source can be found in the Github repository.

### Error Correction Code
This example shows that the error correction code here is robust against single big-flip errors for a random single qubit pure state.
1. Create a folder called "error_correction_code"
2. In this folder, create a file called "example.nqpv" with the following content:
    ```
    def Hrand := load "Hrand.npy" end

    def pf := proof[q] :
        { Hrand[q] };

        [q1 q2] :=0;
        [q q1] *= CX;
        [q q2] *= CX;
        (skip # q *= X # q1 *= X # q2 *= X);
        [q q1] *= CX;
        [q q2] *= CX;
        [q1 q2 q] *= CCX;

        { Hrand[q] }
    end

    show pf end
    ```
3. In the same folder of "error_correction_code", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create a Hermitian on a random ket
    theta = np.random.rand() * np.pi
    phi = np.random.rand() * np.pi * 2

    ket = np.array([np.cos(theta), np.sin(theta)*np.exp(phi*1j)])

    Hrand = np.outer(ket, np.conj(ket))

    np.save("Hrand", Hrand)

    # verify
    nqpv.verify("./prog.nqpv")    
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)

### Deutsch Algorithm
1. Create a folder called "Deutsch_algorithm"
2. In this folder, create a file called "prog.nqpv" with the following content:
    ```

    def Hpost := load "Hpost.npy" end

    def pf := proof[q q1] :
        { I[q] };
        [q1 q2] :=0;
        q1 *= H;
        q2 *= X;
        q2 *= H;
        if M01[q] then
            ( 
                [q1 q2] *= CX
            #
                q1 *= X;
                [q1 q2] *= CX;
                q1 *= X
            )
        else
            (
                skip
            #
                q2 *= X
            )
        end;
        q1 *= H;
        if M01[q1] then
            skip
        else
            skip
        end;
        { Hpost[q q1] }
    end

    show pf end
    ```
3. In the same folder of "Deutsch_algorithm", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create the required operators
    Hpost = np.array([[1., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 1.]])
    np.save("./Hpost", Hpost.reshape((2,2,2,2)))

    # verify
    nqpv.verify("./prog.nqpv")
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)

### Quantum Walk

1. Create a folder called "quantum_walk"
2. In this folder, create a file called "prog.nqpv" with the following content:
    ```
    def invN := load "invN.npy" end
    def MQWalk := load "MQWalk.npy" end
    def W1 := load "W1.npy" end
    def W2 := load "W2.npy" end

    def pf := proof[q1 q2] :
        { I[q1] };

        [q1 q2] :=0;

        {inv: invN[q1 q2]};
        while MQWalk[q1 q2] do
            (
                [q1 q2] *= W1; [q1 q2] *= W2
            #
                [q1 q2] *= W2; [q1 q2] *= W1
            )
        end;

        { Zero[q1] }

    end

    show pf end
    ```
3. In the same folder of "quantum_walk", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create the required operators
    W1 = np.array([[1., 1., 0., -1.],
                    [1., -1., 1., 0.],
                    [0., 1., 1., 1.],
                    [1., 0., -1., 1.]]) / np.sqrt(3)
    W2 = np.array([[1., 1., 0., 1.],
                    [-1., 1., -1., 0.],
                    [0., 1., 1., -1.],
                    [1., 0., -1., -1.]]) / np.sqrt(3)
    np.save("W1", W1.reshape((2,2,2,2)))
    np.save("W2", W2.reshape((2,2,2,2)))

    P0 = np.array([[0., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 1., 0.],
                        [0., 0., 0., 0.]])
    P1 = np.array([[1., 0., 0., 0.],
                        [0., 1., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 1.]])
                        
    MQWalk = np.stack((P1,P0), axis = 0)
    np.save("MQWalk", MQWalk.reshape((2,2,2,2,2)))

    # the invariant N
    invN = np.array([[1., 0., 0., 0.],
                    [0., 0.5, 0., 0.5],
                    [0., 0., 0., 0.],
                    [0., 0.5, 0., 0.5]])
    np.save("invN", invN.reshape((2,2,2,2)))

    # verify
    nqpv.verify("prog.nqpv")
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)


## Contact
If you find any bugs or have any questions, do not hesitate to contact lucianoxu@foxmail.com.


## Development Log
### 0.4b1
- We refactored this software and deleted some redundant functions, including subprogram, subproof and module import.

### 0.3b9
- Now, the verification tool will try to find an existing variable for the particular value before creating a new one with an auto name.
