from self_healing.self_healer import RichFunction, Mutator, single_heal, hospitalization
from self_healing.std_mutant_operator import *
import inspect

# What follows is an incorrect implementation of a selection sort.
# Two bugs 
def sort(ls: list) -> list:
    for i in range(len(ls)):
        minimum, minimum_idx = ls[i], i

        for idx in range(i+1, len(ls)*0):
        # for idx in range(i+1, len(ls)): # correct version
            if ls[idx] >= minimum:
            # if ls[idx] <= minimum: # correct version
                minimum, minimum_idx = ls[idx], idx

        temp = ls[i]
        ls[i] = ls[minimum_idx]
        ls[minimum_idx] = temp

    return ls

# In order to test our sorting function, we implement a property that every
# output of `sort` must respect. In this case, the property checks whether
# the output list of `sort` is actually sorted.
def is_sorted(ls):
    if len(ls) <= 1:
        return True
    
    if ls[0] <= ls[1]:
        return is_sorted(ls[1:])

    return False


# Through the principles of Property-Based Testing (PBT), we generate a 
# number of random inputs for our `sort` function.
# The following is of course only a sketch of what a true PBT library
# (e.g. Hypothesis) can perform.
def pbt(sort_func, iters=100):
    import random
    result, num_passed = True, 0
    
    for _ in range(iters):
        length = random.randint(0, 20)
        lista  = [random.randint(-999999,999999) for _ in range(length)]

        try:
            if not is_sorted(sort_func(lista)):
                result = False
            else:
                num_passed += 1
        except Exception:
            result = False
            num_passed -= 1
            
    return (result, num_passed/iters)

# We then wrap our original `sort` in a class containing some meta
# information about `sort`, such as its source code (represented as
# a string), its name and its fitness score (more on that later)
rich_sort_function = RichFunction(sort, "sort", inspect.getsource(sort), None, 0)

# How will we mutate our (enriched) `sort` function? We need to describe
# a number of mutant operators, which encode what and how we are going to
# mutate. The following are built-ins, but more operators can be expressed
# using the (admittedly not user-frendly) AST API.
m1 = Mutator(check_Binop_math, trans_Binop_math)
m2 = Mutator(check_Binop_left_right, trans_Binop_left_right)
m3 = Mutator(check_true_false, trans_true_false)
m4 = Mutator(check_0_1, trans_0_1)
m5 = Mutator(check_negate_if, trans_negate_if)
m6 = Mutator(check_comparisons, trans_comparisons)

default_mutators = [m1,m2,m3,m4,m5,m6]


# We are ready to mutate our function. Let's first try if a single round of
# mutation is enough to correct (or "heal") our function:
single_heal(rich_sort_function, default_mutators, pbt, debug=False)

# The ouput will be similar to the following:
#
# Working on sort_0
# Working on sort_1
# Working on sort_2
# Working on sort_3
# Working on sort_4
# Working on sort_5
# Working on sort_6
# Working on sort_7
# Working on sort_8
# Working on sort_9
# Working on sort_10
# Working on sort_11
# Working on sort_12
# Working on sort_13
# Working on sort_14
# Working on sort_15
# Working on sort_16
# Working on sort_17
# Working on sort_18
# Working on sort_19
# Working on sort_20
# Working on sort_21
# Working on sort_22
# (False,
#  {<function sort_0 at 0x7f30fef6e550>: sort_0 - 0.103, <function sort_1 at 0x7f30fefa2040>: sort_1 - 0.144, <function sort_2 at 0x7f30fefebdc0>: sort_2 - 0.119, ... <function sort_21 at 0x7f30ff092160>: sort_21 - 0.133, <function sort_22 at 0x7f30ff0921f0>: sort_22 - 0.149})

# Basically: 23 new functions are generated, and each of them is tested
# through our PBT function above. However, no function reaches a score of
# 1.0, aka. no function passes all the tests (actually, they all behave
# quite poorly)

# We need the big guns! Let's try and see if _multiple_ rounds of
# "healing" will move us closer to the solution! (*)

results = hospitalization(rich_sort_function, default_mutators, pbt, max_iters=1)

# A long stdout will follow. The results will be three enriched function,
# such as [sort_42_112 - 1.0, sort_39_267 - 1.0, sort_44_289 - 1.0] (the names
# could be different), each of them containing a function that has passed
# all the tests. For example:

assert results[0].func([5,3,1,2]) == [1,2,3,5]
