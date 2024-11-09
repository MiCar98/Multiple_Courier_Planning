import datetime
from minizinc import Instance, Model, Solver
import numpy as np
def Solve_CP(n_couriers, n_items, courier_loads, item_sizes, distances, upper_bound, lower_bound, minimum_distance, simple=True ,solver_name='gecode'):

    solver = Solver.lookup(solver_name)
    
    if simple:
        MCP = Model("CP_Model_4_0_1_easy.mzn")
    else:
        MCP = Model("CP_Model_4_0_1_hard.mzn")

    MCP_instance = Instance(solver, MCP)

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



    #Check if the distance matrix is symmetric and apply symmetry breaking constraint if so
    if np.all(distances == distances.T):
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
