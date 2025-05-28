# Multiple Couriers Planning Problem

**The project models and solves the Multiple Couriers Planning (MCP) problem using four paradigms: Constraint Programming (CP), propositional SATisfiability (SAT), Satisfiability Modulo Theories (SMT) and Mixed-Integer Linear Programming (MIP).**

---

## 1. Problem Description & Motivation  

The exponential growth of e-commerce—accelerated by the COVID-19 pandemic—has turned last-mile logistics into a strategic asset. Companies must dispatch thousands of parcels every day through fleets of couriers while keeping operating costs low and workloads fair.

Multiple Couriers Planning (MCP) captures this decision problem:

• We have m couriers, each with a capacity limit lᵢ.  
• We have n (≥ m) items. Item j has a customer location j and a size sⱼ.  
• D is the distance matrix, containing at Di,j the distance from node i to node j, with node n + 1 being the depot node.  
• For each courier, we must choose which items to deliver and in which order to visit the corresponding customer locations.  
• Every tour starts and ends at a common depot o, must respect capacity, and our objective is to **minimise the maximum tour length among all couriers** (min–max fairness).

The goals are to:

1. Formalise MCP under different optimisation paradigms (CP, SAT, SMT, MIP).  
2. Implement the models and configure state-of-the-art solvers.  
3. Run an experimental study comparing performance.

---

## 2. Approach & Solution Overview  

### Common Modelling Choices  
• Lower/upper bounds on the objective function to tighten the search space.  
• Implied constraints and global constraints (in CP) are exploited.  
• Symmetry-breaking constraints reduce duplicate search.  
• All solvers were capped at **300 s** wall-clock time to compare the different approaches fairly.
• Random seeds for each approach and solver were fixed for reproducibility.
• To be reproducible, the code was executed through Docker.

---

## 3. Results  

The different models were tested on 21 instances, the first 10 being easier (with m and n ranging from 2, 3 to 10, 13) and the remaining being hard-to-solve instances (with m and n ranging from 20, 47 to 20, 287). Even with a strict five-minute cutoff, the four paradigms behaved very differently:

• **CP is the clear winner**: it produced a feasible solution for all 21 instances within the time limit, and reached the optimal solution for every easy instance and 3 of the hardest ones.  
• **MIP shows promise on large cases**: although its formulations are heavier, the model optimally solved the first 10 instances and solved 4 of the hard ones, reaching the optimal solution twice.  
• **SMT lags due to encoding overhead**: the expressive, solver-independent model captures high-level logic cleanly, but the resulting ground problem is significantly larger, hurting runtime. The model can optimally solve the first 10 instances but finds a feasible (not optimal) solution for just 2 of the larger instances.  
• **SAT performed worst**: in several instances, the Boolean encoding alone exceeded the time limit, preventing the solver from even starting the search. The model is able to optimally solve 9 of the first 10 instances and found a feasible solution for the remaining one. No hard instance was solved.
 
