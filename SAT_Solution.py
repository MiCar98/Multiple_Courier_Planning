from z3 import *
from Bool_utils import *



#Parameters instance 1

m = 2
n = 6
l= [15, 10]
s = [3, 2, 6, 5, 4, 4]
D = [[0, 3, 4, 5, 6, 6, 2],
     [3, 0, 1, 4, 5, 7, 3],
     [4, 1, 0, 5, 6, 6, 4],
     [4, 4, 5, 0, 3, 3, 2],
     [6, 7, 8, 3, 0, 2, 4],
     [6, 7, 8, 3, 2, 0, 4],
     [2, 3, 4, 3, 4, 4, 0]]

LB = 8
UB = 40


#Convert all parameter values into boolean arrays
max_load = sum(s)
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

#Delivery assignment matrix
A = [[Bool(f"a_{i}_{j}") for j in range(n)] for i in range(m)]

#Graph matrix
G = [[[Bool(f"g_{i}_{j}_{k}") for k in range(n+1)] for j in range(n+1)] for i in range(m)]

#Visit sequence matrix
#V = [[Bool(f"v_{j}_{k}") for k in range(n)] for j in range(n)]






#Constraint 1: Every item is carried
const_1 = And(
    *[exactly_one_np([A[i][j] for i in range(m)]) for j in range(n)]
)

#Constraint 2: Loads computation constraint
const_2 = And(
    *[sum_cond_on_array_constraint(C[i], s_bool, A[i], f'Full_Load_Courier_{i}') for i in range(m)]
)

#Constraint 3: Load capacities must be respected
const_3 = And(
    *[compare(C[i], l_bool[i], '<=') for i in range(m)]
)

#Constraint 4: Distance computation constraint
const_4 = And(
    *[sum_cond_on_array_constraint(Dist[i], flatten(D_bool), flatten(G[i]), f'Distance_Courier_{i}') for i in range(m)]
)

#Constraint 5: Channeling between assignment and routing
const_5 = And(
    *[And(*[(A[i][k]==exactly_one_np([G[i][j][k] for j in range(n+1)])) for k in range(n)], 
          *[(Not(A[i][k])==Not(Or([G[i][j][k] for j in range(n+1)]))) for k in range(n)]) 
          for i in range(m)]
)

#Constraint 6: Every courier leaves the Depot
const_6 = And(
    *[exactly_one_np([G[i][n][k] for k in range(n)]) for i in range(m)]
)

#Constraint 7: Every couriers returns to the Depot
const_7 = And(
    *[exactly_one_np([G[i][j][n] for j in range(n)]) for i in range(m)]
)

#Constraint 8: No self-loops
const_8 = And(
    *[And(*[Not(G[i][j][j]) for j in range(n+1)]) for i in range(m)]
)

#Constraint 9: Routes should be coherent
const_9 = And(
    *[And(*[exactly_one_np([G[i][k][j] for k in range(n+1)])==exactly_one_np([G[i][j][k] for k in range(n+1)]) for j in range(n+1)]) for i in range(m)]
)

#Constraint 10: Max_dist is the maximum distance
const_10 = And(
    *[compare(Max_Dist, Dist[i], '>=') for i in range(m)]
)

#Constraint 11: Subtour elimination constraint
...

#Lower bound constraints
lb_const = compare(Max_Dist, LB_bool, '>=')
ub_const = compare(Max_Dist, UB_bool, '<=')

o = Optimize()

o.add(const_1) #All carried
o.add(const_2) #Load computation
o.add(const_3) #Load limitation
o.add(const_4) #Distance computation
o.add(const_5) #Channel assignment <-> routing
o.add(const_6) #All leave depot
o.add(const_7) #All return to depot
o.add(const_8) #No self-loops
o.add(const_9) #Coherent routes
o.add(const_10) #Maximum distance is max of distances

o.add(lb_const)
o.add(ub_const)
# o.add(impl_const_1) #Sparse graph matrix

o.minimize(Int(convert_bool_to_dec(Max_Dist)))

if o.check() == sat:
    print("Satisfiable, with model:")
    model=o.model()

    print(f"Bool Maximum Distance is {[model.evaluate(Max_Dist[i]) for i in range(UB_bits)]}")
    print(f"Maximum Distance is {convert_bool_to_dec([model.evaluate(Max_Dist[i]) for i in range(UB_bits)])}")

    print(f"Assignments are: {[[model.evaluate(A[i][j]) for j in range(n)] for i in range(m)]}")

    print("Distances:")
    for i in range(m):
        print(convert_bool_to_dec([model.evaluate(Dist[i][k]) for k in range(UB_bits)]))

    for i in range(m):
        print(f"Route for courier {i}\n")
        for j in range(n+1):
            for k in range(n+1): 
                print(f"{model.evaluate(G[i][j][k])}", end='\t')
            print()
        print()




else:
    print("Unsatisfiable.")