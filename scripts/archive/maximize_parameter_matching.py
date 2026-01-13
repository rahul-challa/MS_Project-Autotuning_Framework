#!/usr/bin/env python3
"""
Maximize Parameter Matching - Standalone Script

This script provides a standalone interface to the maximized autotuning function.
For most users, the CLI interface is recommended: python -m interfaces.cli autotune
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autotuner.mab_autotuner import run_maximized_autotuning, create_convergence_plot
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description='Predict CPU parameters using ONLY performance metrics',
        epilog='Note: Actual CPU parameters are NOT used during optimization, only for validation at the end.'
    )
    parser.add_argument('--iterations', type=int, default=500, help='Number of iterations (recommended: 500+)')
    parser.add_argument('--use-multi-metric', action='store_true', default=True, help='Use all available metrics')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CPU PARAMETER PREDICTION")
    print("=" * 70)
    print("Using ONLY performance metrics for prediction")
    print("(Actual parameters used only for validation)")
    print()
    
    # Run maximized autotuning (imported from main module)
    best_config, best_error, error_history, best_iteration, actual_params, match_history = run_maximized_autotuning(
        max_iterations=args.iterations,
        use_multi_metric=args.use_multi_metric
    )
    
    # Save results
    results_dir = Path(__file__).parent.parent / 'data' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results JSON
    results_data = {
        'best_config': best_config,
        'actual_parameters': actual_params,
        'best_error': best_error,
        'best_iteration': best_iteration,
        'error_history': error_history,
        'match_history': match_history,
        'iterations': len(error_history),
        'use_multi_metric': args.use_multi_metric,
        'note': 'Parameters predicted using ONLY performance metrics. Actual parameters used only for validation.',
        'max_matches': max(match_history) if match_history else 0,
        'final_matches': match_history[-1] if match_history else 0
    }
    
    results_file = results_dir / 'maximized_results.json'
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    print(f"\nResults saved to: {results_file}")
    
    # Create convergence plot
    plot_file = results_dir / 'maximized_convergence.png'
    create_convergence_plot(error_history, best_error, best_config, str(plot_file))
    
    # Print comparison
    print("\n" + "=" * 70)
    print("VALIDATION: PREDICTED vs ACTUAL PARAMETERS")
    print("=" * 70)
    print(f"{'Parameter':<20} {'Best Config':<15} {'Actual':<15} {'Match':<10} {'Difference':<10}")
    print("-" * 70)
    
    matches = 0
    for param in ['rob_size', 'l1_cache_size', 'l2_cache_size', 'issue_width', 'l1_latency', 'l2_latency']:
        best_val = best_config[param]
        actual_val = actual_params[param]
        diff = abs(best_val - actual_val)
        match = "YES" if best_val == actual_val else "NO"
        if match == "YES":
            matches += 1
        print(f"{param:<20} {best_val:<15} {actual_val:<15} {match:<10} {diff:<10}")
    
    print("-" * 70)
    print(f"Match Percentage: {matches}/6 ({matches/6*100:.1f}%)")
    
    # Show match progression
    if match_history:
        print(f"\nMatch progression:")
        print(f"  Initial matches: {match_history[0]}/6")
        print(f"  Final matches: {match_history[-1]}/6")
        print(f"  Maximum matches: {max(match_history)}/6")
        print(f"  Average matches: {np.mean(match_history):.2f}/6")
    
    print("=" * 70)


if __name__ == '__main__':
    main()
