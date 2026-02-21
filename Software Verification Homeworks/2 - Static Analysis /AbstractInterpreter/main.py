from interval import Interval
from state import AbstractState
from ast_nodes import Const, Var, Add, Assign

def test_interval_operations():
    print("=" * 50)
    print("Testing Interval Operations")
    print("=" * 50)
    
    # Test basic intervals
    a = Interval(0, 5)
    b = Interval(1, 2)
    print(f"a = {a}")
    print(f"b = {b}")
    
    # Test add
    print(f"\nAddition:")
    print(f"  a + b = {a.add(b)}")  # [1, 7]
    
    # Test subtraction
    print(f"\nSubtraction:")
    print(f"  a - b = {a.sub(b)}")  # [-2, 4]
    
    # Test join (least upper bound)
    print(f"\nJoin (LUB):")
    print(f"  a ∪ b = {a.join(b)}")  # [0, 5]
    
    # Test meet (greatest lower bound)
    print(f"\nMeet (GLB):")
    print(f"  a ∩ b = {a.meet(b)}")  # [1, 2]
    
    # Test leq (subset ordering)
    print(f"\nLeq (subset):")
    print(f"  b ⊆ a? {b.leq(a)}")  # True
    print(f"  a ⊆ b? {a.leq(b)}")  # False
    
    # Test bottom and top
    print(f"\nBottom and Top:")
    bot = Interval.bottom()
    top = Interval.top()
    print(f"  bottom = {bot}")
    print(f"  top = {top}")
    print(f"  bot + a = {bot.add(a)}")  # should be bottom
    print(f"  bot ∪ a = {bot.join(a)}")  # should be a

def test_cfg_construction():
    from ast_nodes import Assign, Const, Var, While, Sequence, IfThenElse, Skip
    from cfg import build_cfg, print_cfg
    
    print("\n" + "=" * 50)
    print("Testing CFG Construction")
    print("=" * 50)
    
    # Test 1: Simple assignment
    print("\n[Test 1] Simple assignment: x := 5")
    prog1 = Assign('x', Const(5))
    cfg1 = build_cfg(prog1)
    print_cfg(cfg1)
    
    # Test 2: Sequence
    print("\n[Test 2] Sequence: x := 1; y := 2")
    prog2 = Sequence([
        Assign('x', Const(1)),
        Assign('y', Const(2))
    ])
    cfg2 = build_cfg(prog2)
    print_cfg(cfg2)
    
    # Test 3: While loop
    print("\n[Test 3] While loop: while (x) { x := x - 1 }")
    from ast_nodes import Sub
    prog3 = While(
        Var('x'),
        Assign('x', Sub(Var('x'), Const(1)))
    )
    cfg3 = build_cfg(prog3)
    print_cfg(cfg3)
    
    # Test 4: If-then-else
    print("\n[Test 4] If-then-else: if (x) { y := 1 } else { y := 2 }")
    prog4 = IfThenElse(
        Var('x'),
        Assign('y', Const(1)),
        Assign('y', Const(2))
    )
    cfg4 = build_cfg(prog4)
    print_cfg(cfg4)
    
    # Test 5: Complex: x := 0; while (x < 10) { x := x + 1 }
    print("\n[Test 5] Complex: x := 0; while (x < 10) { x := x + 1 }")
    from ast_nodes import Add
    prog5 = Sequence([
        Assign('x', Const(0)),
        While(
            Var('x'),
            Assign('x', Add(Var('x'), Const(1)))
        )
    ])
    cfg5 = build_cfg(prog5)
    print_cfg(cfg5)

def test_abstract_state():
    print("\n" + "=" * 50)
    print("Testing AbstractState")
    print("=" * 50)
    
    # Create initial state with variables x and y
    state1 = AbstractState({'x': Interval(0, 5), 'y': Interval(1, 3)})
    print(f"state1 = {state1}")
    
    # Test assignment
    state2 = state1.assign('x', Interval(10, 20))
    print(f"After assigning x := [10,20]: {state2}")
    
    # Test join of states
    state3 = AbstractState({'x': Interval(5, 10), 'y': Interval(1, 3)})
    joined = state1.join(state3)
    print(f"\nstate1 = {state1}")
    print(f"state3 = {state3}")
    print(f"state1 ∪ state3 = {joined}")
    
    # Test leq
    print(f"\nstate1 ⊆ joined? {state1.leq(joined)}")  # True
    print(f"joined ⊆ state1? {joined.leq(state1)}")  # False
    
    # Test bottom state
    bottom_state = AbstractState.bottom(['x', 'y'])
    print(f"\nbottom state = {bottom_state}")


def test_transfer_functions():
    print("\n" + "=" * 50)
    print("Testing Transfer Functions (AST Evaluation)")
    print("=" * 50)
    
    # We'll test basic expression evaluation by manually checking
    # Const
    c = Const(42)
    print(f"Const(42) = {c.value}")
    
    # Var
    v = Var('x')
    print(f"Var('x') = {v.name}")
    
    # Add
    add_expr = Add(Const(3), Const(4))
    print(f"Add(Const(3), Const(4)) node created")
    
    # Assign
    assign = Assign('x', Const(10))
    print(f"Assign('x', Const(10)) node created")
    
    # While
    from ast_nodes import While
    while_stmt = While(Const(1), Assign('x', Const(5)))
    print(f"While node created")


def test_edge_cases():
    print("\n" + "=" * 50)
    print("Testing Edge Cases")
    print("=" * 50)
    
    # Negative intervals
    neg = Interval(-10, -5)
    print(f"Negative interval: {neg}")
    print(f"  sub(0, [1,2]) = {Interval(0, 0).sub(Interval(1, 2))}")
    
    # Unbounded intervals
    inf_pos = Interval(0, None)  # [0, +∞)
    inf_neg = Interval(None, 0)  # [-∞, 0]
    
    print(f"[0, +∞) = {inf_pos}")
    print(f"[-∞, 0] = {inf_neg}")
    print(f"  [0, +∞) + [1, 2] = {inf_pos.add(Interval(1, 2))}")
    
    # Disjoint intervals should have empty meet
    a = Interval(0, 2)
    b = Interval(5, 10)
    print(f"\nDisjoint intervals:")
    print(f"  [0, 2] ∩ [5, 10] = {a.meet(b)}")  # should be bottom

def test_solver():
    from cfg import build_cfg
    from solver import solve
    from state import AbstractState
    from interval import Interval
    from ast_nodes import Assign, Const, Var, While, Sequence, Add
    
    print("\n" + "=" * 50)
    print("Testing Solver (Fixed-Point Analysis)")
    print("=" * 50)
    
    # Programma: x := 0; while (x < 10) { x := x + 1 }
    prog = Sequence([
        Assign('x', Const(0)),
        While(
            Var('x'),
            Assign('x', Add(Var('x'), Const(1)))
        )
    ])
    
    cfg = build_cfg(prog)
    initial_state = AbstractState({'x': Interval(0, 0)})
    
    print(f"\nInitial state: {initial_state}")
    print(f"CFG nodes: {len(cfg.nodes)}")
    
    states = solve(cfg, initial_state, widening_enabled=True)
    
    print("\n=== Analysis Result ===")
    for node in cfg.nodes:
        print(f"Node {node.id}: {states[node]}")

if __name__ == "__main__":
    test_interval_operations()
    test_abstract_state()
    test_transfer_functions()
    test_edge_cases()
    test_cfg_construction()
    test_solver() 
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)