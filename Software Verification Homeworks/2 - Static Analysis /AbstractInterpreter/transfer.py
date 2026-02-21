from interval import Interval
from ast_nodes import Const, Var, Add, Sub, Mul, Div, Assign, While, IfThenElse, Skip

def eval_aexp(expr, state):
    """
    Evaluates an arithmetic expression in the abstract state.
    
    This function recursively evaluates arithmetic expressions by applying
    abstract domain operations (addition, subtraction, multiplication, division)
    on intervals.
    
    Args:
        expr: An AST node representing an arithmetic expression
        state: The current abstract state (AbstractState)
    
    Returns:
        Interval: The abstract value of the expression
    """
    if isinstance(expr, Const):
        # Constant: return a singleton interval [value, value]
        return Interval(expr.value, expr.value)

    if isinstance(expr, Var):
        # Variable: look up its abstract value in the state environment
        # If variable not found, return bottom (unreachable state)
        return state.env.get(expr.name, Interval.bottom())

    if isinstance(expr, Add):
        # Addition: recursively evaluate both operands and add their intervals
        left = eval_aexp(expr.left, state)
        right = eval_aexp(expr.right, state)
        return left.add(right)
    
    if isinstance(expr, Sub):
        # Subtraction: recursively evaluate both operands and subtract their intervals
        left = eval_aexp(expr.left, state)
        right = eval_aexp(expr.right, state)
        return left.sub(right)
    
    if isinstance(expr, Mul):
        # Multiplication: recursively evaluate both operands and multiply their intervals
        left = eval_aexp(expr.left, state)
        right = eval_aexp(expr.right, state)
        return left.mul(right)
    
    if isinstance(expr, Div):
        # Division: recursively evaluate both operands and divide their intervals
        # Note: if 0 is in the divisor interval, the result is bottom (runtime error)
        left = eval_aexp(expr.left, state)
        right = eval_aexp(expr.right, state)
        return left.div(right)
    
    # Unknown expression type: return bottom
    return Interval.bottom()


def eval_bexp(expr, state):
    """
    Evaluates a boolean expression in the abstract state.
    
    This function currently provides a simple conservative approximation:
    any expression can be either true or false, so the state is returned unchanged.
    A more precise implementation would split intervals based on comparison operators.
    
    Args:
        expr: An AST node representing a boolean expression
        state: The current abstract state (AbstractState)
    
    Returns:
        AbstractState: The abstract state restricted to the true branch
    """
    # Conservative approximation: any expression can be true or false
    # A more sophisticated version could split intervals for comparisons like x < 5
    return state


def transfer(node, state):
    """
    Generic transfer function for a CFG node.
    
    This function applies the semantic effect of a statement (if present) to the
    abstract state. The transfer function is the core of abstract interpretation,
    computing how each program statement affects the abstract state.
    
    Args:
        node: A CFG node (CFGNode)
        state: The input abstract state (AbstractState)
    
    Returns:
        AbstractState: The output abstract state after applying the node's statement
    """
    if node.stmt is None:
        # Merge nodes or exit nodes: pass the state unchanged
        return state
    
    if isinstance(node.stmt, Skip):
        # Skip statement: no effect on the state
        return state
    
    if isinstance(node.stmt, Assign):
        # Assignment statement: apply the assignment transfer function
        return transfer_assign(node.stmt, state)
    
    # For While and IfThenElse, the node contains the condition expression
    # but conditions do not directly modify the state
    if isinstance(node.stmt, (Const, Var, Add, Sub, Mul, Div)):
        # Condition expressions: no effect on the state
        return state
    
    # Default: return the state unchanged (conservative)
    return state


def transfer_assign(stmt, state):
    """
    Transfer function for assignment statements: x := expr
    
    This function evaluates the right-hand side expression and updates
    the variable in the state with the abstract value.
    
    Args:
        stmt: An Assign AST node
        state: The input abstract state (AbstractState)
    
    Returns:
        AbstractState: A new state with the variable updated
    """
    if not isinstance(stmt, Assign):
        return state
    
    # Evaluate the expression on the right-hand side
    value = eval_aexp(stmt.expr, state)
    
    # Assign the result to the variable and return the new state
    return state.assign(stmt.var, value)