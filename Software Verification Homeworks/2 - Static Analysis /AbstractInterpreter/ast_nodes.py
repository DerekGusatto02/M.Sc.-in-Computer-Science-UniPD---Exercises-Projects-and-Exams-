class Const:
    """Represents a constant integer value in the abstract syntax tree."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Const({self.value})"

class Var:
    """Represents a variable reference in the abstract syntax tree."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Var({self.name})"

class Add:
    """Represents addition of two arithmetic expressions: left + right."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Add({self.left}, {self.right})"

class Sub:
    """Represents subtraction of two arithmetic expressions: left - right."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Sub({self.left}, {self.right})"

class Mul:
    """Represents multiplication of two arithmetic expressions: left * right."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Mul({self.left}, {self.right})"

class Div:
    """Represents integer division of two arithmetic expressions: left / right.
    May raise runtime error if divisor is zero."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"Div({self.left}, {self.right})"

class Assign:
    """Represents variable assignment: var := expr."""
    def __init__(self, var, expr):
        self.var = var      # variable name (string)
        self.expr = expr    # right-hand side expression
    def __repr__(self):
        return f"Assign({self.var}, {self.expr})"

class While:
    """Represents a while loop: while (cond) { body }."""
    def __init__(self, cond, body):
        self.cond = cond    # loop condition (boolean expression)
        self.body = body    # loop body (statement)
    def __repr__(self):
        return f"While({self.cond}, {self.body})"

class Sequence:
    """Represents a sequence of statements: stmt1; stmt2; ...; stmtN."""
    def __init__(self, stmts):
        self.stmts = stmts  # list of statements
    def __repr__(self):
        return f"Seq({self.stmts})"

class IfThenElse:
    """Represents a conditional statement: if (cond) { then_branch } else { else_branch }.
    The else branch is optional and defaults to Skip if not provided."""
    def __init__(self, cond, then_branch, else_branch=None):
        self.cond = cond                # condition (boolean expression)
        self.then_branch = then_branch  # statement executed if condition is true
        self.else_branch = else_branch  # statement executed if condition is false (optional)
    def __repr__(self):
        return f"If({self.cond}, {self.then_branch}, {self.else_branch})"

class Skip:
    """Represents a no-operation statement that has no effect on the program state."""
    def __repr__(self):
        return "Skip"