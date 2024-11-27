# Parameters
param n;  # Number of distribution points (objects)
param m;  # Number of couriers
param D{1..n+1, 1..n+1};  # Distance matrix where n is the depot
param l{1..m};  # Capacity of each courier
param s{1..n};  # Size of each object

param Q;  # Maximum load capacity of all couriers
param LB;
param UB;

# Decision Variables

var x{1..n+1, 1..n+1, 1..m} binary;  # Binary: 1 if courier k travels from i to j, 0 esle
var u{1..n} <= Q, integer;  # Variables for MTZ, one for each delivery point (depot excluded), ensuring u[j] is no greater than the maximum load capacity
#var w{1..n} >= 1, <= n, integer; # Variable for alternative subtour elimination

# Maximum distance traveled by any courier, lowerbound is the distance traveled to reach furthest point and return to depot
var maxDist >= LB, <= UB, integer;
/*
# Array to store the distance traveled by each courier
var distTraveled{1..m} >= 0, integer;
*/

# Objective: Minimize the maximum distance traveled by any courier
minimize MaxDistance:
    maxDist;

# Constraints
/*
# Channeling constraints to ensure that distTraveled is exactly the distance traveled by each courier
subject to DistanceConsistency{k in 1..m}:
    distTraveled[k] = sum {i in 1..n+1, j in 1..n+1} D[i,j] * x[i,j,k];
*/
# Each location is visited exactly once
subject to VisitOnce{j in 1..n}:
    sum {k in 1..m, i in 1..n+1} x[i,j,k] = 1;

# Couriers start and end at the depot
subject to StartAtDepot{k in 1..m}:
    sum {j in 1..n} x[n+1,j,k] = 1;

subject to EndAtDepot{k in 1..m}:
    sum {i in 1..n} x[i,n+1,k] = 1;

# Couriers avoid self-loops
subject to NoSelfLoops{k in 1..m, i in 1..n+1}:
    x[i,i,k] = 0;

# Flow conservation (balanced flow in and out)
subject to FlowConservation{k in 1..m, i in 1..n+1}:
    sum {j in 1..n+1} x[i,j,k] = sum {j in 1..n+1} x[j,i,k];

# Capacity constraints: courier load cannot exceed its capacity
subject to Capacity{k in 1..m}:
    sum {i in 1..n+1, j in 1..n} s[j] * x[i,j,k] <= l[k];

# Lower bound for u variable: ensure u[j] is at least the size of object j
subject to LowerBound_u{j in 1..n}:
    u[j] >= s[j];

# Eliminate subtours (MTZ method)
subject to SubtourElimination_MTZ{k in 1..m, i in 1..n, j in 1..n: i != j}:
    u[j] - u[i] >= s[j] - Q*(1 - x[i,j,k]);

# Constraints for alternative formulation of subtour elimination with variable w
/* subject to FirstVisit{k in 1..m, j in 1..n}:
    w[j] <= 1 + 2*n*(1 - x[n+1,j,k]);

subject to SuccessiveVisit1{k in 1..m, i in 1..n, j in 1..n}:
    w[j] - w[i] >= 1 - 2*n*(1 - x[i,j,k]);

subject to SuccessiveVisit2{k in 1..m, i in 1..n, j in 1..n}:
    w[j] - w[i] <= 1 + 2*n*(1 - x[i,j,k]); */

# Each courier delivers at least one item (implied by NoSelfLoops)
subject to NoIdleCourier{k in 1..m}:
    x[n+1, n+1, k] = 0;

# Symmetry breaking constraints

# Hierarchical constraint type 1

/*for {k1 in 1..m-1} {
    for {k2 in k1+1..m} {
        if l[k1] == l[k2] then {
            subject to HC1{i in 1..n+1, j in i+1..n}:
                x[n+1,j,k1] + x[n+1,i,k2] <= 1;
        }
    }
}*/  # Implemented and injected in python notebook

# Symmetric distance matrix
set J_set{k in 1..m} := 
    setof{j in 1..n: x[n+1, j, k] == 1} j; 

set I_set{k in 1..m} := 
    setof{i in 1..n: x[i, n+1, k] == 1} i;

subject to SymmetryBreakingConstraint{k in 1..m}:
    first(I_set[k]) <= first(J_set[k]);

# Constraint on objective function: ensure maxDist is at least the distance traveled by each courier
subject to MaxDistanceConstraint{k in 1..m}:
    sum {i in 1..n+1, j in 1..n+1} D[i,j] * x[i,j,k] <= maxDist;
/*
# Ensure maxDist is the maximum of distTraveled
subject to MaxDistConstraint{k in 1..m}:
    maxDist >= distTraveled[k];
*/