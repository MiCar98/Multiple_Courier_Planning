/*
Notation
node n+k: a fictitious start node with respect to vehicle k, acting as depot; we have d_n+k,j = d_0,j for all j, k (0 is intended as depot)
node n+m+k: a fictitious end node with respect to vehicle k, acting as depot; we have d_i,n+m+k = d_i,0 for all i, k (0 is intended as depot)
*/

# Parameters
param n;  # Number of distribution points (customers to visit/items to deliver)
param m;  # Number of couriers
param D{1..n+m, 1..n+2*m};  # Distance matrix
param l{1..m};  # Capacity of each courier
param s{1..n};  # Size of each item

param LB;  # lower bound of the objective, injected via python
param UB;  # upper bound of the objective, injected via python

param M1 := max {i in 1..n+1, j in 1..n+m+1} D[i,j] * (n + 2);  # Big M for constraints (22)-(24)

# Decision Variables
var x{1..n+2*m, 1..n+2*m} binary;  # Binary: 1 if arc ij is visited, 0 esle
var del{1..n+2*m, 1..m} binary;  # 1 if item i is delivered by courier j
var dist{1..n+2*m} >= 0, <= M1, integer;  # Distance traveled to reach node i
#var load{1..m} >= 0, integer;  # load of each courier when departing from depot

var maxDist >= LB, <= UB, integer;  # maximum distance traveled by any courier, lowerbound is the distance traveled to reach furthest point and return to depot

# Objective: Minimize the maximum distance traveled by any courier
minimize MaxDistance:
    maxDist;

# Constraints
# Each customer is visited exactly once
subject to VisitOnce{i in 1..n}:
    sum {j in 1..m} del[i,j] = 1;

# Allocating fictitious nodes to corresponding couriers such that they all start and end at depot
subject to StartAtDepot{k in 1..m}:
    del[n+k,k] = 1;

subject to EndAtDepot{k in 1..m}:
    del[n+m+k,k] = 1;

# Making sure that couriers' routes start and end at depot (x variable)
subject to StartAtDepotX{i in n+1..n+m}:
    sum{j in 1..n} x[i,j] = 1;

subject to EndAtDepotX{j in n+m+1..n+2*m}:
    sum{i in 1..n} x[i,j] = 1;

/* Constraints to ensure that the customers belonging to the same route are allocated to the same vehicle
Specifically, constraints C6, C7, C8 ensure that when the route is directly between two nodes in the
transportation network, then they should be allocated to the same vehicle (e.g. del[i,k]=del[j,k]).
If nodes i and j are not allocated to the same vehicle k, then x[i,j] = 0; however, if they are
allocated to the same vehicle k, then x[i,j] can be 0 or 1, based on the routing plan. */

subject to C6{i in 1..n, j in 1..n, k in 1..m: i != j}:
    abs(del[i,k] - del[j,k]) <= 1 - x[i,j];

subject to C7{i in 1..n, k in 1..m}:
    del[n+k,k] - del[i,k] <= 1 - x[n+k,i];

subject to C8{i in 1..n, k in 1..m}:
    del[n+m+k,k] - del[i,k] <= 1 - x[i,n+m+k];

# Constraint 9 ensures that if courier k gets assigned any item i.e. del[i,k] = 1, then the courier should be used in the plan, i.e. x[n+k,n+m+k] = 0.
subject to C9{i in 1..n, k in 1..m}:
    del[i,k] <= 1 - x[n+k,n+m+k];

/* Constraints (12) and (13) indicate that the total number of arcs selected in the final solution,
before and after visiting a customer/fictitious node, should be equal to 1. */
# After departing from a customer, we either visit exactly 1 other customer or we go back to the depot (exclusive or)
subject to C12{i in 1..n}:
    sum{j in 1..n} x[i,j] + sum{k in 1..m} x[i,n+m+k] = 1;

# Before visiting a customer, we either come from (only) 1 other node or from the depot (exclusive or).
subject to C13{j in 1..n}:
    sum{i in 1..n} x[i,j] + sum{k in 1..m} x[n+k,j] = 1;

/* Constraints (15) and (16) make sure that when a customer is visited as first/last customer in the
route, then the respective customer is also allocated to the same vehicle. */
# When customer is visited at first in the route of courier k it is assigned to courier k
subject to C15{i in 1..n, k in 1..m}:
    x[n+k,i] <= del[i,k];

# When customer is visited at last in the route of courier k it is assigned to courier k
subject to C16{i in 1..n, k in 1..m}:
    x[i,n+m+k] <= del[i,k];

/* Constraints (17)–(21) are introduced to restrict the subtours in the route sequence. */
# Constraint 17 avoids self-loops
subject to C17{i in 1..n}:
    x[i,i] = 0;

# Constraint 18 avoids that both arcs (i,j) and (j,i) are traveled
subject to C18{i in 1..n-1, j in i+1..n}:
    x[i,j] + x[j,i] <= 1;

# Constraint 19 ensures that no courier visits a customer after ending its route at depot
subject to C19{j in 1..n, k in 1..m}:
    x[n+m+k,j] = 0;

# Constraint 20 ensures that no courier goes to the starting depot after visiting a customer
subject to C20{i in 1..n, k in 1..m}:
    x[i,n+k] = 0;

# Constraint 21 ensures that no courier goes from ending depot to the starting depot
subject to C21{k in 1..m}:
    x[n+m+k,n+k] = 0;

/* Constraints (22)–(24) represent that if the arc between two nodes is selected/available as a part
of the travel plan, then the distance travelled to reach the second node from the first node is equal
to the travel distance between them */
subject to C22{i in 1..n, k in 1..m}:
    dist[i] >= D[n+k,i] - M1 * (1 - x[n+k,i]);

subject to C23{i in 1..n, j in 1..n: i != j}:
    dist[j] >= dist[i] + D[i,j] - M1 * (1 - x[i,j]);

subject to C24{i in 1..n, k in 1..m}:
    dist[n+m+k] >= dist[i] + D[i,n+m+k] - M1 * (1 - x[i,n+m+k]);

# Capacity constraint
subject to Capacity{k in 1..m}:
    sum{i in 1..n} del[i,k]*s[i] <= l[k];

# Constraint on objective function: ensure maxDist is at least the distance traveled by each courier
subject to MaxDistanceConstraint{k in 1..m}:
    sum{i in 1..n+k, j in 1..n+m+k} (D[i,j] * x[i,j] * del[j,k]) <= maxDist;
    #sum{i in 1..n, j in 1..n} (D[i,j] * del[j,k]) + sum{j in 1..n} (D[n+k,j] * x[n+k,j]) + sum{i in 1..n} (D[i,n+m+k] * x[i,n+m+k]) <= maxDist;