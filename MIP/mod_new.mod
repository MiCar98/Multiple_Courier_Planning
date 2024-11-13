# Parameters
param n;  # Number of distribution points (objects)
param m;  # Number of couriers
param D{1..n+1, 1..n+1};  # Distance matrix where n is the depot
param l{1..m};  # Capacity of each courier
param s{1..n};  # Size of each object

param Q := max {k in 1..m} l[k];
param LB;
param UB;

# Decision Variables
var A{1..n+1, 1..n+1} >= 0, <= m, integer;
var B{1..n} >= 1, <= m, integer;
#var u{1..n} <= Q, integer;  # Variables for MTZ, one for each delivery point (depot excluded)

# Maximum distance traveled by any courier
var maxDist >= LB, <= UB, integer;

# Objective: Minimize the maximum distance traveled by any courier
minimize MaxDistance:
    maxDist;



# Constraints
#subject to LowerBound_u{j in 1..n}:
#    u[j] >= s[j];



# Ensure maxDist is at least the distance traveled by each courier
subject to MaxDistanceConstraint{k in 1..m}:
    sum {i in 1..n+1, j in 1..n+1} (if A[i,j] = k then 1 else 0)*D[i,j] <= maxDist;


# Each location is visited exactly once
subject to VisitOnce{j in 1..n}:
    sum {i in 1..n+1} A[i,j] = B[j];

# Couriers start and end at the depot
subject to StartAtDepot:
    sum {i in 1..n} A[n+1,i] = sum {k in 1..m} k;

subject to EndAtDepot:
    sum {i in 1..n} A[i,n+1] = sum {k in 1..m} k;

# Flow conservation (balanced flow in and out)
subject to FlowConservation{i in 1..n+1}:
    sum {j in 1..n+1} A[i,j] = sum {j in 1..n+1} A[j,i];

# Couriers avoid self-loops
subject to NoSelfLoops{i in 1..n+1}:
    A[i,i] = 0;

# Capacity constraints: courier load cannot exceed its capacity
subject to Capacity{i in 1..m}:
    sum {j in 1..n} (if B[j] = i then 1 else 0)*s[j] <= l[i];

# Eliminate subtours (MTZ method)
#subject to SubtourElimination_MTZ{k in 1..m, i in 1..n, j in 1..n: i != j and (A[i,j]=k or A[i,j]=0)}:
 #   u[j] - u[i] >= s[j] - Q*(k - A[i,j]);

subject to NoSubtourTry{i in 1..n}:
    sum {j in 1..n+1} A[i,j] = B[i];

subject to NoBounceBack{i in 1..n+1, j in 1..n+1}:
    A[i,j]*A[j,i] = 0;
