from transfer import transfer
from state import AbstractState

def solve(cfg, initial_state, widening_enabled=False):
    """
    Fixed-point solver for abstract interpretation analysis.
    
    This function computes the solution to the system of abstract equations
    defined on the Control Flow Graph (CFG) using a worklist algorithm.
    It iteratively applies transfer functions until a fixed point is reached.
    
    Args:
        cfg: Control Flow Graph (CFG) object
        initial_state: AbstractState representing the initial program state at the entry point
        widening_enabled: Boolean flag to enable widening operator (optional, default: False)
    
    Returns:
        dict: A mapping from each CFG node to its computed abstract state
    """
    # Initialize abstract states: entry node gets initial_state, others get bottom
    var_names = list(initial_state.env.keys())
    states = {}
    
    for node in cfg.nodes:
        if node == cfg.entry:
            # Entry node starts with the provided initial state
            states[node] = initial_state
        else:
            # All other nodes start with bottom (unreachable state)
            states[node] = AbstractState.bottom(var_names)
    
    # Initialize worklist with the entry node
    worklist = [cfg.entry]
    iteration = 0
    MAX_ITERATIONS = 1000  # Safety limit to prevent infinite loops
    
    # Worklist algorithm: iteratively process nodes until convergence
    while worklist and iteration < MAX_ITERATIONS:
        # Pop node from worklist (FIFO order for breadth-first traversal)
        node = worklist.pop(0)
        iteration += 1
        
        # Compute new state from all predecessor nodes
        pred_states = []
        for pred in node.pred:
            # Get the state at the predecessor
            pred_state = states[pred]
            # Apply the transfer function of the predecessor's statement
            transferred = transfer(pred, pred_state)
            pred_states.append(transferred)
        
        # Join (least upper bound) all predecessor states
        if pred_states:
            # Initialize with the first predecessor's state
            new_state = pred_states[0]
            # Join with all remaining predecessor states
            for ps in pred_states[1:]:
                new_state = new_state.join(ps)
        else:
            # No predecessors: keep the current state (happens at entry)
            new_state = states[node]
        
        # Apply widening operator if enabled and iteration threshold is reached
        # Widening ensures termination for infinite ascending chains
        if widening_enabled and iteration > 10:
            new_state = apply_widening(states[node], new_state)
        
        # Check if the new state is strictly greater than the old state
        if not new_state.leq(states[node]):
            # State changed: update and propagate to successors
            states[node] = new_state
            # Add all successor nodes to the worklist if not already present
            for succ in node.succ:
                if succ not in worklist:
                    worklist.append(succ)
    
    # Warn if iteration limit was reached (analysis may be incomplete)
    if iteration >= MAX_ITERATIONS:
        print(f"⚠️ Warning: reached iteration limit ({MAX_ITERATIONS})")
    
    return states


def apply_widening(old_state, new_state, thresholds=None):
    """
    Applies the widening operator to abstract intervals.
    
    Widening is used to accelerate convergence in the presence of infinite
    ascending chains. The strategy is:
    - If the lower bound decreases, widen to -∞
    - If the upper bound increases, widen to +∞
    
    Args:
        old_state: The previous abstract state (AbstractState)
        new_state: The newly computed abstract state (AbstractState)
        thresholds: Optional list of threshold values for threshold-based widening
                   (not currently implemented, reserved for future use)
    
    Returns:
        AbstractState: The widened abstract state
    """
    from interval import Interval
    
    # Build the widened environment variable by variable
    widened_env = {}
    
    for var in old_state.env:
        # Get intervals for this variable from both states
        old_iv = old_state.env[var]
        new_iv = new_state.env[var]
        
        # If old state is bottom, cannot widen
        if old_iv.is_bottom:
            widened_env[var] = new_iv
        else:
            # --- Widen the lower bound ---
            if new_iv.lower is not None and old_iv.lower is not None:
                if new_iv.lower < old_iv.lower:
                    # Lower bound decreased: widen to -∞
                    lower = None
                else:
                    # Lower bound stable or increased: keep new value
                    lower = new_iv.lower
            else:
                # At least one bound is already infinite
                lower = new_iv.lower
            
            # --- Widen the upper bound ---
            if new_iv.upper is not None and old_iv.upper is not None:
                if new_iv.upper > old_iv.upper:
                    # Upper bound increased: widen to +∞
                    upper = None
                else:
                    # Upper bound stable or decreased: keep new value
                    upper = new_iv.upper
            else:
                # At least one bound is already infinite
                upper = new_iv.upper
            
            # Create the widened interval for this variable
            widened_env[var] = Interval(lower, upper)
    
    # Return the new state with widened intervals
    return AbstractState(widened_env)