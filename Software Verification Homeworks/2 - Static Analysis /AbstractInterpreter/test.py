"""
Unit tests for the Abstract Interpreter.

This module contains comprehensive tests for all components of the abstract
interpreter: intervals, states, CFG construction, transfer functions, and
the fixed-point solver.
"""

import unittest
from interval import Interval
from interval_parametrized import ParametrizedInterval
from state import AbstractState
from ast_nodes import Const, Var, Add, Sub, Assign, While, Sequence, IfThenElse, Skip
from cfg import build_cfg, print_cfg
from solver import solve


class TestIntervalOperations(unittest.TestCase):
    """Unit tests for the Interval abstract domain."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.a = Interval(0, 5)
        self.b = Interval(1, 2)
        self.bottom = Interval.bottom()
        self.top = Interval.top()
    
    def test_interval_creation(self):
        """Test basic interval creation."""
        self.assertEqual(self.a.lower, 0)
        self.assertEqual(self.a.upper, 5)
        self.assertFalse(self.a.is_bottom)
    
    def test_bottom_element(self):
        """Test the bottom element."""
        self.assertTrue(self.bottom.is_bottom)
    
    def test_top_element(self):
        """Test the top element."""
        self.assertIsNone(self.top.lower)
        self.assertIsNone(self.top.upper)
        self.assertFalse(self.top.is_bottom)
    
    def test_addition(self):
        """Test interval addition."""
        result = self.a.add(self.b)
        self.assertEqual(result.lower, 1)  # 0 + 1
        self.assertEqual(result.upper, 7)  # 5 + 2
    
    def test_subtraction(self):
        """Test interval subtraction."""
        result = self.a.sub(self.b)
        self.assertEqual(result.lower, -2)  # 0 - 2
        self.assertEqual(result.upper, 4)   # 5 - 1
    
    def test_multiplication(self):
        """Test interval multiplication."""
        result = self.a.mul(self.b)
        self.assertEqual(result.lower, 0)   # min(0*1, 0*2, 5*1, 5*2)
        self.assertEqual(result.upper, 10)  # max(0*1, 0*2, 5*1, 5*2)
    
    def test_division(self):
        """Test interval division (no division by zero)."""
        c = Interval(2, 5)  # Positive divisor
        result = self.a.div(c)
        self.assertFalse(result.is_bottom)
    
    def test_division_by_zero(self):
        """Test division by zero returns bottom."""
        zero_interval = Interval(-1, 1)  # Contains 0
        result = self.a.div(zero_interval)
        self.assertTrue(result.is_bottom)
    
    def test_join(self):
        """Test join (least upper bound)."""
        result = self.a.join(self.b)
        self.assertEqual(result.lower, 0)  # min(0, 1)
        self.assertEqual(result.upper, 5)  # max(5, 2)
    
    def test_meet(self):
        """Test meet (greatest lower bound)."""
        result = self.a.meet(self.b)
        self.assertEqual(result.lower, 1)  # max(0, 1)
        self.assertEqual(result.upper, 2)  # min(5, 2)
    
    def test_leq_ordering(self):
        """Test the partial order relation."""
        self.assertTrue(self.b.leq(self.a))  # [1,2] ⊆ [0,5]
        self.assertFalse(self.a.leq(self.b))  # [0,5] ⊄ [1,2]
    
    def test_bottom_leq(self):
        """Test that bottom is less than or equal to everything."""
        self.assertTrue(self.bottom.leq(self.a))
        self.assertTrue(self.bottom.leq(self.top))
    
    def test_infinite_bounds(self):
        """Test intervals with infinite bounds."""
        neg_inf = Interval(None, 5)  # (-∞, 5]
        pos_inf = Interval(0, None)  # [0, +∞)
        result = neg_inf.join(pos_inf)
        self.assertIsNone(result.lower)
        self.assertIsNone(result.upper)
    
    def test_interval_repr(self):
        """Test string representation of intervals."""
        self.assertEqual(repr(self.a), "[0, 5]")
        self.assertEqual(repr(self.bottom), "⊥")
        self.assertEqual(repr(self.top), "[-∞, +∞]")


class TestAbstractState(unittest.TestCase):
    """Unit tests for the AbstractState domain."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state1 = AbstractState({'x': Interval(0, 5), 'y': Interval(1, 3)})
        self.state2 = AbstractState({'x': Interval(5, 10), 'y': Interval(1, 3)})
        self.var_names = ['x', 'y']
    
    def test_state_creation(self):
        """Test abstract state creation."""
        self.assertIn('x', self.state1.env)
        self.assertIn('y', self.state1.env)
    
    def test_state_bottom(self):
        """Test bottom state creation."""
        bottom_state = AbstractState.bottom(self.var_names)
        self.assertTrue(bottom_state.env['x'].is_bottom)
        self.assertTrue(bottom_state.env['y'].is_bottom)
    
    def test_state_assignment(self):
        """Test variable assignment in a state."""
        new_state = self.state1.assign('x', Interval(10, 20))
        self.assertEqual(new_state.env['x'].lower, 10)
        self.assertEqual(new_state.env['x'].upper, 20)
        # Original state unchanged
        self.assertEqual(self.state1.env['x'].lower, 0)
    
    def test_state_join(self):
        """Test join of two states."""
        joined = self.state1.join(self.state2)
        self.assertEqual(joined.env['x'].lower, 0)   # min(0, 5)
        self.assertEqual(joined.env['x'].upper, 10)  # max(5, 10)
    
    def test_state_leq(self):
        """Test partial order on states."""
        self.assertTrue(self.state1.leq(self.state2.join(self.state1)))
    
    def test_state_repr(self):
        """Test string representation of states."""
        repr_str = repr(self.state1)
        self.assertIn('x', repr_str)
        self.assertIn('y', repr_str)


class TestCFGConstruction(unittest.TestCase):
    """Unit tests for Control Flow Graph construction."""
    
    def test_simple_assignment(self):
        """Test CFG for simple assignment: x := 5"""
        prog = Assign('x', Const(5))
        cfg = build_cfg(prog)
        
        self.assertIsNotNone(cfg.entry)
        self.assertIsNotNone(cfg.exit)
        self.assertEqual(len(cfg.nodes), 1)
    
    def test_sequence(self):
        """Test CFG for sequence: x := 1; y := 2"""
        prog = Sequence([
            Assign('x', Const(1)),
            Assign('y', Const(2))
        ])
        cfg = build_cfg(prog)
        
        self.assertEqual(len(cfg.nodes), 2)
        # First node should connect to second
        self.assertTrue(any(succ.id == 1 for succ in cfg.nodes[0].succ))
    
    def test_while_loop(self):
        """Test CFG for while loop."""
        prog = While(
            Var('x'),
            Assign('x', Sub(Var('x'), Const(1)))
        )
        cfg = build_cfg(prog)
        
        # While should have: condition node + body node + exit node
        self.assertGreaterEqual(len(cfg.nodes), 2)
    
    def test_if_then_else(self):
        """Test CFG for if-then-else statement."""
        prog = IfThenElse(
            Var('x'),
            Assign('y', Const(1)),
            Assign('y', Const(2))
        )
        cfg = build_cfg(prog)
        
        # Should have: condition + then branch + else branch + merge node
        self.assertGreaterEqual(len(cfg.nodes), 3)
    
    def test_complex_program(self):
        """Test CFG for complex program: x := 0; while (x) { x := x + 1 }"""
        prog = Sequence([
            Assign('x', Const(0)),
            While(
                Var('x'),
                Assign('x', Add(Var('x'), Const(1)))
            )
        ])
        cfg = build_cfg(prog)
        
        self.assertIsNotNone(cfg.entry)
        self.assertIsNotNone(cfg.exit)
        self.assertGreater(len(cfg.nodes), 2)


class TestTransferFunctions(unittest.TestCase):
    """Unit tests for transfer functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state = AbstractState({'x': Interval(0, 5), 'y': Interval(1, 3)})
    
    def test_eval_const(self):
        """Test evaluation of constant expressions."""
        from transfer import eval_aexp
        result = eval_aexp(Const(42), self.state)
        self.assertEqual(result.lower, 42)
        self.assertEqual(result.upper, 42)
    
    def test_eval_var(self):
        """Test evaluation of variable expressions."""
        from transfer import eval_aexp
        result = eval_aexp(Var('x'), self.state)
        self.assertEqual(result.lower, 0)
        self.assertEqual(result.upper, 5)
    
    def test_eval_add(self):
        """Test evaluation of addition expressions."""
        from transfer import eval_aexp
        expr = Add(Var('x'), Var('y'))
        result = eval_aexp(expr, self.state)
        self.assertEqual(result.lower, 1)   # 0 + 1
        self.assertEqual(result.upper, 8)   # 5 + 3
    
    def test_transfer_assign(self):
        """Test transfer function for assignments."""
        from transfer import transfer_assign
        stmt = Assign('x', Const(42))
        new_state = transfer_assign(stmt, self.state)
        
        self.assertEqual(new_state.env['x'].lower, 42)
        self.assertEqual(new_state.env['x'].upper, 42)


class TestFixedPointSolver(unittest.TestCase):
    """Unit tests for the fixed-point solver."""
    
    def test_simple_assignment_analysis(self):
        """Test analysis of simple assignment."""
        prog = Assign('x', Const(5))
        cfg = build_cfg(prog)
        initial_state = AbstractState({'x': Interval(0, 0)})
        
        states = solve(cfg, initial_state)
        
        self.assertIsNotNone(states)
        self.assertEqual(len(states), len(cfg.nodes))
    
    def test_sequence_analysis(self):
        """Test analysis of statement sequence."""
        prog = Sequence([
            Assign('x', Const(1)),
            Assign('y', Const(2))
        ])
        cfg = build_cfg(prog)
        initial_state = AbstractState({'x': Interval(0, 0), 'y': Interval(0, 0)})
        
        states = solve(cfg, initial_state)
        
        self.assertEqual(len(states), 2)
    
    def test_widening(self):
        """Test analysis with widening enabled."""
        prog = While(
            Var('x'),
            Assign('x', Add(Var('x'), Const(1)))
        )
        cfg = build_cfg(prog)
        initial_state = AbstractState({'x': Interval(0, 0)})
        
        states_with_widening = solve(cfg, initial_state, widening_enabled=True)
        
        # With widening, should converge
        self.assertIsNotNone(states_with_widening)

class TestParametrizedIntervals(unittest.TestCase):
    """Unit tests for the parametrized interval domain Int_{m,n}."""
    
    def setUp(self):
        """Set up test fixtures."""
        from interval_parametrized import ParametrizedInterval
        
        # Standard interval domain Int_{-∞, +∞}
        self.a = ParametrizedInterval(0, 5)
        self.b = ParametrizedInterval(1, 2)
        
        # Bounded domain Int_{0, 100}
        self.a_bounded = ParametrizedInterval(0, 5, m=0, n=100)
        self.b_bounded = ParametrizedInterval(1, 2, m=0, n=100)
        
        # Constant propagation domain Int_{10, 5} (m > n)
        self.const_prop = ParametrizedInterval(42, 42, m=10, n=5)
        
        self.bottom = ParametrizedInterval.bottom()
        self.top = ParametrizedInterval.top()
    
    def test_parametrized_interval_creation(self):
        """Test creation of parametrized intervals."""
        self.assertEqual(self.a.lower, 0)
        self.assertEqual(self.a.upper, 5)
        self.assertEqual(self.a.m, float('-inf'))
        self.assertEqual(self.a.n, float('+inf'))
    
    def test_bounded_interval_creation(self):
        """Test creation with bounds m and n."""
        self.assertEqual(self.a_bounded.m, 0)
        self.assertEqual(self.a_bounded.n, 100)
    
    def test_constraint_violation(self):
        """Test that intervals outside [m,n] are rejected."""
        from interval_parametrized import ParametrizedInterval
        
        with self.assertRaises(AssertionError):
            # Try to create [50, 150] in Int_{0, 100}
            ParametrizedInterval(50, 150, m=0, n=100)
    
    def test_bottom_element(self):
        """Test bottom element properties."""
        from interval_parametrized import ParametrizedInterval
        
        self.assertTrue(self.bottom.is_bottom)
        # Bottom with constraints
        bottom_bounded = ParametrizedInterval.bottom(m=0, n=100)
        self.assertTrue(bottom_bounded.is_bottom)
        self.assertEqual(bottom_bounded.m, 0)
        self.assertEqual(bottom_bounded.n, 100)
    
    def test_top_element(self):
        """Test top element properties."""
        self.assertIsNone(self.top.lower)
        self.assertIsNone(self.top.upper)
        self.assertFalse(self.top.is_bottom)
    
    def test_is_singleton(self):
        """Test singleton interval detection."""
        singleton = ParametrizedInterval(42, 42)
        self.assertTrue(singleton.is_singleton())
        
        non_singleton = ParametrizedInterval(0, 5)
        self.assertFalse(non_singleton.is_singleton())
        
        infinite = ParametrizedInterval(None, None)
        self.assertFalse(infinite.is_singleton())
    
    def test_constant_propagation_domain(self):
        """Test detection of constant propagation domain (m > n)."""
        from interval_parametrized import ParametrizedInterval
        
        const_prop = ParametrizedInterval(42, 42, m=10, n=5)
        self.assertTrue(const_prop.is_constant_propagation_domain())
        
        normal = ParametrizedInterval(42, 42, m=0, n=100)
        self.assertFalse(normal.is_constant_propagation_domain())
    
    def test_bounded_addition(self):
        """Test addition with bounded domain."""
        result = self.a_bounded.add(self.b_bounded)
        self.assertEqual(result.lower, 1)   # 0 + 1
        self.assertEqual(result.upper, 7)   # 5 + 2
        self.assertEqual(result.m, 0)
        self.assertEqual(result.n, 100)
    
    def test_addition_clamping(self):
        """Test that addition results are clamped to [m, n]."""
        from interval_parametrized import ParametrizedInterval
        
        # Int_{0, 10}: [5, 8] + [2, 5] = [7, 13] -> clamped to [7, 10]
        a = ParametrizedInterval(5, 8, m=0, n=10)
        b = ParametrizedInterval(2, 5, m=0, n=10)
        result = a.add(b)
        
        self.assertEqual(result.lower, 7)
        self.assertIsNone(result.upper)  # Clamped to +∞ (exceeds n)
    
    def test_subtraction_with_bounds(self):
        """Test subtraction with bounded domain."""
        result = self.a_bounded.sub(self.b_bounded)
        self.assertEqual(result.lower, -2)  # 0 - 2
        self.assertEqual(result.upper, 4)   # 5 - 1
    
    def test_multiplication_with_bounds(self):
        """Test multiplication with bounded domain."""
        result = self.a_bounded.mul(self.b_bounded)
        self.assertEqual(result.lower, 0)
        self.assertEqual(result.upper, 10)
    
    def test_division_no_zero(self):
        """Test division when divisor has no zero."""
        from interval_parametrized import ParametrizedInterval
        
        dividend = ParametrizedInterval(10, 20)
        divisor = ParametrizedInterval(2, 5)
        result = dividend.div(divisor)
        
        self.assertFalse(result.is_bottom)
        self.assertEqual(result.lower, 2)   # 10 // 5
        self.assertEqual(result.upper, 10)  # 20 // 2
    
    def test_division_by_zero(self):
        """Test division by zero returns bottom."""
        from interval_parametrized import ParametrizedInterval
        
        dividend = ParametrizedInterval(10, 20)
        divisor = ParametrizedInterval(-1, 1)  # Contains 0
        result = dividend.div(divisor)
        
        self.assertTrue(result.is_bottom)
    
    def test_join(self):
        """Test join (union) operation."""
        result = self.a_bounded.join(self.b_bounded)
        self.assertEqual(result.lower, 0)   # min(0, 1)
        self.assertEqual(result.upper, 5)   # max(5, 2)
    
    def test_join_with_infinity(self):
        """Test join that results in infinity."""
        from interval_parametrized import ParametrizedInterval
        
        a = ParametrizedInterval(0, 50, m=0, n=100)
        b = ParametrizedInterval(60, None, m=0, n=100)  # [60, +∞]
        result = a.join(b)
        
        self.assertEqual(result.lower, 0)
        self.assertIsNone(result.upper)  # +∞
    
    def test_meet(self):
        """Test meet (intersection) operation."""
        result = self.a_bounded.meet(self.b_bounded)
        self.assertEqual(result.lower, 1)   # max(0, 1)
        self.assertEqual(result.upper, 2)   # min(5, 2)
    
    def test_meet_no_overlap(self):
        """Test meet with non-overlapping intervals returns bottom."""
        from interval_parametrized import ParametrizedInterval
        
        a = ParametrizedInterval(0, 5, m=0, n=100)
        b = ParametrizedInterval(10, 20, m=0, n=100)
        result = a.meet(b)
        
        self.assertTrue(result.is_bottom)
    
    def test_leq_ordering(self):
        """Test partial order with bounded domain."""
        self.assertTrue(self.b_bounded.leq(self.a_bounded))
        self.assertFalse(self.a_bounded.leq(self.b_bounded))
    
    def test_bottom_leq(self):
        """Test that bottom is less-than-or-equal to everything."""
        from interval_parametrized import ParametrizedInterval
        
        bottom = ParametrizedInterval.bottom(m=0, n=100)
        self.assertTrue(bottom.leq(self.a_bounded))
        self.assertTrue(bottom.leq(self.bottom))
    
    def test_repr_standard(self):
        """Test string representation of standard intervals."""
        self.assertEqual(repr(self.a), "[0, 5]_{-∞,+∞}")
        self.assertEqual(repr(self.bottom), "⊥_{-∞,+∞}")
    
    def test_repr_bounded(self):
        """Test string representation of bounded intervals."""
        self.assertEqual(repr(self.a_bounded), "[0, 5]_{0,100}")
    
    def test_repr_const_prop(self):
        """Test string representation of constant propagation intervals."""
        self.assertEqual(repr(self.const_prop), "[42, 42]_{10,5}")
    
    def test_multiple_constraints(self):
        """Test operations preserve constraints."""
        from interval_parametrized import ParametrizedInterval
        
        a = ParametrizedInterval(10, 20, m=0, n=100)
        b = ParametrizedInterval(5, 15, m=0, n=100)
        
        # All operations should preserve m=0, n=100
        for result in [a.add(b), a.sub(b), a.mul(b), a.join(b), a.meet(b)]:
            self.assertEqual(result.m, 0)
            self.assertEqual(result.n, 100)
    
    def test_parametrized_bounds_consistency(self):
        """Test that operations maintain consistency with bounds."""
        from interval_parametrized import ParametrizedInterval
        
        # Int_{-10, 10}: ensure results stay within bounds
        a = ParametrizedInterval(-5, 5, m=-10, n=10)
        b = ParametrizedInterval(-3, 3, m=-10, n=10)
        
        result_add = a.add(b)
        # [-5 + (-3), 5 + 3] = [-8, 8] within [-10, 10]
        self.assertEqual(result_add.lower, -8)
        self.assertEqual(result_add.upper, 8)

class TestEdgeCases(unittest.TestCase):
    """Unit tests for edge cases and corner cases."""
    
    def test_empty_sequence(self):
        """Test handling of empty sequence."""
        from ast_nodes import Sequence
        from cfg import build_cfg
        
        prog = Sequence([])
        cfg = build_cfg(prog)
        
        # Empty sequence should still have entry and exit
        self.assertIsNotNone(cfg.entry)
        self.assertIsNotNone(cfg.exit)
    
    def test_skip_statement(self):
        """Test Skip statement."""
        prog = Skip()
        cfg = build_cfg(prog)
        
        self.assertEqual(len(cfg.nodes), 1)
    
    def test_nested_while(self):
        """Test nested while loops."""
        prog = While(
            Var('x'),
            While(
                Var('y'),
                Assign('y', Sub(Var('y'), Const(1)))
            )
        )
        cfg = build_cfg(prog)
        
        self.assertGreater(len(cfg.nodes), 3)
    
    def test_negative_intervals(self):
        """Test intervals with negative values."""
        iv = Interval(-10, -5)
        self.assertEqual(iv.lower, -10)
        self.assertEqual(iv.upper, -5)
    
    def test_singleton_interval(self):
        """Test singleton intervals."""
        iv = Interval(42, 42)
        self.assertEqual(iv.lower, 42)
        self.assertEqual(iv.upper, 42)


def run_all_tests():
    """Run all unit tests with verbose output."""
    print("=" * 70)
    print("Running Abstract Interpreter Unit Tests")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntervalOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestAbstractState))
    suite.addTests(loader.loadTestsFromTestCase(TestCFGConstruction))
    suite.addTests(loader.loadTestsFromTestCase(TestTransferFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestFixedPointSolver))
    suite.addTests(loader.loadTestsFromTestCase(TestParametrizedIntervals))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    return result


if __name__ == "__main__":
    # Run all tests
    run_all_tests()