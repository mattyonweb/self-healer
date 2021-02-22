import ast
import astpretty
import inspect
import astor
from dataclasses import dataclass
from typing import *

def pprint(s):
    tree = ast.parse(s)
    astpretty.pprint(ast.parse(tree), show_offsets=False)


# =========================================================== #
# =========================================================== #

Coord = List[int]

class Mutator():
    """ This class basically implements a mutant operator. It is parametrized
by two important Callables:

- A `check` function, which checks whether a given AST is a suitable
for mutation
- A `trans` function, which describes how to transform the AST 
described by `check` into new ASTs (which we will call "mutant")

This class also implements all the methods needed to perform this mutations.
"""
    def __init__(self,
                 check: Callable[[ast.AST], bool],
                 trans: Callable[[ast.AST], List[ast.AST]]):
        self.check = check
        self.trans = trans
        self.found: List[Coord] = list() # Ricorda di svuotarla!
        
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
        
        if isinstance(value, list):

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

            self.found = list() #fundamental!
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
    """ This class is a utility class to give a new name to
the function we are mutating. """
    counter = -1
    living_foos = list()

    def __init__(self, original_name: str):
        ChangeFooName.counter += 1
        self.original_name = original_name
        ChangeFooName.living_foos.append(self.current_name())
        super().__init__()

    def current_name(self):
        return self.original_name + "_" + str(ChangeFooName.counter)
        
    def visit_FunctionDef(self, node):
        if node.name == self.original_name:
            node.name = self.current_name()
        return node

    def visit_Name(self, node):
        if node.id == self.original_name:
            node.id = self.current_name()
        return node

#############################################################

class SelfHealer():
    """ TODO: questa classe serve davvero? Sostanzialmente:
1. Prende una lista di Mutators
2. Per ognuno di essi crea i nuovi AST
3. Cambia i nomi delle funzioni generate
""" 
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
# Default mutators. Useful, but maybe TODO move it to UTILS

m1 = Mutator(check_Binop_math, trans_Binop_math)
m2 = Mutator(check_Binop_left_right, trans_Binop_left_right)
m3 = Mutator(check_true_false, trans_true_false)
m4 = Mutator(check_0_1, trans_0_1)
m5 = Mutator(check_negate_if, trans_negate_if)
m6 = Mutator(check_comparisons, trans_comparisons)

default_mutators = [m1,m2,m3,m4,m5,m6]

# =========================================================== #
# =========================================================== #

@dataclass
class RichFunction:
    """ An enriched function wraps useful meta-data around
an otherwise normal Callable. """
    func: Callable # The actual function
    name: str      # Function name
    src_code: str  # Function src_code 
    ast: ast.AST   # Function AST (not used)
    score: float   # Function PBT score 

    def __repr__(self):
        return f"{self.name} - {self.score}"


# =========================================================== #


def single_heal(foo: RichFunction, mutators: List[Mutator],
                pbt: Callable, debug=False):
    """ This function performs a round of mutation on a function foo. """
    
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
        stats[func] = RichFunction(func=func,
                                   name=new_fname,
                                   src_code=new_src_code,
                                   ast=None,
                                   score=score)

    return (found_correct, stats)
        

def hospitalization(
        foo: RichFunction, mutators: List[Mutator],
        pbt: Callable, max_iters=2):
    
    """ Multiple rounds of healing. """
    
    found_correct, today_stats = single_heal(foo, mutators, pbt)

    sorted_foos = sorted(today_stats.values(),
                         key=lambda nt: nt.score, reverse=True)
    sorted_foos = sorted_foos[:1 + len(sorted_foos) // 2]

    if found_correct:
        return [sorted_foos[0]]
    if max_iters <= 0:
        return [sorted_foos[0]]
    
    # TODO: remove unused sort_23_253_554 functions and the likes!

    results = list()
    for chosen_foo in sorted_foos:
        rec_out = hospitalization(chosen_foo, mutators, pbt, max_iters=max_iters-1)
        results.append(rec_out)

    flatten_results = [r for r_ in results for r in r_]
    perfect_scores  = [r for r in flatten_results if r.score > 0.99]
    if perfect_scores:
        return perfect_scores
    return sorted(flatten_results, key=lambda x: x[0].score)
