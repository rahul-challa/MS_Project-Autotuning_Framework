#!/usr/bin/env python3
"""
Verify Setup - Check that the codebase is ready for use.

This script verifies that all components are properly set up and working.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def verify_imports():
    """Verify all critical imports work."""
    print("Verifying imports...")
    try:
        from autotuner.mab_autotuner import run_maximized_autotuning, run_autotuning
        print("  [OK] mab_autotuner")
    except Exception as e:
        print(f"  [FAIL] mab_autotuner: {e}")
        return False
    
    try:
        from autotuner.benchmark_runner import BenchmarkRunner
        print("  [OK] benchmark_runner")
    except Exception as e:
        print(f"  [FAIL] benchmark_runner: {e}")
        return False
    
    try:
        from autotuner.workload_registry import get_all_workloads, WORKLOADS
        print(f"  [OK] workload_registry ({len(WORKLOADS)} workloads)")
    except Exception as e:
        print(f"  [FAIL] workload_registry: {e}")
        return False
    
    try:
        from autotuner.parameter_matching_optimizer import calculate_combined_error
        print("  [OK] parameter_matching_optimizer")
    except Exception as e:
        print(f"  [FAIL] parameter_matching_optimizer: {e}")
        return False
    
    try:
        from autotuner.system_profiler import SystemProfiler
        print("  [OK] system_profiler")
    except Exception as e:
        print(f"  [FAIL] system_profiler: {e}")
        return False
    
    return True

def verify_structure():
    """Verify project structure."""
    print("\nVerifying project structure...")
    
    required_dirs = [
        'src/autotuner',
        'src/interfaces',
        'scripts',
        'docs',
        'data/results'
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  [OK] {dir_path}/")
        else:
            print(f"  [FAIL] {dir_path}/ missing")
            all_ok = False
    
    return all_ok

def verify_files():
    """Verify essential files exist."""
    print("\nVerifying essential files...")
    
    required_files = [
        'main.py',
        'README.md',
        'requirements.txt',
        'pyproject.toml',  # setup.py consolidated into pyproject.toml
        'src/interfaces/cli.py',
        'src/autotuner/sequential_tuner.py'  # Main autotuner
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} missing")
            all_ok = False
    
    return all_ok

def verify_functionality():
    """Verify basic functionality."""
    print("\nVerifying functionality...")
    
    try:
        from autotuner.workload_registry import get_all_workloads
        workloads = get_all_workloads()
        if len(workloads) >= 15:
            print(f"  [OK] Workload registry ({len(workloads)} workloads)")
        else:
            print(f"  [WARN] Only {len(workloads)} workloads found")
    except Exception as e:
        print(f"  [FAIL] Workload registry: {e}")
        return False
    
    try:
        from autotuner.mab_autotuner import TUNABLE_PARAMETERS
        import math
        total_configs = math.prod(len(v) for v in TUNABLE_PARAMETERS.values())
        print(f"  [OK] Parameter space ({len(TUNABLE_PARAMETERS)} parameters, {total_configs:,} configurations)")
    except Exception as e:
        print(f"  [FAIL] Parameter space: {e}")
        return False
    
    try:
        from autotuner.system_profiler import SystemProfiler
        profiler = SystemProfiler()
        params = profiler.get_actual_parameters()
        if len(params) == 6:
            print(f"  [OK] System profiler (extracted {len(params)} parameters)")
        else:
            print(f"  [WARN] System profiler extracted {len(params)} parameters")
    except Exception as e:
        print(f"  [FAIL] System profiler: {e}")
        return False
    
    return True

def main():
    print("=" * 70)
    print("VERIFYING CODEBASE SETUP")
    print("=" * 70)
    print()
    
    checks = [
        ("Imports", verify_imports),
        ("Structure", verify_structure),
        ("Files", verify_files),
        ("Functionality", verify_functionality)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("VERIFICATION COMPLETE: All checks passed!")
        print("Codebase is ready for use.")
    else:
        print("VERIFICATION COMPLETE: Some checks failed.")
        print("Please review the errors above.")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
