from z3 import *
from Bool_utils import *
from colorama import Fore
import time



N_inst = sys.argv[1]
if int(N_inst)<10:
     name_inst=".\\Instances\\inst0"+N_inst+".dat"
else:
    name_inst=".\\Instances\\inst"+N_inst+".dat"

#name_inst = 'C:\\Users\\Utente\\Desktop\\Università\\Magistrale\\CDMO\\Project\\Instances\\inst01.dat'

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

Dnp = np.array(D)
round_trips=[]
for i in range(n):
    round_trips.append(Dnp[i][n]+Dnp[n][i])
LB = max(round_trips)
LLB = min(round_trips)

UB = 0
for i in range(n):
    UB+=max(Dnp[i,:])

print(Fore.WHITE+f'{m}')
print(n)
print(l)
print(s)
print(D)

start_encode=time.time()
#Convert all parameter values into boolean arrays
max_load = max(sum(s), max(l))
max_load_bits = convert_dec_to_bool(max_load)['Num_bits']
UB_bits = convert_dec_to_bool(UB)['Num_bits']
Dist = [[Bool(f"dist_{i}_bit_{j}") for j in range(UB_bits)] for i in range(m)]
C = [[Bool(f"courier_load_{i}_bit_{j}") for j in range(max_load_bits)] for i in range(m)]
Max_Dist = [Bool(f"Max_Dist_bit_{i}") for i in range(UB_bits)]




l_bool = [convert_dec_to_bool(l[i], max_load_bits)['Conversion'].tolist() for i in range(len(l))]
s_bool = [convert_dec_to_bool(s[i], max_load_bits)['Conversion'].tolist() for i in range(len(s))]
D_bool = [[convert_dec_to_bool(D[i][j], UB_bits)['Conversion'].tolist() for j in range(len(D[i]))] for i in range(len(D))]

LB_bool = convert_dec_to_bool(LB, UB_bits)['Conversion'].tolist()
UB_bool = convert_dec_to_bool(UB, UB_bits)['Conversion'].tolist()
LLB_bool = convert_dec_to_bool(LLB, UB_bits)['Conversion'].tolist()

#Delivery assignment matrix
A = [[Bool(f"a_{i}_{j}") for j in range(n)] for i in range(m)]

#Graph matrix
G = [[[Bool(f"g_{i}_{j}_{k}") for k in range(n+1)] for j in range(n+1)] for i in range(m)]

#Visit sequence matrix
V = [[Bool(f"visit_item_{j}_as_{k}") for k in range(n)] for j in range(n)]






#Constraint 1: Every item is carried
const_1 = And(
    *[exactly_one_np([A[i][j] for i in range(m)], f'Item_{j}_is_carried_once') for j in range(n)]
)

#Constraint 2: Loads computation constraint
const_2 = And(
    *[sum_cond_on_array_constraint(C[i], s_bool, A[i], f'Full_Load_Courier_{i}') for i in range(m)]
)

#Constraint 3: Load capacities must be respected
const_3 = And(
    *[compare(C[i], l_bool[i], '<=') for i in range(m)]
)

#Constraint 3_bis: every courier delivers at least one item
const_3_bis = And(
    *[at_least_one_np(A[i]) for i in range(m)]
)

#Constraint 4: every node is visited once
const_4 = And(
    *[exactly_one_np(V[j], f"Item_{j}_in_only_one_path") for j in range(n)]
)

#Constraint 5: No self-loops
const_5 = And(
    *[And(*[Not(G[i][j][j]) for j in range(n+1)]) for i in range(m)]
)

#Constraint 6: Channeling between assignment and routing - departure from node j
const_6 = And(
    *[And(*[(Implies(A[i][j], exactly_one_np(G[i][j],  f'Courier_{i}_departs_from_node_{j}'))) for j in range(n)], 
          *[(Implies(Not(A[i][j]), Not(Or(G[i][j])))) for j in range(n)]) 
          for i in range(m)]
)

#Constraint 7: Channeling between assignment and routing - arrival to node k
const_7 = And(
    *[And(*[(Implies(A[i][k], exactly_one_np([G[i][j][k] for j in range(n+1)], f'Courier_{i}_arrives_at_node_{k}'))) for k in range(n)], 
          *[(Implies(Not(A[i][k]), Not(Or([G[i][j][k] for j in range(n+1)])))) for k in range(n)]) 
          for i in range(m)]
)


#Constraint 8: Every courier leaves the Depot
const_8 = And(
    *[exactly_one_np(G[i][n], f'Courier_{i}_leaves_Depot') for i in range(m)]
)

#Constraint 9: Every couriers returns to the Depot
const_9 = And(
    *[exactly_one_np([G[i][j][n] for j in range(n+1)], f'Courier_{i}_returns_to_Depot') for i in range(m)]
)


# #Constraint 9: Routes should be coherent
# const_9 = And(
#     *[And(*[exactly_one_np([G[i][k][j] for k in range(n+1)])==exactly_one_np([G[i][j][k] for k in range(n+1)]) for j in range(n+1)]) for i in range(m)]
# )

#Constraint 10: Subtour elimination constraint
const_10 = And(
            *[And(
                *[And(
                    *[Implies(G[i][j][k], consecutive(V[j], V[k])) for k in range(n)],
                    Implies(G[i][n][j], V[j][0])) 
                for j in range(n)])
            for i in range(m)])

#Constraint 11: Distance computation constraint
const_11 = And(
    *[sum_cond_on_array_constraint(Dist[i], flatten(D_bool), flatten(G[i]), f'Distance_Courier_{i}') for i in range(m)]
)

#Constraint 12: Max_dist is the maximum distance
const_12 = And(
    *[compare(Max_Dist, Dist[i], '>=') for i in range(m)]
)

#Constraint 13: Max_dist must be equal to one of the distances
const_13 = Or(
    *[compare(Max_Dist, Dist[i], '==') for i in range(m)]
)



#Lower bound constraints
lb_const = compare(Max_Dist, LB_bool, '>=')
ub_const = And(
    *[compare(Dist[i], UB_bool, '<=') for i in range(m)]
)
llb_const = And(
    *[compare(Dist[i], LLB_bool, '>=') for i in range(m)]
)
o = Optimize()
#o = Solver()

o.add(const_1) 
o.add(const_2) 
o.add(const_3)
o.add(const_3_bis) 
o.add(const_4) 
o.add(const_5) 
o.add(const_6) 
o.add(const_7) 
o.add(const_8) 
o.add(const_9) 
o.add(const_10) 
o.add(const_11)
o.add(const_12) 
o.add(const_13) 
#o.add(compare(convert_dec_to_bool(14, UB_bits)['Conversion'].tolist(), Max_Dist, '==')

o.add(lb_const)
o.add(ub_const)
o.add(llb_const)

end_encode = time.time()
print(f"Encoding time: "+ Fore.MAGENTA+f"{end_encode-start_encode}")

start_optimize = time.time()
o.set("timeout", 300000)
objective = Sum([If(Max_Dist[i], 2**(len(Max_Dist)-i), 0) for i in range(len(Max_Dist))])
o.minimize(objective)


res = o.check()
if res == sat:
    print(Fore.WHITE+"Satisfiable, with model:")
    model=o.model()
    #print("Objective value:", model.eval(objective))
    
    print(Fore.WHITE+f"Upper Bound is {convert_bool_to_dec(UB_bool)}")
    print(Fore.WHITE+f"Lower Bound is {convert_bool_to_dec(LB_bool)}")

    print(Fore.WHITE+f"Bool Maximum Distance is {[model.evaluate(Max_Dist[i]) for i in range(UB_bits)]}")
    print(Fore.WHITE+f"Maximum Distance is"+ Fore.MAGENTA + f" {convert_bool_to_dec([model.evaluate(Max_Dist[i]) for i in range(UB_bits)])}")

    print(Fore.WHITE+f"Assignments are: {[[model.evaluate(A[i][j]) for j in range(n)] for i in range(m)]}")

    print(Fore.WHITE+"Distances:")
    for i in range(m):
        print(convert_bool_to_dec([model.evaluate(Dist[i][k]) for k in range(UB_bits)]))

    print(Fore.WHITE+"Loads:")
    for i in range(m):
        print(convert_bool_to_dec([model.evaluate(C[i][k]) for k in range(max_load_bits)]))

    for i in range(m):
        print(Fore.WHITE+f"Route for courier {i}\n")
        for j in range(n+1):
            for k in range(n+1): 
                value = model.evaluate(G[i][j][k])
                if value==True:
                    print(Fore.GREEN + f'{value}:{D[j][k]}', end='\t')
                else:
                    print(Fore.RED + f'{value}', end='\t')
            print()
        print()

    print(Fore.WHITE+"Visiting orders")
    for j in range(n):
        for k in range(n):
            value = model.evaluate(V[j][k])
            if value==True:
                print(Fore.GREEN + f'{value}', end='\t')
            else:
                print(Fore.RED + f'{value}', end='\t')
        print()
    print()

elif res==unsat:
    print("Unsatisfiable.")
else:
    print("No optimal solution found")
    model=o.model()
    print(Fore.WHITE+f"Sub-Optimal Maximum Distance is"+ Fore.MAGENTA + f" {convert_bool_to_dec([model.evaluate(Max_Dist[i]) for i in range(UB_bits)])}")
end_optimize = time.time()
print(Fore.WHITE + f"Solution time: "+ Fore.MAGENTA+f"{end_optimize-start_optimize}")
print(Fore.WHITE + f"Total time: "+ Fore.MAGENTA+f"{end_encode+end_optimize-start_encode-start_optimize}")