import datetime, os, re
from minizinc import Instance as mzn_Instance
from minizinc import Solver as mzn_Solver
from minizinc import Model as mzn_Model
import numpy as np
import time, math
from z3 import *
from SAT_utils import *
#from amplpy import AMPL

def Solve_CP(n_couriers, n_items, courier_loads, item_sizes, distances, upper_bound, lower_bound, minimum_distance, simple=True, solver_name='gecode', break_symmetry=True):

    encoding_start = time.time()
    solver = mzn_Solver.lookup(solver_name)
    
    if simple:
        MCP = mzn_Model("CP_Model_4_0_1_easy.mzn")
    else:
        MCP = mzn_Model("CP_Model_4_0_1_hard.mzn")

    MCP_instance = mzn_Instance(solver, MCP)

    MCP_instance['m']=n_couriers
    MCP_instance['n']=n_items
    MCP_instance['l']=courier_loads
    MCP_instance['s']=item_sizes
    MCP_instance['D']=distances

    MCP_instance["LB"]=lower_bound
    print(MCP_instance["LB"])
    MCP_instance["LLB"]=minimum_distance
    print(MCP_instance["LLB"])
    MCP_instance["UB"]=upper_bound
    print(MCP_instance["UB"])


    name=''
    #Check if the distance matrix is symmetric and apply symmetry breaking constraint if so
    if break_symmetry and np.all(distances == distances.T):
        print("Matrix is symmetric")
        name=solver_name+'_symmetry_break'
        MCP_instance.add_string("constraint forall(i in 1..m)(arg_max(Z[i,1..n+1])>Z[i,n+1]);")
    else:
        name=solver_name    

    encoding_stop = time.time()
    encoding_time = encoding_stop-encoding_start    
    #Solve computing the solution
    to = datetime.timedelta(seconds=300-math.floor(encoding_time))
    solving_start = time.time()
    print(f"Solving the problem with\nnumber of couriers = {MCP_instance['m']}\nnumber of items = {MCP_instance['n']}\n")
    result = MCP_instance.solve(timeout=to)#, intermediate_solutions=True)
    solving_stop = time.time()
    solving_time = solving_stop-solving_start

    #Extract the solution variable
    # print('SOLUTION'+92*'=')
    # Znp = np.array(result["Z"])
    # Zc, Zi = Znp.shape
    # for c in range(Zc):
    #     print(f"Path for courier {c+1}")
    #     node = Znp[c][Zi-1]
    #     print('Depot', end='--->')
    #     while node!=Zi:
    #         print(node, end='--->')
    #         node = Znp[c][node-1]
    #     print("Depot")
    #     print()

        
    # print(f"Optimal maximum distance found = {result['objective']}")
    # print(100*'='+ '\n')
    Znp = np.array(result["Z"])
    Zc, Zi = Znp.shape
    solution = []
    for c in range(Zc):
        node = Znp[c][Zi-1]
        path = []
        while node!=Zi:
            path.append(node)
            node = Znp[c][node-1]
        solution.append(path)

    tot_time = encoding_time + solving_time
    if math.floor(tot_time)<300:
        optimal='true'
    else:
        optimal='false'

    results = {
        "approach":name,
        "time":math.floor(tot_time),
        "optimal":optimal,
        "obj":result['objective'],
        "sol":solution
    }

    return results


def Solve_SAT(n_couriers, n_items, courier_loads, item_sizes, distances, upper_bound, lower_bound, minimum_distance, break_symmetry=False):
    encoding_start=time.time()
    #Convert all parameter values into boolean arrays
    max_load = max(sum(item_sizes), max(courier_loads))
    max_load_bits = convert_dec_to_bool(max_load)['Num_bits']
    UB_bits = convert_dec_to_bool(upper_bound)['Num_bits']
    Dist = [[Bool(f"dist_{i}_bit_{j}") for j in range(UB_bits)] for i in range(n_couriers)]
    C = [[Bool(f"courier_load_{i}_bit_{j}") for j in range(max_load_bits)] for i in range(n_couriers)]
    Max_Dist = [Bool(f"Max_Dist_bit_{i}") for i in range(UB_bits)]

    l_bool = [convert_dec_to_bool(courier_loads[i], max_load_bits)['Conversion'].tolist() for i in range(len(courier_loads))]
    s_bool = [convert_dec_to_bool(item_sizes[i], max_load_bits)['Conversion'].tolist() for i in range(len(item_sizes))]
    D_bool = [[convert_dec_to_bool(distances[i][j], UB_bits)['Conversion'].tolist() for j in range(len(distances[i]))] for i in range(len(distances))]

    LB_bool = convert_dec_to_bool(lower_bound, UB_bits)['Conversion'].tolist()
    UB_bool = convert_dec_to_bool(upper_bound, UB_bits)['Conversion'].tolist()
    LLB_bool = convert_dec_to_bool(minimum_distance, UB_bits)['Conversion'].tolist()

    #Delivery assignment matrix
    A = [[Bool(f"a_{i}_{j}") for j in range(n_items)] for i in range(n_couriers)]

    #Graph matrix
    G = [[[Bool(f"g_{i}_{j}_{k}") for k in range(n_items+1)] for j in range(n_items+1)] for i in range(n_couriers)]

    #Visit sequence matrix
    V = [[Bool(f"visit_item_{j}_as_{k}") for k in range(n_items)] for j in range(n_items)]

    
    #Constraint 1: Every item is carried
    const_1 = And(
        *[exactly_one_np([A[i][j] for i in range(n_couriers)], f'Item_{j}_is_carried_once') for j in range(n_items)]
    )

    #Constraint 2: Loads computation constraint
    const_2 = And(
        *[sum_cond_on_array_constraint(C[i], s_bool, A[i], f'Full_Load_Courier_{i}') for i in range(n_couriers)]
    )

    #Constraint 3: Load capacities must be respected
    const_3 = And(
        *[compare(C[i], l_bool[i], '<=') for i in range(n_couriers)]
    )

    #Constraint 4: every courier delivers at least one item
    const_4 = And(
        *[at_least_one_np(A[i]) for i in range(n_couriers)]
    )

    #Constraint 5: every node is visited once
    const_5 = And(
        *[exactly_one_np(V[j], f"Item_{j}_in_only_one_path") for j in range(n_items)]
    )

    #Constraint 6: No self-loops
    const_6 = And(
        *[And(*[Not(G[i][j][j]) for j in range(n_items+1)]) for i in range(n_couriers)]
    )

    #Constraint 7: Channeling between assignment and routing - departure from node j
    const_7 = And(
        *[And(*[(Implies(A[i][j], exactly_one_np(G[i][j],  f'Courier_{i}_departs_from_node_{j}'))) for j in range(n_items)], 
            *[(Implies(Not(A[i][j]), Not(Or(G[i][j])))) for j in range(n_items)]) 
            for i in range(n_couriers)]
    )

    #Constraint 8: Channeling between assignment and routing - arrival to node k
    const_8 = And(
        *[And(*[(Implies(A[i][k], exactly_one_np([G[i][j][k] for j in range(n_items+1)], f'Courier_{i}_arrives_at_node_{k}'))) for k in range(n_items)], 
            *[(Implies(Not(A[i][k]), Not(Or([G[i][j][k] for j in range(n_items+1)])))) for k in range(n_items)]) 
            for i in range(n_couriers)]
    )


    #Constraint 9: Every courier leaves the Depot
    const_9 = And(
        *[exactly_one_np(G[i][n_items], f'Courier_{i}_leaves_Depot') for i in range(n_couriers)]
    )

    #Constraint 10: Every couriers returns to the Depot
    const_10 = And(
        *[exactly_one_np([G[i][j][n_items] for j in range(n_items+1)], f'Courier_{i}_returns_to_Depot') for i in range(n_couriers)]
    )


    #Constraint 11: Subtour elimination constraint
    const_11 = And(
                *[And(
                    *[And(
                        *[Implies(G[i][j][k], consecutive(V[j], V[k])) for k in range(n_items)],
                        Implies(G[i][n_items][j], V[j][0])) 
                    for j in range(n_items)])
                for i in range(n_couriers)])

    #Constraint 12: Distance computation constraint
    const_12 = And(
        *[sum_cond_on_array_constraint(Dist[i], flatten(D_bool), flatten(G[i]), f'Distance_Courier_{i}') for i in range(n_couriers)]
    )

    #Constraint 13: Max_dist is the maximum distance
    const_13 = And(
        *[compare(Max_Dist, Dist[i], '>=') for i in range(n_couriers)]
    )

    #Constraint 14: Max_dist must be equal to one of the distances
    const_14 = Or(
        *[compare(Max_Dist, Dist[i], '==') for i in range(n_couriers)]
    )

    name=''
    if break_symmetry:
        name='symmetry_break'
        #constraint to break symmetry
    else:
        name='basic'


    #Lower bound constraint
    lb_const = compare(Max_Dist, LB_bool, '>=')
    #Upper bound constraint
    ub_const = And(
        *[compare(Dist[i], UB_bool, '<=') for i in range(n_couriers)]
    )
    llb_const = And(
        *[compare(Dist[i], LLB_bool, '>=') for i in range(n_couriers)]
    )

    o = Optimize()

    o.add(const_1) 
    o.add(const_2) 
    o.add(const_3)
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
    o.add(const_14) 

    o.add(lb_const)
    o.add(ub_const)
    o.add(llb_const)

    encoding_stop = time.time()
    encoding_time = encoding_stop - encoding_start

    solving_start = time.time()
    o.set("timeout", math.floor(300000-encoding_time*1000))
    objective = Sum([If(Max_Dist[i], 2**(len(Max_Dist)-i), 0) for i in range(len(Max_Dist))])
    o.minimize(objective)

    res = o.check()
    if res == sat:
        model=o.model()

        obj=convert_bool_to_dec([model.evaluate(Max_Dist[i]) for i in range(UB_bits)])

        result = []
        for i in range(n_couriers):
            courier_route=[]
            for j in range(n_items+1):
                row=[]
                for k in range(n_items+1):
                    row.append(model.evaluate(G[i][j][k]))
                courier_route.append(row)
            result.append(courier_route)
        
        paths = decode_paths(result, n_couriers, n_items)




    elif res==unsat:
        print("Unsatisfiable.")
    else:
        print("No optimal solution found")
        model=o.model()
        obj=convert_bool_to_dec([model.evaluate(Max_Dist[i]) for i in range(UB_bits)])

        result = []
        for i in range(n_couriers):
            courier_route=[]
            for j in range(n_items):
                row=[]
                for k in range(n_items):
                    row.append(model.evaluate(G[i][j][k]))
                courier_route.append(row)
            result.append(courier_route)
        
        paths = decode_paths(result, n_couriers, n_items)
    
    
    solving_stop = time.time()
    solving_time = solving_stop-solving_start
    tot_time = encoding_time+solving_time

    if math.floor(tot_time)<300:
        optimal='true'
    else:
        optimal='false'

    results = {
        "approach":name,
        "time":math.floor(tot_time),
        "optimal":optimal,
        "obj":obj,
        "sol":paths
    }

    return results
def Solve_SMT(num_couriers, num_objects, capacities, weights, distance_matrix, upper_bound, lower_bound, break_symmetry=False):
    depot = num_objects  # Index for the depot (last element in distance matrix)
    

    LB=lower_bound
    UB=upper_bound


    print(f"Lower Bound (LB): {LB}")
    print(f"Upper Bound (UB): {UB}")

    # Variables, constraints, and solver setup
    load = [Int(f'load_{i}') for i in range(num_couriers)]
    assignments = [[Bool(f'assignments_{i}_{j}') for j in range(num_objects)] for i in range(num_couriers)]
    route = [[[Bool(f'route_{i}_{j}_{k}') for k in range(num_couriers)] for j in range(len(distance_matrix))] for i in range(len(distance_matrix))]
    visit_order = [[Int(f'visit_order_{j}_{k}') for j in range(num_objects + 1)] for k in range(num_couriers)]

    solver = Optimize()



    # Constraint: Each item should be assigned to exactly one courier
    for j in range(num_objects):
        solver.add(Or([assignments[k][j] for k in range(num_couriers)]))  # At least one assignment
        for k1, k2 in combinations(range(num_couriers), 2):
            solver.add(Or(Not(assignments[k1][j]), Not(assignments[k2][j])))  # At most one assignment

    # Load and capacity constraints for each courier
    for i in range(num_couriers):
        # Each load is the sum of weights assigned to the courier
        solver.add(load[i] == Sum([If(assignments[i][j], weights[j], 0) for j in range(num_objects)]))
        solver.add(load[i] <= capacities[i])

# Channeling constraints between assignments and routes
    for k in range(num_couriers):
        for j in range(num_objects):
            # If item `j` is assigned to courier `k`, courier `k` must visit `j`
            solver.add(Implies(assignments[k][j], Or([route[i][j][k] for i in range(num_objects + 1) if i != j])))

            # If there's a route to item `j` for courier `k`, item `j` must be assigned to courier `k`
            solver.add(Implies(Or([route[i][j][k] for i in range(num_objects + 1) if i != j]), assignments[k][j]))

    # Ensure each courier starts from and returns to the depot
    for k in range(num_couriers):
        # Courier `k` should start at the depot, with exactly one route from the depot to some other point
        solver.add(Sum([If(route[depot][j][k], 1, 0) for j in range(num_objects)]) == 1)

        # Courier `k` should return to the depot, with exactly one route to the depot from some other point
        solver.add(Sum([If(route[j][depot][k], 1, 0) for j in range(num_objects)]) == 1)

    # Flow control to prevent subtours and ensure continuous paths
    for k in range(num_couriers):
        solver.add(visit_order[k][depot] == 0)  # Depot is the starting point

        for j in range(num_objects + 1):
            # Ensure that each non-depot location (assigned location) has exactly one incoming and one outgoing route if visited
            if j != depot:
                solver.add(Sum([If(route[i][j][k], 1, 0) for i in range(num_objects + 1) if i != j]) == If(assignments[k][j], 1, 0))
                solver.add(Sum([If(route[j][i][k], 1, 0) for i in range(num_objects + 1) if i != j]) == If(assignments[k][j], 1, 0))

        # Enforce continuity in visit order if there is a route from i to j for courier k
        for i in range(num_objects + 1):
            for j in range(num_objects + 1):
                if i != j and j != depot:
                    solver.add(Implies(route[i][j][k], visit_order[k][j] == visit_order[k][i] + 1))

    # Objective: Minimize maximum distance traveled by any courier, within bounds
    max_distance = Int("max_distance")
    total_distance = [Int(f"total_distance_{i}") for i in range(num_couriers)]


    for k in range(num_couriers):
        # Sum distances for the route of each courier
        solver.add(total_distance[k] == Sum([If(route[i][j][k], distance_matrix[i][j], 0)
                                            for i in range(len(distance_matrix))
                                            for j in range(len(distance_matrix))]))
        solver.add(total_distance[k] <= max_distance)  # Ensure max_distance bounds each courier's total distance

    solving_start = time.time()
    solver.minimize(max_distance)  # Minimize the maximum distance among all couriers

    # Add bounds as constraints
    solver.add(IntVal(LB) <= max_distance)
    solver.add(max_distance <= IntVal(UB))

    # Solve and output the solution
    if solver.check() == sat:
        model = solver.model()
        loads = [model.evaluate(load[i]) for i in range(num_couriers)]
        assignments_values = [[model.evaluate(assignments[i][j]) for j in range(num_objects)] for i in range(num_couriers)]
        distances = [model.evaluate(total_distance[i]) for i in range(num_couriers)]
        print("Loads per courier:", loads)
        print("Assignments:", assignments_values)
        print("Distances per courier:", distances)
        print("Max distance:", model.evaluate(max_distance))

        for k in range(num_couriers):
            print(f"Courier {k + 1}:")
            for i in range(len(distance_matrix)):
                for j in range(len(distance_matrix)):
                    if is_true(model.evaluate(route[i][j][k])):
                        print(f"  Point {i + 1} -> Point {j + 1}")
        

    else:
        print("No solution found.")
    result = []
    for i in range(num_couriers):
        courier_route=[]
        for j in range(num_objects+1):
            row=[]
            for k in range(num_objects+1):
                row.append(model.evaluate(route[j][k][i]))
            courier_route.append(row)
        result.append(courier_route)
        
    paths = decode_paths(result, num_couriers, num_objects)
    
    
    solving_stop = time.time()

    solving_time = solving_stop-solving_start
    tot_time = solving_time

    if math.floor(tot_time)<300:
        optimal='true'
    else:
        optimal='false'

    results = {
        "approach":'SMT_'+str(break_symmetry),
        "time":math.floor(tot_time),
        "optimal":optimal,
        "obj":model.evaluate(max_distance),
        "sol":paths
    }

    return results



# def Solve_MIP(m, n, l, s, D, upper_bound, lower_bound, solver_name='gurobi', break_symmetry=False):
#     ampl = AMPL()

#     is_symmetric = np.array_equal(D, D.T)
#     if is_symmetric and break_symmetry:
#         ampl.read("model1_sb.mod")
#     else:
#         ampl.read("model1.mod")

#     ampl.get_parameter("n").set(n)
#     ampl.get_parameter("m").set(m)
#     D_dict = {(i+1, j+1): D[i, j] for i in range(D.shape[0]) for j in range(D.shape[1])}
#     ampl.get_parameter("D").setValues(D_dict)
#     ampl.get_parameter("l").setValues({i+1: l[i] for i in range(len(l))})
#     ampl.get_parameter("s").setValues({i+1: s[i] for i in range(len(s))})
#     ampl.get_parameter("Q").set(int(max(l)))
#     ampl.get_parameter("LB").set(lower_bound)
#     ampl.get_parameter("UB").set(upper_bound)

#     # Enforce symmetry breaking constraints if break_simmetry parameter is true
#     if break_symmetry:
#         # Implementing hierarchical constarint type 1 (HC1)
#         # Partition the couriers based on their load capacity
#         courier_partitions = {}
#         for idx, capacity in enumerate(l):
#             if capacity not in courier_partitions:
#                 courier_partitions[capacity] = []
#             courier_partitions[capacity].append(idx + 1)

#         # Given a courier with index k, find the courier with the same capacity and the largest index smaller than k
#         for k in range(2, m+1):
#             # Get the capacity of the given courier
#             courier_capacity = l[k - 1]

#             # Find the couriers with the same capacity and smaller index
#             same_capacity_couriers = [idx for idx in courier_partitions[courier_capacity] if idx < k]

#             # Get the courier with the largest index among them
#             if same_capacity_couriers:
#                 largest_index_courier = max(same_capacity_couriers)

#         for k in range(2, m+1):
#             courier_capacity = l[k - 1]
#             same_capacity_couriers = [idx for idx in courier_partitions[courier_capacity] if idx < k]
#             if same_capacity_couriers:
#                 largest_index_courier = max(same_capacity_couriers)
#                 for j in range(1, n+1):
#                     ampl.eval(f"subject to HC1_{k}_{j}: sum {{i in 1..n+1}} x[i, {j}, {k}]  <= sum {{j_prime in 1..{j}-1}} sum {{i in 1..n+1}} x[i, j_prime, {largest_index_courier}];")

#         # Hierarchical constraint on first item delivered
#         for k1 in range(1, m):
#             for k2 in range(k1+1, m+1):
#                 if l[k1-1] == l[k2-1]:
#                     for i in range(1, n+1):
#                         for j in range(i+1, n+1):
#                             ampl.eval(f"subject to HC1_{k1}_{k2}_{i}_{j}: x[n+1,{j},{k1}] + x[n+1,{i},{k2}] <= 1;")    

#     ampl.setOption('randseed', 42)
#     ampl.setOption("solver", solver_name)
#     ampl.setOption(solver_name + "_options", "timelim=300 timing=2 seed=42")
#     solver_output = ampl.get_output("solve;")
#     solver_time_match = re.search(r"Solver time = ([\d.]+)s", solver_output)
#     solver_time = float(solver_time_match.group(1)) if solver_time_match else None

#     # Extract the solution variable
#     print('SOLUTION'+92*'=')
    
#     x = ampl.getVariable("x").getValues()
#     u = ampl.getVariable("u").getValues()
#     maxDist = int(ampl.getVariable("maxDist").value())
    
#     print(f"Optimal maximum distance found = {maxDist}")
#     print(100*'='+ '\n')

#     xnp = x.to_pandas().values.reshape((n+1, n+1, m))
#     solution = []
#     for k in range(1, m + 1):
#         path = []
#         current_node = n + 1
#         while True:
#             next_node = None
#             for i in range(1, n + 1):
#                 if xnp[current_node-1, i-1, k-1] > 0.5:
#                     next_node = i
#                     break
#             if next_node is None:
#                 break
#             path.append(next_node)
#             current_node = next_node
#         solution.append(path)
#         print(f"Path for courier {k}: {'--->'.join(map(str, path))}")
#         print()

#     if math.floor(solver_time)<300:
#         optimal='true'
#     else:
#         optimal='false'

#     results = {
#         "approach":solver_name + ' + SB' if break_symmetry else solver_name,
#         "time":math.floor(solver_time),
#         "optimal":optimal,
#         "obj":maxDist,
#         "sol":solution
#     }

#     return results