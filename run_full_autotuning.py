#!/usr/bin/env python3
"""
Full Autotuning Script

Collects ground truth for all workloads and runs autotuning with all MacSim-supported parameters,
then compares predicted vs actual CPU parameters.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autotuner.sequential_tuner import run_sequential_autotuning
from autotuner.benchmark_runner import BenchmarkRunner
from autotuner.system_profiler import SystemProfiler
from autotuner.workload_registry import get_all_workloads
import json

def main():
    print("=" * 80)
    print("Full Autotuning with All Workloads and MacSim Parameters")
    print("=" * 80)
    print()
    
    # Step 1: Collect ground truth for all workloads
    print("Step 1: Collecting ground truth for all workloads...")
    print("-" * 80)
    benchmark_runner = BenchmarkRunner()
    all_workloads = get_all_workloads()
    print(f"Total workloads: {len(all_workloads)}")
    
    ground_truth_file = Path(__file__).parent / 'data' / 'results' / 'ground_truth.json'
    if not ground_truth_file.exists():
        print("Ground truth not found. Collecting now...")
        ground_truth = benchmark_runner.collect_ground_truth(
            workload_ids=None,  # All workloads
            output_file=ground_truth_file
        )
        print(f"✓ Collected ground truth for {len([k for k in ground_truth.keys() if k != '_metadata'])} workloads")
    else:
        with open(ground_truth_file, 'r') as f:
            data = json.load(f)
            workloads_collected = [k for k in data.keys() if k != '_metadata']
            print(f"✓ Ground truth already exists with {len(workloads_collected)} workloads")
    
    print()
    
    # Step 2: Extract actual CPU parameters
    print("Step 2: Extracting actual CPU parameters from system...")
    print("-" * 80)
    system_profiler = SystemProfiler()
    actual_params = system_profiler.get_actual_parameters()
    if not actual_params:
        print("Warning: Actual CPU parameters could not be extracted.")
        print("Actual parameter fields in the final results will be left blank.")
        print()
    else:
        print("Actual CPU parameters:")
        for param, value in sorted(actual_params.items()):
            print(f"  {param:25s}: {value}")
        print()
    
    # Step 3: Run autotuning
    print("Step 3: Running sequential autotuning...")
    print("-" * 80)
    print("Configuration: 5 rounds × 5000 iterations per parameter")
    print("This will take some time...")
    print()
    
    best_config, best_error, error_history, predicted_actual_params, tuning_info = \
        run_sequential_autotuning(
            iterations_per_param=5000,
            num_rounds=5,
            use_multi_metric=True
        )
    
    print()
    print("=" * 80)
    print("Results Summary")
    print("=" * 80)
    print()
    
    # Step 4: Compare predicted vs actual
    print("Predicted Parameters:")
    for param, value in sorted(best_config.items()):
        print(f"  {param:25s}: {value}")
    print()
    
    print("Actual Parameters:")
    for param, value in sorted(actual_params.items()):
        print(f"  {param:25s}: {value}")
    print()
    
    # Calculate matches
    matches = 0
    total = 0
    print("Parameter Comparison:")
    print("-" * 80)
    print(f"{'Parameter':<30} {'Predicted':<15} {'Actual':<15} {'Match':<10}")
    print("-" * 80)
    
    for param in sorted(set(list(best_config.keys()) + list(actual_params.keys()))):
        predicted_val = best_config.get(param, 'N/A')
        actual_val = actual_params.get(param, 'N/A')
        if predicted_val != 'N/A' and actual_val != 'N/A':
            total += 1
            match = "✓" if predicted_val == actual_val else "✗"
            if predicted_val == actual_val:
                matches += 1
            print(f"{param:<30} {str(predicted_val):<15} {str(actual_val):<15} {match:<10}")
    
    print("-" * 80)
    match_percent = (matches / total * 100) if total > 0 else 0
    print(f"Matches: {matches}/{total} ({match_percent:.2f}%)")
    print(f"Best Error: {best_error:.9f}")
    print()
    
    # Save results
    results_file = Path(__file__).parent / 'data' / 'results' / 'full_autotuning_results.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'predicted_parameters': best_config,
            'actual_parameters': actual_params,
            'matches': matches,
            'total_parameters': total,
            'match_percent': match_percent,
            'best_error': float(best_error),
            'tuning_info': tuning_info,
            'workloads_used': len(all_workloads)
        }, f, indent=2)
    
    print(f"Results saved to: {results_file}")
    print()
    print("=" * 80)
    print("Autotuning Complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()
