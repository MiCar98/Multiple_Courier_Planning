# Parameters
param m;  # Number of couriers
param n;  # Number of items to deliver/distribution points to visit
param l{1..m} >= 0;  # Load size of each courier
param s{1..n} >= 0;  # Size of each item
param D{1..n+1, 1..n+1};  # Distance matrix

# Decision Variables
var x{1..n+1, 1..n+1, 1..m} binary;
var y{1..n+1, 1..m} binary;
var u{1..n} >= 0 <= n;
var maxDist >= 0;  # Maximum distance traveled by any courier

# Objective: Minimize maximum distance traveled by any courier
minimize MaxDistance:
    maxDist;

# Constraints
# Each item should be delivered (each distribution point is visited exactly once).
subject to ItemDelivered{j in 1..n}:
    sum {k in 1..m, i in 1..n+1} x[i,j,k] = 1;

# Flow conservation
subject to FlowConservation{k in 1..m, i in 1..n+1}:
    sum {j in 1..n+1} x[i,j,k] = y[i,k];

subject to FlowConservation2{k in 1..m, j in 1..n+1}:
    sum {i in 1..n+1} x[i,j,k] = y[j,k];

# Couriers start and end at the depot
subject to StartAtDepot{k in 1..m}:
    sum {j in 1..n+1} x[0,j,k] = 1;

subject to EndAtDepot{k in 1..m}:
    sum {i in 1..n+1} x[i,0,k] = 1;

# Eliminate subtours
subject to SubtourElimination{i in 1..n+1, j in 1..n+1, k in 1..m}:
    u[i] - u[j] + (n+1) * x[i,j,k] <= n if i != j;

# Capacity constraints
subject to Capacity{k in 1..m}:
    sum {i in 1..n+1} d[i] * y[i,k] <= Q[k];

# Ensure maxDist is at least the distance traveled by each courier
subject to MaxDistanceConstraint{k in 1..m}:
    sum {i in 1..n+1, j in 1..n+1} D[i,j] * x[i,j,k] <= maxDist;