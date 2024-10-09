%Model for the CP solution of the CDMO project
include "globals.mzn";

%Instance Variables===============================================================================================================================
int: m;                               %Number of couriers
int: n;                               %Number of items
array [1..m] of var int: l;           %Array of maximum load sizes for each of the m couriers
array [1..n] of var int: s;           %Array of sizes for each of the n items
array [1..n+1,1..n+1] of var int: D;  %Matrix of distances from distribution point i to j

%Auxiliary Variables==============================================================================================================================


%Instance Variables
array [1..m,1..n+1] of var 1..n+1: Z; %Matrix where element i,j indicates that courier i will carry item j
                                        
%The converision from model 3.x to 4.x lead to a reduction of the search space in the Instance variable from (m+1)^((n+1)*(n+1)) to (m+1)^(m*(n+1))

array [1..m] of var int: Dist;          %Array which contains the distances travelled by each courier at the end of its juorney
                                                                      
%Lower Bound Definition===========================================================================================================================
%Each courier has to travel at least to the closest node
var int: LB = max([(D[n+1,j]+D[j,n+1]) | j in 1..n]);%One courier has to travel to the furthest node, assuming the triangular inequality is respected, in case each courier carries one item (n=m), the longest distance travelled is the round trip from to depot to the furthest node.
%var int: LB = sum(r in 0..div(n,m))(D[k,argmax(D[k, r*m+1..n])]);  
constraint (max(Dist[1..m])>=LB); %Each distance must  be higher than the lower bound

%Upper Bound Definition===========================================================================================================================
var int: UB = sum(j in 1..n+1)(max(D[j,1..n+1]));%In case there is only one courier and the courier takes the longest route for all items, this gives us the longest possible path
constraint (max(Dist[1..m])<UB);%Each distance must be lower than the upper bound

%Problem Constraints==============================================================================================================================
constraint forall(i in 1..m)(all_different(Z[i,1..n+1]));%Each row is a permutation of the elements
constraint forall(i in 1..m)(subcircuit(Z[i,1..n+1]));%Each permutation is a subcircuit of the complete graph
constraint forall(i in 1..m)(sum(j in 1..n where Z[i,j]!=j)(s[j])<=l[i]);%Load capacities must be respected
constraint forall(j in 1..n)((count(r in Z[1..m,j])(r!=j))==1); %Each item can only be carried by one courier
constraint forall(i in 1..m)(Z[i,n+1]!=(n+1)); %Each courier has to live the depot
constraint forall(i in 1..m) (Dist[i] = sum(j in 1..n+1 where Z[i,j]!=j)(D[j, Z[i,j]])); %Distance formulation

%Symmetry Breaking Constraints====================================================================================================================
constraint forall(i in 1..m, j in i+1..m where l[i]=l[j])(lex_lesseq(Z[i,1..n+1],Z[j,1..n+1])); %Ensure that two couriers with the same load size take different paths
constraint if forall(f in 1..n+1, g in 1..n where f != g)(
    D[f,g] == D[g,f]
) then
    forall(i in 1..m)(lex_lesseq(Z[i, 1..n+1], reverse(Z[i, 1..n+1]))) %In case the distance matrix is symmetric we ensure that each circuit is explored in only one direction
else
    true  % No constraint if the matrix is not symmetric
endif;

int: Scale=10;
%int: Base=2;
% 
solve :: int_search(Z, dom_w_deg, indomain_random, complete) minimize(max(Dist[1..m]))::restart_luby(Scale);
%solve minimize(max(Dist[1..m]));

%SOLUTIONS

%Tested Solver Configurations:
%(1) Gecode 6.3.0
%(2) Gecode 6.3.0 with dom_w_deg variable choice, indomain_random assigment
%(3) Gecode 6.3.0 with dom_w_deg variable choice, indomain_random assigment + Courier Symmetry Breaking
%(4) Gecode 6.3.0 with dom_w_deg variable choice, indomain_random assigment + Distance Symmetry Breaking 
%(5) Gecode 6.3.0 with dom_w_deg variable choice, indomain_middle assigment + Both Symmetry Breaking
