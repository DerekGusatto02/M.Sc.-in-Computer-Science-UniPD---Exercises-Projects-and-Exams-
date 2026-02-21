class Interval:
    """Represents an abstract interval domain for numeric values.
    
    An interval is a contiguous set of integers represented by lower and upper bounds.
    Special values:
    - bottom (⊥): represents an unreachable/empty set of values
    - top (⊤): represents all possible integer values (-∞, +∞)
    - None for bounds: represents infinity (-∞ for lower, +∞ for upper)
    
    Attributes:
        lower: The lower bound of the interval (None = -∞)
        upper: The upper bound of the interval (None = +∞)
        is_bottom: Boolean flag indicating if this is the bottom element
    """
    
    def __init__(self, lower=None, upper=None, is_bottom=False):
        """Initializes an interval with given bounds.
        
        Args:
            lower: Lower bound (integer or None for -∞), default None
            upper: Upper bound (integer or None for +∞), default None
            is_bottom: Boolean flag for bottom element, default False
        """
        self.lower = lower      # None represents -∞
        self.upper = upper      # None represents +∞
        self.is_bottom = is_bottom

    @staticmethod
    def bottom():
        """Creates the bottom element representing an unreachable state.
        
        Returns:
            Interval: The bottom interval (⊥)
        """
        return Interval(is_bottom=True)

    @staticmethod
    def top():
        """Creates the top element representing all possible values.
        
        Returns:
            Interval: The top interval [-∞, +∞]
        """
        return Interval(None, None)
    
    def __repr__(self):
        """Returns a string representation of the interval.
        
        Returns:
            str: A formatted string showing the interval bounds or ⊥ for bottom
        """
        if self.is_bottom:
            return "⊥"
        l = "-∞" if self.lower is None else str(self.lower)
        u = "+∞" if self.upper is None else str(self.upper)
        return f"[{l}, {u}]"
    
    def leq(self, other):
        """Checks the partial order relation (subset ordering).
        
        This interval is less-than-or-equal-to (leq) another interval if it is
        a subset of it. This is the subset relation on intervals.
        
        Args:
            other: Another Interval object
        
        Returns:
            bool: True if self ⊆ other, False otherwise
        """
        if self.is_bottom:
            # Bottom is a subset of any interval
            return True
        if other.is_bottom:
            # Only bottom is a subset of bottom
            return False

        # Check lower bound: self's lower must be ≥ other's lower
        lower_ok = (
            other.lower is None or
            (self.lower is not None and other.lower <= self.lower)
        )

        # Check upper bound: self's upper must be ≤ other's upper
        upper_ok = (
            other.upper is None or
            (self.upper is not None and self.upper <= other.upper)
        )

        return lower_ok and upper_ok
    
    def join(self, other):
        """Computes the least upper bound (join) of two intervals.
        
        The join represents the smallest interval containing both input intervals.
        This is the union operation: the result is the smallest interval that
        encompasses both intervals.
        
        Args:
            other: Another Interval object
        
        Returns:
            Interval: The join of self and other
        """
        if self.is_bottom:
            return other
        if other.is_bottom:
            return self

        # Lower bound: take the minimum (smallest of the two)
        lower = min(
            x for x in [self.lower, other.lower] if x is not None
        ) if self.lower is not None and other.lower is not None else None

        # Upper bound: take the maximum (largest of the two)
        upper = max(
            x for x in [self.upper, other.upper] if x is not None
        ) if self.upper is not None and other.upper is not None else None

        return Interval(lower, upper)
    
    def meet(self, other):
        """Computes the greatest lower bound (meet) of two intervals.
        
        The meet represents the largest interval contained in both input intervals.
        This is the intersection operation: the result is the largest interval that
        is contained in both intervals. If there is no overlap, returns bottom.
        
        Args:
            other: Another Interval object
        
        Returns:
            Interval: The meet of self and other
        """
        if self.is_bottom or other.is_bottom:
            return Interval.bottom()

        # Lower bound: take the maximum (largest of the two minima)
        lower = max(
            x for x in [self.lower, other.lower] if x is not None
        ) if self.lower is not None and other.lower is not None else self.lower or other.lower

        # Upper bound: take the minimum (smallest of the two maxima)
        upper = min(
            x for x in [self.upper, other.upper] if x is not None
        ) if self.upper is not None and other.upper is not None else self.upper or other.upper

        # If lower > upper, the intervals don't overlap: return bottom
        if lower is not None and upper is not None and lower > upper:
            return Interval.bottom()

        return Interval(lower, upper)

    def add(self, other):
        """Computes the interval resulting from addition of two intervals.
        
        For intervals [a, b] and [c, d], the sum is [a+c, b+d].
        If either interval is bottom, returns bottom.
        If either bound is infinite, the result bound is also infinite.
        
        Args:
            other: Another Interval object
        
        Returns:
            Interval: The interval representing all possible sums
        """
        if self.is_bottom or other.is_bottom:
            return Interval.bottom()

        # Lower bound: sum of lower bounds (None if either is None)
        lower = None if self.lower is None or other.lower is None else self.lower + other.lower
        # Upper bound: sum of upper bounds (None if either is None)
        upper = None if self.upper is None or other.upper is None else self.upper + other.upper

        return Interval(lower, upper)

    def sub(self, other):
        """Computes the interval resulting from subtraction of two intervals.
        
        For intervals [a, b] and [c, d], the difference is [a-d, b-c].
        If either interval is bottom, returns bottom.
        If either bound is infinite, the result bound is also infinite.
        
        Args:
            other: Another Interval object (the subtrahend)
        
        Returns:
            Interval: The interval representing all possible differences
        """
        if self.is_bottom or other.is_bottom:
            return Interval.bottom()

        # Lower bound: minuend's lower minus subtrahend's upper
        lower = None if self.lower is None or other.upper is None else self.lower - other.upper
        # Upper bound: minuend's upper minus subtrahend's lower
        upper = None if self.upper is None or other.lower is None else self.upper - other.lower

        return Interval(lower, upper)
    
    def mul(self, other):
        """Computes the interval resulting from multiplication of two intervals.
        
        For intervals [a, b] and [c, d], we compute all four corner products:
        a*c, a*d, b*c, b*d and return [min, max].
        If either interval is bottom, returns bottom.
        
        Args:
            other: Another Interval object
        
        Returns:
            Interval: The interval representing all possible products
        """
        if self.is_bottom or other.is_bottom:
            return Interval.bottom()

        # Compute all four corner products
        products = []
        for l in [self.lower, self.upper]:
            for r in [other.lower, other.upper]:
                if l is not None and r is not None:
                    products.append(l * r)
        
        # If no finite products, return top
        if not products:
            return Interval(None, None)

        # Return interval from minimum to maximum product
        lower = min(p for p in products if p is not None)
        upper = max(p for p in products if p is not None)
        
        return Interval(lower, upper)

    def div(self, other):
        """Computes the interval resulting from integer division of two intervals.
        
        For intervals [a, b] and [c, d], integer division is performed on all
        valid corner quotients. If 0 is in the divisor interval, the result is
        bottom (representing a runtime error: division by zero).
        
        Args:
            other: Another Interval object (the divisor)
        
        Returns:
            Interval: The interval representing all possible quotients, or bottom
                     if division by zero is possible
        """
        if self.is_bottom or other.is_bottom:
            return Interval.bottom()

        # Check if 0 is in the divisor interval
        if (other.lower is None or other.lower <= 0) and \
           (other.upper is None or other.upper >= 0):
            # 0 could be in other interval: division by zero is possible
            return Interval.bottom()
        
        # No zero in divisor: compute all valid corner quotients
        quotients = []
        for l in [self.lower, self.upper]:
            for r in [other.lower, other.upper]:
                if l is not None and r is not None and r != 0:
                    quotients.append(l // r)  # Integer division
        
        # If no quotients computed, return bottom
        if not quotients:
            return Interval.bottom()

        # Return interval from minimum to maximum quotient
        lower = min(quotients)
        upper = max(quotients)
        
        return Interval(lower, upper)