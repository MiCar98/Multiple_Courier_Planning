import datetime
from minizinc import Instance, Model, Solver
import numpy as np
import sys

gecode = Solver.lookup("gecode")

MCP = Model("CP_Model_4_0_1.mzn")

MCP_instance = Instance(gecode, MCP)

#Input the number of the instance to solve
N_inst = sys.argv[1]
if int(N_inst)<10:
    name_inst=".\\instances\\inst0"+N_inst+".dat"
else:
    name_inst=".\\instances\\inst"+N_inst+".dat"

#Open instance .dat file
f = open(name_inst, 'r')

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


MCP_instance['m']=m
MCP_instance['n']=n
MCP_instance['l']=l
MCP_instance['s']=s
MCP_instance['D']=D

#Read instance number N_inst and obtain parameters:
#MCP_instance.add_file(name_inst)
print(MCP_instance['m'])
print(MCP_instance['n'])
print(MCP_instance['l'])
print(MCP_instance['s'])
print(MCP_instance['D'])


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

MCP_instance["LB"]=LB
print(MCP_instance["LB"])
MCP_instance["LLB"]=LLB
print(MCP_instance["LLB"])
MCP_instance["UB"]=UB
print(MCP_instance["UB"])


#Check if the distance matrix is symmetric and apply symmetry breaking constraint if so
if np.all(Dnp == Dnp.T):
    print("Matrix is symmetric")
    MCP_instance.add_string("constraint forall(i in 1..m)(arg_max(Z[i,1..n+1])>Z[i,n+1]);")
    

#Solve computing the solution
to = datetime.timedelta(seconds=300)
print(f"Solving the problem with\nnumber of couriers = {MCP_instance['m']}\nnumber of items = {MCP_instance['n']}\n")
result = MCP_instance.solve(timeout=to)#, intermediate_solutions=True)


#Extract the solution variable
print('SOLUTION'+92*'=')
Znp = np.array(result["Z"])
Zc, Zi = Znp.shape
for c in range(Zc):
    print(f"Path for courier {c+1}")
    node = Znp[c][Zi-1]
    print('Depot', end='--->')
    while node!=Zi:
         print(node, end='--->')
         node = Znp[c][node-1]
    print("Depot")
    print()

    
print(f"Optimal maximum distance found = {result['objective']}")
print(100*'='+ '\n')


#Configuration 1: Gecode, dom_w_deg, indomain_random, distance symmetry breaking, redundant constraint
#Configuration 2: 
