import nqpv
import numpy as np
import time

def qvarlv_n(n : int) -> str:
    r = "["
    for i in range(n):
        r += "q" + str(i) + " "
    return r + "]"

def Hn (n : int) -> str:
    r = ""
    for i in range(n):
        r += "q"+str(i) +" *= H; "
    return r

def generate_grover_prog(n : int) -> str:
    ctt  = '''
    def O := load "O.npy" end
    def CP := load "CP.npy" end
    def Psol := load "Psol.npy" end
    
    setting IDENTICAL_VAR_CHECK := false end

    '''

    ctt += "def pf := proof" + qvarlv_n(n) + " :\n"
    ctt += "\t { Zero[q0] };\n\n"
    ctt += "\t" + qvarlv_n(n) + ":=0;\n\n"
    ctt += "\t// H^n\n" 
    ctt += "\t" + Hn(n) + "\n\n"
    ctt += "\t// Oracle\n"
    ctt += "\t" + qvarlv_n(n) + " *= O;\n\n"
    ctt += "\t// H^n\n"
    ctt += "\t" + Hn(n) + "\n\n"
    ctt += "\t// controlled phase gate\n"
    ctt += "\t" + qvarlv_n(n) + " *= CP;\n\n"
    ctt += "\t// H^n\n"
    ctt += "\t" + Hn(n) + "\n\n"

    for i in range(n):
        ctt += "\tif M10[q" + str(i) + "] then skip else skip end;\n"
    
    ctt += "\t{ Psol" + qvarlv_n(n) + "}\n"
    ctt += "end"
    return ctt

def verify_grover_n (n : int):

    # create the nqpv file
    with open("./prog.nqpv", "w") as p:
        p.write(generate_grover_prog(n))

    # create the required operators
    N = 2**n
    sol = np.array([0.]*N)
    sol[0] = 1.
    Psol = np.tensordot(sol, sol, 0)
    np.save("./Psol", Psol.reshape((2,)*(2*n)))
    O = np.eye(N) - 2*Psol
    np.save("./O", O.reshape((2,)*(2*n)))
    temp = np.array([-1.]*N)
    temp[0] = 1.
    CP = np.diag(temp)
    np.save("./CP", CP.reshape((2,)*(2*n)))

    # verify
    nqpv.verify("./prog.nqpv")


def grover_performance_test(n_max : int = 14):
    with open("test_result.txt", "w") as p:
        p.write("Grover N performance test \n\nqubit_n\t\ttime (s)\n")
        p.flush()

        for i in range(1, n_max + 1):
            print("grover " + str(i) + "...", end="")

            T1 = time.time()

            verify_grover_n(i)

            T2 = time.time()
            t = (T2 - T1)

            p.write(str(i) + "\t\t" + str(t) + "\n")
            p.flush()
            print(str(t) + " (s)\n")


            


if __name__ == "__main__":
    grover_performance_test(15)