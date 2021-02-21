import ast
from typing import *
from copy import deepcopy

# Example:
# 1+x ==> [1-x, 1*x, 1/x]

def check_Binop_math(node: ast.AST) -> bool:
    if isinstance(node, ast.BinOp):
        return True
    return False

def trans_Binop_math(node: ast.AST) -> List[ast.AST]:
    out = list()
    
    ops = set([ast.Add(), ast.Sub(), ast.Mult(), ast.Div()])
    original_op = node.op

    for new_op in ops - set([original_op]):
        new_node = deepcopy(node)
        new_node.op = new_op
        out.append(new_node)

    return out

# =========================================================== #
# Example:
# 1+x ==> [1, x]

def check_Binop_left_right(node: ast.AST) -> bool:
    if isinstance(node, ast.BinOp):
        return True
    return False

def trans_Binop_left_right(node: ast.AST) -> List[ast.AST]:
    return [node.left, node.right]


# =========================================================== #
def check_true_false(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return node.value in [True, False]
    return False

def trans_true_false(node):
    if node.value:
        return [ast.Constant(value=False, kind=None)]
    return [ast.Constant(value=True, kind=None)]


# =========================================================== #
def check_0_1(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return node.value in [0,1]
    return False

def trans_0_1(node):
    if node.value == 1:
        return [ast.Constant(value=0, kind=None)]
    else:
        return [ast.Constant(value=1, kind=None)]

# =========================================================== #
def check_negate_if(node: ast.AST) -> bool:
    return isinstance(node, ast.If)

def trans_negate_if(node):
    new_node = deepcopy(node)
    new_node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
    return [new_node]

# =========================================================== #
def pprint_ast(node: ast.AST):
    import astpretty
    astpretty.pprint(node, show_offsets=False)
    
def check_comparisons(node: ast.AST) -> bool:
    return isinstance(node, ast.Compare)

def trans_comparisons(node):
    out = list()
    ops = set([ast.Lt(), ast.LtE(), ast.Gt(), ast.GtE(), ast.Eq(), ast.NotEq()])

    try:
        field = "ops" if "ops" in node.__dict__ else "operand"
        # for new_op in ops - set([node.ops[0]]): #bug
        print("FIELD", field)
        print("NODE.DICT", node.__dict__)
        print("NODE.DICT.FIELD", node.__dict__[field])

        if field == "ops":
            ignore_ops = set(node.__dict__[field]) #d[field] è lista
        else:
            ignore_ops = set([node.__dict__[field]]) #d[field] è singleton
            
        for new_op in ops - ignore_ops: #bug
        # for new_op in ops - set([node.__dict__[field][0]]): #bug
            new_node = deepcopy(node)
            new_node.ops = [new_op]
            out.append(new_node)

        return out
    
    except Exception as e:
        print(f"WARNIN: {e}")
        pprint_ast(node)
        raise e
        return [node]

