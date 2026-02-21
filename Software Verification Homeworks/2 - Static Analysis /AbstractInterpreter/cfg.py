from ast_nodes import Const, Var, Assign, While, Sequence, IfThenElse, Skip

class CFGNode:
    """Represents a single node in the Control Flow Graph.
    
    Attributes:
        id: Unique identifier for the node
        stmt: The AST statement associated with this node (if any)
        succ: List of successor nodes
        pred: List of predecessor nodes
    """
    def __init__(self, node_id, stmt=None):
        self.id = node_id               # Unique node identifier
        self.stmt = stmt                # Associated AST statement (or None for merge nodes)
        self.succ = []                  # List of successor nodes
        self.pred = []                  # List of predecessor nodes
    
    def __repr__(self):
        return f"Node({self.id}, {self.stmt})"

class CFG:
    """Represents a Control Flow Graph (CFG).
    
    Attributes:
        nodes: List of all CFG nodes
        entry: The entry node (program start)
        exit: The exit node (program end)
        node_counter: Counter for generating unique node IDs
    """
    def __init__(self):
        self.nodes = []                 # All nodes in the CFG
        self.entry = None               # Entry point of the program
        self.exit = None                # Exit point of the program
        self.node_counter = 0           # Counter for unique node IDs
    
    def new_node(self, stmt=None):
        """Creates a new CFG node with a unique ID.
        
        Args:
            stmt: The AST statement for this node (optional)
        
        Returns:
            CFGNode: The newly created node
        """
        node = CFGNode(self.node_counter, stmt)
        self.nodes.append(node)
        self.node_counter += 1
        return node
    
    def add_edge(self, from_node, to_node):
        """Adds a directed edge between two nodes.
        
        Args:
            from_node: The source node
            to_node: The destination node
        """
        if to_node not in from_node.succ:
            from_node.succ.append(to_node)
        if from_node not in to_node.pred:
            to_node.pred.append(from_node)

def build_cfg(program):
    """Builds the Control Flow Graph (CFG) from a While program.
    
    This is the main entry point for CFG construction. It creates a CFG
    object and delegates to build_cfg_stmt to recursively construct the graph.
    
    Args:
        program: An AST node representing the While program
    
    Returns:
        CFG: The constructed Control Flow Graph with entry and exit nodes set
    """
    cfg = CFG()
    
    # Recursively build the CFG from the program statement
    entry, exit_node = build_cfg_stmt(cfg, program)
    
    # Set the entry and exit points of the CFG
    cfg.entry = entry
    cfg.exit = exit_node
    
    return cfg


def build_cfg_stmt(cfg, stmt):
    """Recursively constructs the CFG for a single statement.
    
    Handles different statement types (Assign, Sequence, While, IfThenElse, Skip)
    and creates appropriate nodes and edges in the CFG.
    
    Args:
        cfg: The CFG object being constructed
        stmt: The AST statement to process
    
    Returns:
        tuple: (entry_node, exit_node) - the entry and exit nodes of this statement's CFG
    
    Raises:
        ValueError: If the statement type is not recognized
    """
    
    if isinstance(stmt, Skip) or stmt is None:
        # Skip statement: create a single node with no effect
        node = cfg.new_node(Skip())
        return node, node
    
    elif isinstance(stmt, Assign):
        # Assignment statement: create a single node
        # The transfer function will handle the actual state update
        node = cfg.new_node(stmt)
        return node, node
    
    elif isinstance(stmt, Sequence):
        # Sequence of statements: connect them in cascade
        # stmt1; stmt2; ... ; stmtN
        entry_node = None
        exit_node = None
        
        for s in stmt.stmts:
            # Recursively build CFG for each statement
            s_entry, s_exit = build_cfg_stmt(cfg, s)
            
            if entry_node is None:
                # First statement: its entry is the sequence's entry
                entry_node = s_entry
            else:
                # Connect the previous statement's exit to this statement's entry
                cfg.add_edge(exit_node, s_entry)
            
            # Update the exit node to the current statement's exit
            exit_node = s_exit
        
        return entry_node, exit_node
    
    elif isinstance(stmt, While):
        # While loop: cond -> body -> cond (back-edge)
        #             cond -> exit (when condition is false)
        
        # Create a node for the loop condition test
        cond_node = cfg.new_node(stmt.cond)
        
        # Recursively build the CFG for the loop body
        body_entry, body_exit = build_cfg_stmt(cfg, stmt.body)
        
        # Add edges:
        # From condition to body (when condition is true)
        cfg.add_edge(cond_node, body_entry)
        
        # Back-edge from body exit to condition (loop)
        cfg.add_edge(body_exit, cond_node)
        
        # Create exit node for when condition is false
        exit_node = cfg.new_node(None)
        cfg.add_edge(cond_node, exit_node)
        
        return cond_node, exit_node
    
    elif isinstance(stmt, IfThenElse):
        # If-then-else: cond -> then_branch \
        #                        -> merge_node
        #               cond -> else_branch /
        
        # Create a node for the condition test
        cond_node = cfg.new_node(stmt.cond)
        
        # Recursively build the CFG for the then branch
        then_entry, then_exit = build_cfg_stmt(cfg, stmt.then_branch)
        
        # Recursively build the CFG for the else branch
        # If no else branch is provided, use Skip
        if stmt.else_branch is not None:
            else_entry, else_exit = build_cfg_stmt(cfg, stmt.else_branch)
        else:
            else_entry, else_exit = build_cfg_stmt(cfg, Skip())
        
        # Add edges:
        # From condition to then branch (when condition is true)
        cfg.add_edge(cond_node, then_entry)
        
        # From condition to else branch (when condition is false)
        cfg.add_edge(cond_node, else_entry)
        
        # Both branches converge to a merge node
        merge_node = cfg.new_node(None)
        cfg.add_edge(then_exit, merge_node)
        cfg.add_edge(else_exit, merge_node)
        
        return cond_node, merge_node
    
    else:
        # Unknown statement type: raise an error
        raise ValueError(f"Unknown statement type: {type(stmt)}")


def print_cfg(cfg):
    """Pretty-prints the Control Flow Graph in a human-readable format.
    
    Displays:
    - Entry and exit nodes
    - All nodes in the CFG
    - Successor relationships for each node
    
    Args:
        cfg: The CFG to print
    """
    print("\n=== Control Flow Graph (CFG) ===")
    print(f"Entry node: {cfg.entry}")
    print(f"Exit node: {cfg.exit}")
    print("\nNodes and edges:")
    for node in cfg.nodes:
        print(f"  {node}")
        for succ in node.succ:
            print(f"    -> {succ}")