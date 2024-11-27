import sys, os
from Solving_Functions import *
from pathlib import Path

#The command receives as input three parameters, the type of solution method, the solver for the method and the number of the instance.

N_inst = sys.argv[3]
if int(N_inst)<10:
    inst_name="Instances/inst0"+N_inst+".dat"
    simple = True
else:
    inst_name="Instances/inst"+N_inst+".dat"
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
break_symmetry = sys.argv[4]
dict={}
if method=="CP":
    if solver not in ["gecode", "chuffed"]:
        print(f"There is no {solver} solver for CP")
    else:
        dict=Solve_CP(m, n, l, s, Dnp, UB, LB, LLB, simple, solver, break_symmetry)
elif method=="SAT":
    dict=Solve_SAT(m, n, l, s, Dnp, UB, LB, LLB)
elif method=="SMT":
    dict=Solve_SMT(m, n, l, s, D, UB, LB, break_symmetry)
elif method=="MIP":
    #dict=Solve_MIP(m, n, l, s, Dnp, UB, LB, solver, break_symmetry)
    print("Hello there")
else:
    print("There is no such method")

#Printing results on file
keys = ['time', 'optimal', 'obj', 'sol']
file_name = 'res/'+method+'/'+N_inst+'.json'
path = Path(file_name)
if path.is_file():
    f = open(file_name, 'r')
    f2 = open(file_name+'_2', 'w')
    bracket = f.readline()
    f2.write(bracket)
    f2.write("\""+dict['approach'] +"\":\n{")
    for k in keys:
        f2.write("\""+k+"\":"+str(dict[k]))
        if k !='sol':
            f2.write(',\n')
        else:
            f2.write('\n')
    f2.write("},\n")

    for line in f.readlines():
        f2.write(line)
    f.close()
    f2.close()
    os.remove(file_name)
    os.rename(file_name+'_2', file_name)

else:
    f = open(file_name, 'x')
    f.write('{')
    f.write("\n\""+dict['approach'] +"\":\n{")
    for k in keys:
        f.write("\""+k+"\":"+str(dict[k]))
        if k !='sol':
            f.write(',\n')
        else:
            f.write('\n')
    f.write("}\n")
    f.write('}')


