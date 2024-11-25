import math
import numpy as np
from z3 import *
from itertools import combinations

def at_least_one_np(bool_vars):
    return Or(bool_vars)

def at_most_one_np(bool_vars):
    return And([Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)])

def exactly_one_np(bool_vars, name = ""):
    return And(at_least_one_np(bool_vars), at_most_one_np(bool_vars))

def flatten(matrix):
    return [e for row in matrix for e in row]

#Conversion function from Decimal to boolean array
def convert_dec_to_bool(dec_number, enc_bits=None):
  if enc_bits == None:
    n_bits = math.ceil(math.log(dec_number, 2))
  elif dec_number!=0 and enc_bits<math.ceil(math.log(dec_number, 2)):
    print("Impossible conversion, too few bits specified")
    return None
  else:
    n_bits = enc_bits

  bits = (1 << np.arange(n_bits))[::-1]
  return {"Num_bits":n_bits, "Conversion":(bits & dec_number) != 0}

#Conversion function from boolean list to integer
def convert_bool_to_dec(bool_list):
  num = 0
  n_bits=len(bool_list)
  for b in range(n_bits):
    if bool_list[b]==True:
      num+=2**(n_bits-b-1)
  return num    


#This function defines the constraint that ensures that res = u + v it works only if the two have the same length, res is assumed to have enough bits to express the sum of u and v 
def sum_2_bool_constraint(u, v, res, name):
  if len(u)!=len(v):
    print("Can only sum integers with the same length")
  bits = len(u)
  c = [Bool(f"carry_{i}_from_{name}") for i in range(bits)]
  const = And(*[And(
    Implies(And(u[i],v[i],c[i]), And(res[i], c[i-1])),
    Implies(Or(And(u[i],v[i], Not(c[i])), And(u[i], Not(v[i]), c[i]), And(Not(u[i]), v[i], c[i])), And(Not(res[i]), c[i-1])),
    Implies(Or(And(u[i],Not(v[i]), Not(c[i])), And(Not(u[i]), v[i], Not(c[i])), And(Not(u[i]), Not(v[i]), c[i])), And(res[i], Not(c[i-1]))),
    Implies(And(Not(u[i]),Not(v[i]),Not(c[i])), And(Not(res[i]), Not(c[i-1]))),
    Not(c[0])
  ) for i in range(bits)])
  return const



#This function defines the constraint that ensures that decisions[i] = sum{j in 1..n}(array[j] if conditions[j]=True)
def sum_cond_on_array_constraint(decision, array, conditions, name):
  if len(array)!=len(conditions):
    print("Number of numbers to sum does't match the number of conditions")
  bits=len(array[0])
  ps = [[Bool(f"bit_{j}_of_ps_{i}_from_{name}") for j in range(bits)]for i in range(len(array))]
  ps.append(decision)
  const = And(
      Not(Or(ps[0])),
    *[And(Implies(conditions[i], sum_2_bool_constraint(ps[i], array[i], ps[i+1], f"Partial_Sum_{i}_from_{name}")), 
          Implies(Not(conditions[i]), compare(ps[i], ps[i+1], '=='))) for i in range(len(array))])
  
  return const
  

def compare(num_1, num_2, operator='>'):

  
  n = len(num_1)
  if len(num_2)!=n:
    print("Can only compare integers with same bit size")
    return []

  if type(num_1[0])==bool:
    num_1_bool = [BoolVal(m) for m in num_1]
  else:
    num_1_bool = num_1

  if type(num_2[0])==bool:
    num_2_bool = [BoolVal(m) for m in num_2]
  else:
    num_2_bool = num_2
  
  if operator == '==':
    const = And(
      *[Or(And(num_1_bool[i], num_2_bool[i]), And(Not(num_1_bool[i]), Not(num_2_bool[i]))) for i in range(n)]
    )
    return const
    

  elif operator == '>':
    const = Or(
      *[And(*[Or(And(num_1_bool[j], num_2_bool[j]), And(Not(num_1_bool[j]), Not(num_2_bool[j]))) for j in range(i)], num_1_bool[i], Not(num_2_bool[i])) for i in range(n)]
    )
    return const
  elif operator == '>=':
    const = Or(
      And(*[Or(And(num_1_bool[i], num_2_bool[i]), And(Not(num_1_bool[i]), Not(num_2_bool[i]))) for i in range(n)]),
      Or(*[And(*[Or(And(num_1_bool[j], num_2_bool[j]), And(Not(num_1_bool[j]), Not(num_2_bool[j]))) for j in range(i)], num_1_bool[i], Not(num_2_bool[i])) for i in range(n)])
    )
    return const
  elif operator == '<':
    return compare(num_2_bool, num_1_bool, '>')
  elif operator == '<=':
    return compare(num_2_bool, num_1_bool, '>=')
  else:
    print("Unsupported Operator")
    return []

def consecutive(v, u):
    n = len(v)
    const = And(
      Not(u[0]),
      *[v[i] == u[i+1] for i in range(n-1)],
      Not(v[n-1])
    )

    return const

def decode_paths(result, n_couriers, n_items):
  paths=[]
  for i in range(n_couriers):
      start = -1
      courier_path = []
      while start!=n_items:
          if start==-1:
            start=n_items
          start_row = result[i][start]
          for k in range(len(start_row)):
            if result[i][start][k]==True:
              if k!=n_items:
                courier_path.append(k+1)
              start = k 
      paths.append(courier_path)
  return paths


