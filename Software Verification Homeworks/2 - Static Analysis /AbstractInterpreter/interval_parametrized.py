"""
Parametrized Interval Domain Int_{m,n}

Represents intervals constrained to a range [m, n].
Extends the base Interval class with parametric bounds.
"""

from interval import Interval

class ParametrizedInterval(Interval):
    """
    Extends Interval with parametric constraints [m, n].
    
    The domain is defined as:
      Int_{m,n} = {∅, Z} ∪ {[k,k] | k ∈ Z} ∪
                  {[a,b] | a < b, [a,b] ⊆ [m,n]} ∪
                  {(-∞, k] | k ∈ [m,n]} ∪
                  {[k, +∞) | k ∈ [m,n]}
    
    Attributes:
        lower: Lower bound of interval (inherited from Interval)
        upper: Upper bound of interval (inherited from Interval)
        is_bottom: Boolean flag for bottom element (inherited)
        m: Lower constraint (default: -∞)
        n: Upper constraint (default: +∞)
    """
    
    def __init__(self, lower=None, upper=None, is_bottom=False, m=None, n=None):
        """
        Initialize a parametrized interval with constraints [m, n].
        
        Args:
            lower: Lower bound (integer or None for -∞), default None
            upper: Upper bound (integer or None for +∞), default None
            is_bottom: Boolean flag for bottom element, default False
            m: Lower constraint (integer or None for -∞), default None
            n: Upper constraint (integer or None for +∞), default None
        
        Raises:
            AssertionError: If interval [lower, upper] is not in [m, n] 
                           (unless in constant propagation domain m > n)
        """
        # Call parent constructor with interval bounds
        super().__init__(lower, upper, is_bottom)
        
        # Set constraint bounds (default to -∞ and +∞)
        self.m = m if m is not None else float('-inf')
        self.n = n if n is not None else float('+inf')
        
        # Validate interval is within [m, n] bounds
        # EXCEPTION: In constant propagation domain (m > n), skip validation
        is_const_prop = self._to_num(self.m) > self._to_num(self.n)
        
        if not is_bottom and not is_const_prop and lower is not None and upper is not None:
            assert self._to_num(lower) >= self._to_num(self.m), \
                f"Interval lower bound {lower} < constraint {self.m}"
            assert self._to_num(upper) <= self._to_num(self.n), \
                f"Interval upper bound {upper} > constraint {self.n}"
    
    @staticmethod
    def _to_num(x):
        """Convert value to number for comparison (handle infinities)."""
        if x is None:
            return float('inf')
        return x
    
    @staticmethod
    def bottom(m=None, n=None):
        """
        Create the bottom element (empty set ∅) of Int_{m,n}.
        
        Args:
            m: Lower constraint, default None (-∞)
            n: Upper constraint, default None (+∞)
        
        Returns:
            ParametrizedInterval: The bottom element
        """
        return ParametrizedInterval(is_bottom=True, m=m, n=n)
    
    @staticmethod
    def top(m=None, n=None):
        """
        Create the top element (all values Z) of Int_{m,n}.
        
        Args:
            m: Lower constraint, default None (-∞)
            n: Upper constraint, default None (+∞)
        
        Returns:
            ParametrizedInterval: The top element [-∞, +∞]
        """
        return ParametrizedInterval(None, None, m=m, n=n)
    
    def is_constant_propagation_domain(self):
        """
        Check if this is a constant propagation domain (m > n).
        
        In constant propagation, only singleton intervals [k,k] are allowed.
        
        Returns:
            bool: True if m > n, False otherwise
        """
        return self._to_num(self.m) > self._to_num(self.n)
    
    def is_singleton(self):
        """
        Check if this interval is a singleton [k,k].
        
        Returns:
            bool: True if lower == upper and both are finite
        """
        if self.is_bottom:
            return False
        return self.lower is not None and self.lower == self.upper
    
    def __repr__(self):
        """Return string representation with constraints."""
        if self.is_bottom:
            m_str = "-∞" if self.m == float('-inf') else str(int(self.m))
            n_str = "+∞" if self.n == float('+inf') else str(int(self.n))
            return f"⊥_{{{m_str},{n_str}}}"
        
        # Format bounds
        l = "-∞" if self.lower is None else str(self.lower)
        u = "+∞" if self.upper is None else str(self.upper)
        
        # Format constraints
        m_str = "-∞" if self.m == float('-inf') else str(int(self.m))
        n_str = "+∞" if self.n == float('+inf') else str(int(self.n))
        
        return f"[{l}, {u}]_{{{m_str},{n_str}}}"
    
    def _clamp_lower(self, lower):
        """
        Clamp lower bound to constraint m.
        
        If lower < m, return None (-∞).
        
        Args:
            lower: Lower bound to clamp
        
        Returns:
            Lower bound clamped to m bound
        """
        if lower is None:
            return None
        if self.m != float('-inf') and lower < self.m:
            return None  # Force to -∞
        return lower
    
    def _clamp_upper(self, upper):
        """
        Clamp upper bound to constraint n.
        
        If upper > n, return None (+∞).
        
        Args:
            upper: Upper bound to clamp
        
        Returns:
            Upper bound clamped to n bound
        """
        if upper is None:
            return None
        if self.n != float('+inf') and upper > self.n:
            return None  # Force to +∞
        return upper
    
    # Override lattice operations to preserve constraints
    
    def join(self, other):
        """
        Compute join preserving parametric constraints.
        
        Override parent join to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The join with constraints applied
        """
        if self.is_bottom:
            return other
        if other.is_bottom:
            return self
        
        # Use parent join to compute union
        parent_result = super().join(other)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)
    
    def meet(self, other):
        """
        Compute meet preserving parametric constraints.
        
        Override parent meet to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The meet with constraints applied
        """
        # Use parent meet
        parent_result = super().meet(other)
        
        if parent_result.is_bottom:
            return ParametrizedInterval.bottom(self.m, self.n)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)
    
    # Override arithmetic operations to preserve constraints
    
    def add(self, other):
        """
        Compute addition preserving parametric constraints.
        
        Override parent add to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The sum with constraints applied
        """
        # Use parent addition
        parent_result = super().add(other)
        
        if parent_result.is_bottom:
            return ParametrizedInterval.bottom(self.m, self.n)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)
    
    def sub(self, other):
        """
        Compute subtraction preserving parametric constraints.
        
        Override parent sub to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The difference with constraints applied
        """
        # Use parent subtraction
        parent_result = super().sub(other)
        
        if parent_result.is_bottom:
            return ParametrizedInterval.bottom(self.m, self.n)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)
    
    def mul(self, other):
        """
        Compute multiplication preserving parametric constraints.
        
        Override parent mul to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The product with constraints applied
        """
        # Use parent multiplication
        parent_result = super().mul(other)
        
        if parent_result.is_bottom:
            return ParametrizedInterval.bottom(self.m, self.n)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)
    
    def div(self, other):
        """
        Compute division preserving parametric constraints.
        
        Override parent div to clamp result to [m, n].
        
        Args:
            other: Another ParametrizedInterval
        
        Returns:
            ParametrizedInterval: The quotient with constraints applied
        """
        # Use parent division
        parent_result = super().div(other)
        
        if parent_result.is_bottom:
            return ParametrizedInterval.bottom(self.m, self.n)
        
        # Clamp bounds to constraints
        lower = self._clamp_lower(parent_result.lower)
        upper = self._clamp_upper(parent_result.upper)
        
        return ParametrizedInterval(lower, upper, m=self.m, n=self.n)