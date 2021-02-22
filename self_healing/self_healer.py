import ast
import astpretty
from typing import *
import sys

# from hypothesis import given
# import hypothesis.strategies as st

def pprint(s):
    tree = ast.parse(s)
    astpretty.pprint(ast.parse(tree), show_offsets=False)


# =========================================================== #
# =========================================================== #

Coord = List[int]

class Mutator():
    def __init__(self,
                 check: Callable[[ast.AST], bool],
                 trans: Callable[[ast.AST], List[ast.AST]]):
        self.check = check
        self.trans = trans
        self.found: List[Coord] = list()
        
    def find_locations(self, node: ast.AST, current_loc: Coord) -> None:
        """ Recursive search of locations, according to the 
        self.check function. It doesn't return anything: it updates
        self.found. """

        if self.check(node):
            self.found.append(current_loc)
                
        for idx, (field, value) in enumerate(ast.iter_fields(node)):
            if isinstance(value, list):
                for idx2, item in enumerate(value):
                    if isinstance(item, ast.AST):     
                        self.find_locations(item, current_loc + [idx, idx2])

            elif isinstance(value, ast.AST):
                self.find_locations(value, current_loc + [idx])

                
    def retrieve_single_location(self, node: ast.AST, loc: Coord) -> ast.AST:
        """ Return node at a given location, identified by a coordinate. """
        if loc == []:
            return node
        
        field, value = list(ast.iter_fields(node))[loc[0]]

        print(value)
        
        if isinstance(value, list):
            print("VALUE", value)
            print("LOC", loc)

            item = value[loc[1]]
            if isinstance(item, ast.AST):
                return self.retrieve_single_location(item, loc[2:])
                
        elif isinstance(value, ast.AST):
            return self.retrieve_single_location(value, loc[1:])

        

    def retrieve_all_locations(self, node: ast.AST, locs: List[Coord]) -> Dict[Coord, ast.AST]:       
        return {tuple(loc) : self.retrieve_single_location(node, loc) for loc in locs}


    def apply_mutations(self, tree: ast.AST) -> Dict[Coord, List[ast.AST]]:
        self.find_locations(tree, [])

        try:
            new_nodes = dict()
            for k, v in self.retrieve_all_locations(tree, self.found).items():
                new_nodes[k] = self.trans(v)

            self.found = list()
            return new_nodes

        except Exception as e:
            print("errore grave")
            print(pprint(tree))
            print(astor.to_source(tree))
            raise e
            

    def replace_at(self, node, new_node, index):
        """ Che cazz serve sta funzione? """
        for idx, (field, old_value) in enumerate(list(ast.iter_fields(node))):
            if isinstance(old_value, list):
                new_values = []
                
                for idx2, value in enumerate(old_value):
                    if isinstance(value, ast.AST):

                        if index[0] == idx and index[1] == idx2:
                            if len(index[2:]) == 0:
                                value = new_node
                            else:
                                value = self.replace_at(value, new_node, index[2:])
                        else:
                            value = value
                                                        
                        if value is None:
                            continue
                        elif not isinstance(value, ast.AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)

                old_value[:] = new_values
                
            elif isinstance(old_value, ast.AST):
                if index[0] == idx:
                    if len(index[1:]) == 0:
                        new_value = new_node
                    else:
                        new_value = self.replace_at(old_value, new_node, index[1:])
                else:
                    new_value = old_value

                if new_value is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_value)
        return node
                
    def return_new_asts(self, tree: ast.AST):
        from copy import deepcopy
        
        new_asts = list()
        
        for loc, new_nodes in self.apply_mutations(tree).items():
            for new_node in new_nodes:
                new_asts.append(
                    self.replace_at(deepcopy(tree),
                                    new_node,
                                    loc)
                )

        return new_asts

# =========================================================== #
# =========================================================== #
# =========================================================== #

from self_healing.std_mutant_operator import *


class ChangeFooName(ast.NodeTransformer):
    counter = -1

    def __init__(self, original_name: str):
        self.original_name = original_name
        ChangeFooName.counter += 1
        super().__init__()
        
    def visit_FunctionDef(self, node):
        if node.name == self.original_name:
            node.name = self.original_name + "_" + str(ChangeFooName.counter)
        return node

    def visit_Name(self, node):
        if node.id == self.original_name:
            node.id = self.original_name + "_" + str(ChangeFooName.counter)
        return node

    def current_name(self):
        return self.original_name + "_" + str(ChangeFooName.counter)

    
class SelfHealer(object):
    def __init__(self, mutators, original_name_foo=None):
        self.mutators = mutators
        self.foo_name = original_name_foo

    def gather_all_mutants(self, tree) -> List[Tuple[str, ast.AST]]:
        mutants = list()
        
        for mutator in self.mutators:
            for mutant in mutator.return_new_asts(tree):
                if not self.foo_name:
                    mutants.append(mutant)
                else:
                    cfn = ChangeFooName(self.foo_name)
                    mutant = cfn.visit(mutant)
                    mutants.append((cfn.current_name(), mutant))
                    
        return mutants

    def pprint_all_mutants(self, tree):
        mutants = self.gather_all_mutants(tree)
        for (_, m) in mutants:
            print(astor.to_source(m))
        return mutants

# =========================================================== #

import inspect
import astor
import astunparse

m1 = Mutator(check_Binop_math, trans_Binop_math)
m2 = Mutator(check_Binop_left_right, trans_Binop_left_right)
m3 = Mutator(check_true_false, trans_true_false)
m4 = Mutator(check_0_1, trans_0_1)
m5 = Mutator(check_negate_if, trans_negate_if)
m6 = Mutator(check_comparisons, trans_comparisons)



# =========================================================== #
# =========================================================== #


# Esempio di funzione da mutare
def sort(ls: list) -> list:
    for i in range(len(ls)):
        minimum, minimum_idx = ls[i], i

        for idx in range(i+1, len(ls)*0):
        # for idx in range(i+1, len(ls)): #corretto
            if ls[idx] >= minimum:
            # if ls[idx] <= minimum: #corretto
                minimum, minimum_idx = ls[idx], idx

        temp = ls[i]
        ls[i] = ls[minimum_idx]
        ls[minimum_idx] = temp

    return ls

# Proprietà da testare via PBT
def is_sorted(ls):
    if len(ls) <= 1:
        return True
    
    if ls[0] <= ls[1]:
        return is_sorted(ls[1:])

    return False


# PBT framework costruito a caso
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
        except Exception as e:
            result = False
            num_passed -= 1
            
    return (result, num_passed/iters)


from dataclasses import dataclass

@dataclass
class Func:
    func: Callable
    name: str
    src_code: str
    ast: ast.AST
    score: float

    def __repr__(self):
        return f"{self.name} - {self.score}"


micio = Func(sort, "sort", inspect.getsource(sort), None, 0)

def heal(foo, debug=False):
    src_code = foo.src_code

    tree     = ast.parse(src_code)
    sh       = SelfHealer([m1,m2,m3,m4,m5,m6],
                          original_name_foo=foo.name)

    new_srcs = list()
    for (new_name, m) in sh.gather_all_mutants(tree):
        new_srcs.append((new_name, astor.to_source(m)))
    
    stats = dict()
    found_correct = False
    
    for new_fname, new_src_code in new_srcs:
        if debug:
            print(new_src_code)
            
        exec(new_src_code, globals())
        exec(f"func = {new_fname}", globals())
         
        try:
            seems_correct, score = pbt(func, 1000)
            
        except NameError as e:
            print(f"WARNING: {new_fname} o func non sono state trovate!")
            print(e)
            continue
        except Exception as e:
            if debug:
                print(f"WARNING: {new_fname} ha ritornato l'eccezione!")
                print(e)    
            continue
            
        if seems_correct:
            print(new_fname)
            print(new_src_code)
            print(f"{new_fname} SUCCESSFUL - SCORE IS {score}")
            found_correct = True
            
        else:
            if debug:
                print(f"{new_fname} FAIL - SCORE IS {score}")

        print(f"Working on {new_fname}")
        stats[func] = Func(func=func,
                           name=new_fname,
                           src_code=new_src_code,
                           ast=None,
                           score=score)

    return (found_correct, stats)
        

def hospitalization(foo, max_iters=2):
    # print(foo)
    # print(foo.func)
    # print([g for g in globals() if g.startswith("sort")])
    
    found_correct, today_stats = heal(foo)

    sorted_foos = sorted(today_stats.values(),
                         key=lambda nt: nt.score, reverse=True)
    sorted_foos = sorted_foos[:1 + len(sorted_foos) // 2]

    if found_correct:
        return [sorted_foos[0]]
    if max_iters == 0:
        return [sorted_foos[0]]
    
    # Qua potresi eliminare da glovals() le foos che non usi più...

    results = list()
    for chosen_foo in sorted_foos:
        rec_out = hospitalization(chosen_foo, max_iters=max_iters-1)
        results.append(rec_out)
    return results
    
# heal(sort, "sort")

# from hypothesis import given
# import hypothesis.strategies as st

# @given(l=st.lists(st.integers()))
# def test_decode_inverts_encode(foo, l):
#     assert is_sorted(foo(l))
