# Parameters
param n;  # Number of distribution points (objects)
param m;  # Number of couriers
param D{0..n, 0..n};  # Distance matrix where n is the depot
param l{1..m};  # Capacity of each courier
param s{0..n-1};  # Size of each object

param Q := max {k in 1..m} l[k];


# Decision Variables
var x{0..n, 0..n, 1..m} binary;  # Binary: 1 if courier k travels from i to j, 0 esle
var u{0..n-1};  # Variables for MTZ, one for each delivery point (depot excluded)

# Maximum distance traveled by any courier, upperbound is the distance traveled to reach furthest point and return to depot
var maxDist >= max {j in 0..n-1} (D[n, j] + D[j, n]);


# Objective: Minimize the maximum distance traveled by any courier
minimize MaxDistance:
    maxDist;

# Ensure u[j] is at least the size of object j
subject to LowerBound_u{j in 0..n-1}:
    u[j] >= s[j];

# Ensure u[j] is no greater than the maximum load capacity
subject to UpperBound_u{j in 0..n-1}:
    u[j] <= Q;

# Each location is visited exactly once
subject to VisitOnce{j in 0..n-1}:
    sum {k in 1..m, i in 0..n} x[i,j,k] = 1;

# Flow conservation (balanced flow in and out)
subject to FlowConservation{k in 1..m, i in 0..n}:
    sum {j in 0..n} x[i,j,k] = sum {j in 0..n} x[j,i,k];

# Couriers start and end at the depot
subject to StartAtDepot{k in 1..m}:
    sum {j in 0..n-1} x[n,j,k] = 1;

subject to EndAtDepot{k in 1..m}:
    sum {i in 0..n-1} x[i,n,k] = 1;

# Couriers avoid self-loops
subject to NoSelfLoops{k in 1..m, i in 0..n}:
    x[i,i,k] = 0;

# Eliminate subtours (MTZ method)
subject to SubtourElimination_MTZ{k in 1..m, i in 0..n-1, j in 0..n-1: i != j}:
    u[j] - u[i] >= s[j] - Q*(1 - x[i,j,k]);


# Capacity constraints: courier load cannot exceed its capacity
subject to Capacity{k in 1..m}:
    sum {i in 0..n, j in 0..n-1} s[j] * x[i,j,k] <= l[k];

# Symmetry breaking constraints

set J_set{k in 1..m} := 
    setof{j in 0..n-1: x[n, j, k] >= 1} j; 

set I_set{k in 1..m} := 
    setof{i in 0..n-1: x[i, n, k] >= 1} i;

subject to SymmetryBreakingConstraint{k in 1..m}:
    first(I_set[k]) < first(J_set[k]);

# Ensure maxDist is at least the distance traveled by each courier
subject to MaxDistanceConstraint{k in 1..m}:
    sum {i in 0..n, j in 0..n} D[i,j] * x[i,j,k] <= maxDist;