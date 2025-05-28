# Combinatorial Decision Making & Optimization – Modelling and Solving the Multiple Couriers Planning Problem

**Repo for the CDMO exam (Master in Artificial Intelligence, University of Bologna, academic year 2023/2024, University of Bologna).  
The project models and solves the Multiple Couriers Planning (MCP) problem using four paradigms: Constraint Programming (CP), propositional SATisfiability (SAT), Satisfiability Modulo Theories (SMT) and Mixed-Integer Linear Programming (MIP).**

---

## 1. Problem Description & Motivation  

The exponential growth of e-commerce—accelerated by the COVID-19 pandemic—has turned last-mile logistics into a strategic asset. Companies must dispatch thousands of parcels every day through fleets of couriers while keeping operating costs low and workloads fair.

Multiple Couriers Planning (MCP) captures this decision problem:

• We have m couriers, each with a capacity limit lᵢ.  
• We have n (≥ m) items. Item j has a customer location j and a size sⱼ.  
• D is the distance matrix, containing at Di,j the distance from node i to node j, with node n + 1 being the depot node.
• For each courier we must choose which items to deliver and in which order to visit the corresponding customer locations.  
• Every tour starts and ends at a common depot o, must respect capacity, and our objective is to **minimise the maximum tour length among all couriers** (min–max fairness).

The project asks to:

1. Formalise MCP under different optimisation paradigms (CP, SAT, SMT, MIP).  
2. Implement the models and configure state-of-the-art solvers.  
3. Run an experimental study comparing performance.

---

## 2. Approach & Solution Overview  

### Common Modelling Choices  
• Lower/upper bounds on the objective function to tighten the search space.  
• Implied constraints and global constraints (in CP) are exploited.  
• Symmetry-breaking constraints reduce duplicate search.  
• All solvers were capped at **300 s** wall-clock time.

---

## 3. Results  

Even with a strict five-minute cutoff, the four paradigms behaved very differently:

• **CP is the clear winner**: it produced a feasible (often optimal) tour set for every single test instance within the 300 s limit.  
• **MIP shows promise on large cases**: although its formulations are heavier, commercial solvers (notably Gurobi) occasionally proved optimality on instances that other approaches left unresolved.  
• **SMT lags due to encoding overhead**: the expressive, solver-independent model captures high-level logic cleanly, but the resulting ground problem is significantly larger, hurting runtime.  
• **SAT performed worst**: in several instances the Boolean encoding alone exceeded the time limit, preventing the solver from even starting the search.
