import sys
from Solving_Functions import *

#The command receives as input three parameters, the type of solution method, the solver for the method and the number of the instance.

N_inst = sys.argv[3]
if int(N_inst)<10:
    inst_name=".\\Instances\\inst0"+N_inst+".dat"
    simple = True
else:
    inst_name=".\\Instances\\inst"+N_inst+".dat"
    simple = False

#Open instance .dat file
f = open(inst_name, 'r')

#Read number of couriers
m=int(f.readline())

#Read number of items
n=int(f.readline())

#Read courier capacities
l_split = f.readline().split()
l=[]
for i in l_split:
    l.append(int(i))

#Read item sizes
s_split = f.readline().split()
s=[]
for i in s_split:
    s.append(int(i))

#Read distance matrix
D = []
for i in range(n+1):
    d_split = f.readline().split()
    d_row = []
    for j in d_split:
        d_row.append(int(j))
    D.append(d_row)

#Starting from D compute Upper and Lower bound for the problem:
Dnp = np.array(D)
round_trips=[]
for i in range(n):
    round_trips.append(Dnp[i][n]+Dnp[n][i])
LB = max(round_trips)
LLB = min(round_trips)

UB = 0
for i in range(n):
    UB+=max(Dnp[i,:])

method = sys.argv[1]
solver = sys.argv[2]
if method=="CP":
    if solver not in ["gecode", "chuffed"]:
        print(f"There is no {solver} solver for CP")
    else:
        Solve_CP(m, n, l, s, Dnp, UB, LB, LLB, simple, solver)
elif method=="SAT":
    #Solve_SAT(...)
    print("Not Yet Implemented")
elif method=="SMT":
    #Solve_SMT(...)
    print("Not Yet Implemented")
elif method=="MIP":
    #Solve_MIP(...)
    print("Not Yet Implemented")
else:
    print("There is no such method")

