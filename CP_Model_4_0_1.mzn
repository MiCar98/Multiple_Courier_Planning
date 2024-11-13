%Model for the CP solution of the CDMO project
include "globals.mzn";

%Instance Variables===============================================================================================================================
int: m;                               %Number of couriers
int: n;                               %Number of items
array [1..m] of int: l;           %Array of maximum load sizes for each of the m couriers
array [1..n] of int: s;           %Array of sizes for each of the n items
array [1..n+1,1..n+1] of int: D;  %Matrix of distances from distribution point i to j
int: LB;
int: LLB;
int: UB;

%Auxiliary Variables==============================================================================================================================


%Instance Variables
array [1..m,1..n+1] of var 1..n+1: Z; %Matrix where element i,j indicates that courier i will carry item j
                                        
array [1..m] of var LLB..UB: Dist;          %Array which contains the distances travelled by each courier at the end of its juorney

array [1..n] of var 1..m: Carry;
                                                                      
%Lower Bound Definition===========================================================================================================================
%At least one courier must travel to the furthest node, assuming trinagular inequality, this is the lower bound for maximum distance
constraint (max(Dist[1..m])>=LB); %The maximum distance must be higher than the lower bound.

%Problem Constraints==============================================================================================================================

constraint forall(i in 1..m)(subcircuit(Z[i,1..n+1]));%Z[i,1..n+1],ch permutation is a subcircuit of the complete graph
constraint forall(i in 1..m)(sum(j in 1..n where Z[i,j]!=j)(s[j])<=l[i]);%Load capacities must be respected
constraint forall(j in 1..n)((count(r in Z[1..m,j])(r!=j))==1); %Each item can only be carried by one courier
constraint forall(i in 1..m)(Z[i,n+1]!=(n+1)); %Each courier has to live the depot
constraint forall(i in 1..m) (Dist[i] = sum(j in 1..n+1 where Z[i,j]!=j)(D[j, Z[i,j]])); %Distance formulation

%Redundant Constraints
constraint forall(i in 1..m)(all_different(Z[i,1..n+1]));%Each row is a permutation of the elements
constraint forall(i in 1..m, j in 1..n where Z[i,j]!=j) (Carry[j] = i); %Carry assignement formulation
constraint bin_packing_capa(l, Carry, s); %Load Capacities must be respected

%Symmetry Breaking Constraints====================================================================================================================
%constraint forall(i in 1..m, j in i+1..m where l[i]=l[j])(lex_lesseq(Z[i, 1..n+1], Z[j,1..n+1])); %Ensure that two couriers with the same load size take different paths


%SOLVER CONFIGURATIONS

%Configuration 1
%solve :: int_search(Z, dom_w_deg, indomain_random, complete) minimize(max(Dist[1..m]));

%Configuration 2
%solve :: seq_search([int_search(Z, first_fail, indomain_min, complete), int_search(Z, dom_w_deg, indomain_random,complete)])::restart_luby(10)::relax_and_reconstruct(array1d(Z),50)minimize(max(Dist[1..m]));

%Configuration 3
%solve :: seq_search([int_search(Z,first_fail,indomain_random, complete), int_search(Z,dom_w_deg,indomain_random,complete)])::restart_luby(10)::relax_and_reconstruct(array1d(Z),60)minimize(max(Dist[1..m]));

%Configuration 4
solve :: seq_search([int_search(Z,first_fail,indomain_random, complete), int_search(Z,dom_w_deg,indomain_random,complete)])::restart_luby(10)::relax_and_reconstruct(array1d(Z),70)minimize(max(Dist[1..m]));


