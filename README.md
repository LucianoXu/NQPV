# NQPV - Nondeterministic Quantum Program Verifier

**Version: 0.1**

NQPV is an assistant tool for the formal verification of nondeterministic quantum programs.

## Install
NQPV is written in pure Python. It can be easily installed through PyPI. To do this, after installing Python3 and pip, open a command prompt and run this command:
```
pip install nqpv
```


Github repository: https://github.com/LucianoXu/NQPV. Example codes can be found there.

## Introduction
This assistant tool is an implementation of [the article], and please refer to this article for more detailed information. Briefly speaking, formal verification means to check whether particular properties hold for the given program, with the solid gurantee from mathematics. This tool, NQPV, mainly focuses on the partial correctness of quantum programs, which says that initial quantum states satisfying the precondition will also satisfy the postcondition when they terminate after the program computation. 

Here, the quantum programs in consideration consist of skip, abort, initialization, unitary transformation, if, while and nondeterministic choice. The conditions (or assertions) are represented by sets of proper Hermitian operators. These will be introduced in the following.

To work with this verifier, an individual folder is needed, which contains the quantum program and the operators used in the program. The verifier will check the program's grammar, verify the correctness property automatically, and provide a report as the result. Correspondingly, this tool provides two kinds of methods: that for operator creation and that for verification.

## Quantum Program - Constructing the "prog" file
An individual folder is needed for each verification. Within each folder a file called "prog" must exist, which describes the verification task. The *prog* file should contain such information:

- all quantum variables, 
- the quantum program itself, 
- pre and post conditions, and
- the loop invariant for while programs.

The *prog* file is organized by a context-free grammar, using three classes of terms: *keyword*, *identifier* and *operator*. *keyword* includes the reserved words for program structures, which cannot be used as identifiers. In this tool, *identifier* follows the same rule as that in C or Python (regular expression: '[a-zA-Z_][a-zA-Z_0-9]*'), and are used to indicate quantum variables and quantum operators. *operator* includes non-letter characters for program structures.

Here is the list of keywords in NQPV:
> **qvar**, **skip**, **abort**, **if**, **then**, **else**, **while**, **do**, **end**, **inv**

### Formal grammar of the "prog" file
In the following we will explain the grammar of the *prog* file. 
If you found the formal description of the grammar hard to understand, you may refer to the examples for an intuitive idea.

The whole *prog* should contain the four part mentioned above.

> $$
\begin{aligned}
 \mathrm{prog} ::=\ & \mathrm{qvar}\ [\ \mathrm{id\_ls}\ ]\\
    & \{\ \mathrm{herm\_ls} \}\\
    & \mathrm{sequence} \\
    & \{\ \mathrm{herm\_ls} \}
\end{aligned}
> $$

The first line indicates all the quantum variables. The second and forth line indicates the pre and post conditions. The third line indicates the sequence of quantum program. 

$\mathrm{id\_ls}$ is a list of one or more identifiers. 
> $$
\begin{aligned}
 \mathrm{id\_ls} ::=\ & \mathrm{id} \\
                    &|\ \mathrm{id\_ls}\quad \mathrm{id}
\end{aligned}
> $$

$\mathrm{herm\_ls}$ is a list of one or more operators.  
> $$
\begin{aligned}
 \mathrm{herm\_ls} ::=\ & \mathrm{id}\ [\ \mathrm{id\_ls}\ ]\\
                    &|\ \mathrm{herm\_ls}\quad  \mathrm{id}\ [\ \mathrm{id\_ls}\ ]
\end{aligned}
> $$

$\mathrm{id}\ [\ \mathrm{id\_ls}\ ]$ describes a particular operator, with the identifier list specifying the Hilbert space of the operator. For example, 
$$
\mathrm{P0}\ [\ \mathrm{q1}\ ]
$$
may refer to a Herimitian operator $\ket{0}\bra{0}$ on the space of variable $\mathrm{q1}$, and 
$$
\mathrm{CX}\ [\ \mathrm{q2}\ \mathrm{q1}\ ]
$$
may refer to the controlled-X gate with $\mathrm{q2}$ being the control and $\mathrm{q1}$ being the target.

$\mathrm{sequence}$ is a list of programs, which are composed by sequential combination.
> $$
\begin{aligned}
 \mathrm{sequence} ::=\ & \mathrm{sentence}\\
                    &|\ \mathrm{sequence};\  \mathrm{sentence}
\end{aligned}
> $$

And $\mathrm{sentence}$ is just a piece of program, which can be skip, abort, initialization, unitary transformation, if, while and nondeterministic choice.
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

The last rule of the grammar above corresponds to the nondeterministic choice.

## Verification Procedure and API

This section describes how the verification tool is used, the corresponding API and the detailed verification procedure in the backend.

### Operator Creation

To work with this tool, all operators (unitary operators, Hermitian operators and operators of measurement) must be provided. That is to say, there should be a corresponding NumPy binary file ".npy" for the data, either in the same folder with *prog*, or in a particular *operator library*. NQPV provides a methode to create an operator library.

> **nqpv.lib_create (lib_path)<br>**
> Creates a library of commonly used operators at the specified location. 
> - Parameters : 
>   - **lib_path** : string <br>
>       The path of the newly created operator library relative to the run path.
> - Returns : None

The library is a folder, and you can of course copy your own operator files into the folder. Also note that if an operator file is named "**id**.npy", it will be referred in the *prog* file with the same identifier **id**.

For an operator on $n$ qubits, the data saved in the ".npy" file are rank $2*n$ tensors for unitaries and Hermitians, and rank $(2*n + 1)$ tensors for measurement operator sets. The $2*n$ indices are all 2 dimensional, sorted in the particular order: the first $n$ indices are the "row indices" of the corresponding "matrix", while the second $n$ indices are the corresponding "column indices".

NQPV provides the methods to create the ".npy" file for operators from **numpy.ndarray** objects. The NumPy object can be rank $2*n$ tensors or a $(2^n*2^n)$ matrices.

> **nqpv.save_unitary (path, id, unitary)<br>**
> Check and save the unitary operator. <br>
> This method will check whether the claimed unitary operator $U$ satisfies $U^\dagger U = I$.
> - Parameters : 
>   - **path** : string <br>
>       The folder path to save the newly created operator.
>   - **id** : string <br>
>       The identifier of the unitary operator. The operator will be save in the file "**id**.npy"
>   - **unitary** : **numpy.ndarray**, $(2^n*2^n)$ matrix or rank $2*n$ tensor <br>
>       The NumPy object of the unitary operator.
> - Returns : bool <br>
>   Whether the operator is successfully saved.


> **nqpv.save_hermitian (path, id, herm)<br>**
> Check and save the Hermitian operator. <br>
> This method will check whether the claimed Hermitian operator $H$ satisfies $H = H^\dagger$ and $\boldsymbol{0}\sqsubseteq H \sqsubseteq I$.
> - Parameters : 
>   - **path** : string <br>
>       The folder path to save the newly created operator.
>   - **id** : string <br>
>       The identifier of the Hermitian operator. The operator will be save in the file "**id**.npy"
>   - **herm** : **numpy.ndarray**, $(2^n*2^n)$ matrix or rank $2*n$ tensor <br>
>       The NumPy object of the Hermitian operator.
> - Returns : bool <br>
>   Whether the operator is successfully saved.


The extra (2 dimensional) index at the beginning of the measurement tensor is for the two possible results. For example, if $M$ is a tensor for the measurement operator set, then $M[0]$ represents the measurement operator for result 0 and $M[1]$ the result 1.

> **nqpv.save_measurement (path, id, measure)<br>**
> Check and save the measurement operator set. <br>
> This method will check whether the claimed measurement operator set $M$ satisfies $M[0]^\dagger M[0] + M[1]^\dagger M[1] = I$.
> - Parameters : 
>   - **path** : string <br>
>       The folder path to save the newly created operator.
>   - **id** : string <br>
>       The identifier of the measurement operator set. The operator will be save in the file "**id**.npy"
>   - **herm** : **numpy.ndarray**, $(2*2^n*2^n)$ tensor or rank $(2*n + 1)$ tensor <br>
>       The NumPy object of the measurement operator set. Note that the first index is for the possible measurement results.
> - Returns : bool <br>
>   Whether the operator is successfully saved.

### Program Verification

The method to conduct a verification task is the following one:

> **nqpv.verify (folder_path, lib_path = "", silent = False, total_correctness = False, preserve_pre = False, opt_in_output = False, save_opt = False)<br>**
> Conduct the verification task, and produce a 'output.txt' report.
> 
> - Parameters: 
>   - **folder_path** : string <br>
>       The folder of the verification task, relative to the run path. It should contain the *prog* file and the operator files mentioned in *prog* (if not in the operator library).
>   - **lib_path** : string <br>
>       The folder path of an operator library, relative to the run path. If provided, the verifier will also search in the library for the operators mentioned in *prog*.
>   - **silent** : bool <br>
>       Whether this method produces a lot of output in the command prompt. If **True**, only critical information is shown.
>   - **total_correctness** : bool <br>
>       Whether to verify in the sense of total correctness. If **False**, only partial correctness is considered. **(Keep this switch off since total correctness has not been considered yet.)**
>   - **preserve_pre** : bool <br>
>       Whether to preserve the current weakest (liberal) precondition at each step of calculation. If **True**, then what provided in the output is actually a *proof outline*.
>   - **opt_in_output** : bool <br>
>       Whether to show the operators in the report (including the intermediate preconditions, if **preserve_pre** is on). If **True**, all operators will be appended at the end of the report in the text form.
>   - **save_opt** : bool <br>
>       Whether to save the used operators in **folder_path** (including the intermediate preconditions, if **preserve_pre** is on). If **True**, all operators will be save in individual "**id**.npy" files.
> - Returns : None

The verification report 'output.txt' will include at least the following information:
- verification task settings,
- the source code from *prog*, and
- the syntactic/semantic analysis result.

Here the syntactic analysis checks whether the content in *prog* can be properly interpreted with the grammar. The semantic analysis afterwards checks whether there is any problem in the meaning of the verification task. It will mainly examine the following aspects:
- whether all operators mentioned can be found,
- whether there are repeat identifiers in some identifier list, and
- whether the qubit number of operators and identifier lists matches. For example, $\mathrm{CX}\ [\ \mathrm{q1}\ ]$ or $\mathrm{X}\ [\ \mathrm{q1}\ \mathrm{q2}\ ]$ will not be acceptable.

If there are syntactic or semantic errors, the report will stop there, providing the error information. Otherwise it will continue verifying and provide the following information:
- the verification result (property holds / does not hold / not determined yet),
- the proof outline (If **preserve_pre** is on, all intermediate weakest (liberal) preconditions will be named and provided.), and
- (if **opt_in_output** is on) all operators mentioned in the proof outline in text form.

The verification utilizes a technique called *backward predicate transformation*. If there is not any while structures in the program, the whole calculation can be done automatically. That is, the weakest (liberal) precondition with respect to the given postcondition will be derived and compared with the desired precondition. Based on this, the verification tool will give a definite conclusion between the following two:
- Property holds.
- Property does not hold.

However, if there are while structures, the automatical calculation relies on the specified *loop invariant* from the user. The verifier will first check whether it is a valid loop invariant. If not, the verification will stop and the failure will be reported. Otherwise, the corresponding precondition is derivied and the procedure continues. In this case, the verification result can be:
- Property holds.
- Property cannot be determined. A suitable loop invariant may be sufficient.

The tool can only give a definite conclusion if the property does hold.

## Examples
This section gives some examples of verification tasks. The source can be found in the Github repository.

### Error Correction Code
This example shows that the error correction code here is robust against single big-flip errors, for a random single qubit pure state.
1. Create a folder called "example_ErrCorr"
2. In this folder, create a file called "prog" with the following content:
    ```
    qvar [q q1 q2]

    { Hrand[q] }

    [q1 q2] := 0;
    [q q1] *= CX;
    [q q2] *= CX;
    (((skip # q *= X) # q1 *= X) # q2 *= X);
    [q q1] *= CX;
    [q q2] *= CX;
    [q1 q2 q] *= CCX

    { Hrand[q] }
    ```
3. In the same folder containing "example_ErrCorr", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create the operator library
    nqpv.lib_create("./lib")

    # create a Hermitian on a random ket
    theta = np.random.rand() * np.pi
    phi = np.random.rand() * np.pi * 2

    ket = np.array([np.cos(theta), np.sin(theta)*np.exp(phi*1j)])

    Hrand = np.outer(ket, np.conj(ket))

    nqpv.save_hermitian("./example_ErrCorr", "Hrand", Hrand)

    # verify
    nqpv.verify("./example_ErrCorr", "./lib", opt_in_output = True, preserve_pre = True)
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)

5. Check the folder "example_ErrCorr" and the report "output.txt" should be there.

### Deutsch Algorithm
1. Create a folder called "example_Deutsch"
2. In this folder, create a file called "prog" with the following content:
    ```
    qvar [q q1 q2]

    { I[q] }

    [q1 q2] := 0;
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
    end

    { Hpost[q q1] }    
    ```
3. In the same folder containing "example_Deutsch", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create the operator library
    nqpv.lib_create("./lib")

    # create the required operators
    Hpost = np.array([[1., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 1.]])
    nqpv.save_hermitian("./example_Deutsch", "Hpost", Hpost)

    # verify
    nqpv.verify("./example_Deutsch", "./lib", opt_in_output = True, preserve_pre = True)
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)

5. Check the folder "example_Deutsch" and the report "output.txt" should be there.

### Quantum Walk

1. Create a folder called "example_QWalk"
2. In this folder, create a file called "prog" with the following content:
    ```
    qvar [q1 q2]

    { I[q1] }

    [q1 q2] := 0;

    {inv: invN[q1 q2]}
    while MQWalk[q1 q2] do
        (
            [q1 q2] *= W1; [q1 q2] *= W2
        #
            [q1 q2] *= W2; [q1 q2] *= W1
        )
    end

    { Zero[q1] }
    ```
3. In the same folder containing "example_QWalk", create a python script "example.py" with the following content:

    ```Python
    import nqpv
    import numpy as np

    # create the operator library
    nqpv.lib_create("./lib")

    # create the required operators
    W1 = np.array([[1., 1., 0., -1.],
                    [1., -1., 1., 0.],
                    [0., 1., 1., 1.],
                    [1., 0., -1., 1.]]) / np.sqrt(3)
    W2 = np.array([[1., 1., 0., 1.],
                    [-1., 1., -1., 0.],
                    [0., 1., 1., -1.],
                    [1., 0., -1., -1.]]) / np.sqrt(3)
    nqpv.save_unitary("./example_QWalk", "W1", W1)
    nqpv.save_unitary("./example_QWalk", "W2", W2)

    P0 = np.array([[0., 0., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 1., 0.],
                        [0., 0., 0., 0.]])
    P1 = np.array([[1., 0., 0., 0.],
                        [0., 1., 0., 0.],
                        [0., 0., 0., 0.],
                        [0., 0., 0., 1.]])
                        
    MQWalk = np.stack((P0,P1), axis = 0)
    nqpv.save_measurement("./example_QWalk", "MQWalk", MQWalk)

    # the invariant N
    invN = np.array([[1., 0., 0., 0.],
                    [0., 0.5, 0., 0.5],
                    [0., 0., 0., 0.],
                    [0., 0.5, 0., 0.5]])
    nqpv.save_hermitian("./example_QWalk", "invN", invN)

    # verify
    nqpv.verify("./example_QWalk", "./lib", opt_in_output = True, preserve_pre = True)
    ```

4. Run the python script in the folder. (Note that the run path also needs to be the folder.)

5. Check the folder "example_QWalk" and the report "output.txt" should be there.

## Contact
If you find any bug or have any questions, do not hesitate to contact lucianoxu@foxmail.com.
