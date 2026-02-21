from interval import Interval

class AbstractState:
    """Represents an abstract program state as a non-relational domain.
    
    An abstract state is a mapping from variable names to abstract values (intervals).
    This implements a variable-wise (non-relational) abstract domain where variables
    are analyzed independently of each other.
    
    Attributes:
        env: Dictionary mapping variable names (strings) to Interval objects
    """
    
    def __init__(self, mapping):
        """Initializes an abstract state with the given variable-to-interval mapping.
        
        Args:
            mapping: A dictionary where keys are variable names (strings) and
                    values are Interval objects representing the abstract value
        """
        self.env = mapping  # Dictionary: variable name -> Interval

    @staticmethod
    def bottom(vars):
        """Creates a bottom (unreachable) abstract state for a set of variables.
        
        The bottom state represents an unreachable program point where no concrete
        value can exist. All variables are mapped to bottom intervals.
        
        Args:
            vars: An iterable of variable names (strings)
        
        Returns:
            AbstractState: A new state where all variables are mapped to bottom
        """
        return AbstractState({v: Interval.bottom() for v in vars})
    
    def join(self, other):
        """Computes the least upper bound (join) of two abstract states.
        
        The join operation combines two abstract states by taking the join of
        intervals for each variable. This is the abstract equivalent of the union
        operation and is used for merging states from different paths.
        
        Args:
            other: Another AbstractState object
        
        Returns:
            AbstractState: A new state representing the join of both states
        """
        new_env = {}
        for v in self.env:
            # Join the intervals for each variable
            new_env[v] = self.env[v].join(other.env[v])
        return AbstractState(new_env)
    
    def leq(self, other):
        """Checks the partial order relation (subset ordering) between two states.
        
        State s1 is less-than-or-equal-to (leq) state s2 if for all variables,
        the interval in s1 is a subset of the interval in s2. This is used to
        check convergence in the fixed-point iteration.
        
        Args:
            other: Another AbstractState object
        
        Returns:
            bool: True if this state is less-than-or-equal-to other, False otherwise
        """
        return all(self.env[v].leq(other.env[v]) for v in self.env)
    
    def assign(self, var, value_interval):
        """Updates a variable with a new abstract value.
        
        This function implements the assignment statement x := expr by updating
        the variable x with the abstract value (interval) of the expression.
        Returns a new state with the variable updated.
        
        Args:
            var: The variable name (string) to assign to
            value_interval: An Interval object representing the new abstract value
        
        Returns:
            AbstractState: A new state with the variable updated
        """
        # Create a copy of the environment to avoid modifying the original state
        new_env = self.env.copy()
        # Update the variable with the new interval
        new_env[var] = value_interval
        return AbstractState(new_env)
    
    def __repr__(self):
        """Returns a string representation of the abstract state.
        
        Returns:
            str: A string representation of the environment dictionary
        """
        return str(self.env)