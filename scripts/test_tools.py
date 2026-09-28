"""
scripts/test_tools.py
---------------------
Independent tests for the Tool Framework (Part 4).
"""
import sys
import os

# Ensure the project root is on sys.path so `backend.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools import Tool, ToolRegistry, ToolExecutor, CalculatorTool

SEP = '-' * 56

def run_tests() -> None:
    print(SEP)
    print('  HackwithHyderabad Agent -- Tool Framework Test')
    print(SEP)
    
    all_passed = True
    
    # TEST 1 â€” Tool creation
    try:
        calc = CalculatorTool()
        assert calc.name == "calculator"
        print("  [PASS] Tool creation")
    except Exception as e:
        print(f"  [FAIL] Tool creation: {e}")
        all_passed = False
        
    # TEST 2 â€” Registration
    registry = ToolRegistry()
    try:
        registry.register(calc)
        assert registry.has_tool("calculator")
        tools = registry.list_tools()
        assert any(t["name"] == "calculator" for t in tools)
        print("  [PASS] Tool registration")
    except Exception as e:
        print(f"  [FAIL] Tool registration: {e}")
        all_passed = False
        
    # TEST 3 â€” Duplicate registration
    try:
        registry.register(CalculatorTool())
        print("  [FAIL] Duplicate registration handled (should have raised error)")
        all_passed = False
    except ValueError:
        print("  [PASS] Duplicate registration handling")
    except Exception as e:
        print(f"  [FAIL] Duplicate registration handled incorrectly: {e}")
        all_passed = False
        
    # Set up executor
    executor = ToolExecutor(registry)
        
    # TEST 4 â€” Successful execution
    try:
        res = executor.execute("calculator", {"operation": "add", "a": 10, "b": 20})
        assert res["success"] is True
        assert res["result"] == 30
        print("  [PASS] Calculator execution")
    except Exception as e:
        print(f"  [FAIL] Calculator execution: {e}")
        all_passed = False
        
    # TEST 5 â€” Another operation
    try:
        res = executor.execute("calculator", {"operation": "multiply", "a": 5, "b": 4})
        assert res["success"] is True
        assert res["result"] == 20
        print("  [PASS] Multiple operation execution")
    except Exception as e:
        print(f"  [FAIL] Multiple operation execution: {e}")
        all_passed = False
        
    # TEST 6 â€” Unknown tool
    try:
        res = executor.execute("unknown_tool", {})
        assert res["success"] is False
        assert "Unknown tool" in res["error"]
        print("  [PASS] Unknown tool handling")
    except Exception as e:
        print(f"  [FAIL] Unknown tool handling: {e}")
        all_passed = False
        
    # TEST 7 â€” Invalid arguments
    try:
        # Missing 'b'
        res = executor.execute("calculator", {"operation": "add", "a": 10})
        assert res["success"] is False
        assert "Invalid arguments" in res["error"] or "missing 1 required positional argument" in res["error"]
        print("  [PASS] Invalid argument handling")
    except Exception as e:
        print(f"  [FAIL] Invalid argument handling: {e}")
        all_passed = False
        
    # TEST 8 â€” Division safety
    try:
        res = executor.execute("calculator", {"operation": "divide", "a": 10, "b": 0})
        assert res["success"] is False
        assert "Division by zero" in res["error"] or "division by zero" in res["error"].lower()
        print("  [PASS] Division-by-zero handling")
    except Exception as e:
        print(f"  [FAIL] Division-by-zero handling: {e}")
        all_passed = False

    print(SEP)
    if all_passed:
        print("  [PASS] Tool Framework verified")
    else:
        print("  [FAIL] Tool Framework verification failed")
        sys.exit(1)
    print(SEP)

if __name__ == '__main__':
    run_tests()
