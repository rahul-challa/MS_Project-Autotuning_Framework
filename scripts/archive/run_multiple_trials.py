#!/usr/bin/env python3
"""
Run multiple autotuning trials and track the best result.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from autotuner.mab_autotuner import run_maximized_autotuning
from autotuner.system_profiler import SystemProfiler

def count_matches(predicted: dict, actual: dict) -> int:
    """Count how many parameters match exactly."""
    matches = 0
    for param in predicted:
        if predicted[param] == actual[param]:
            matches += 1
    return matches

def aggregate_predictions(all_configs: list, all_errors: list = None, method: str = 'mode') -> dict:
    """
    Aggregate multiple predictions into a single ensemble prediction.
    
    Args:
        all_configs: List of configuration dictionaries from multiple runs
        method: Aggregation method ('mode', 'median', 'mean', 'weighted')
    
    Returns:
        Single aggregated configuration dictionary
    """
    if not all_configs:
        return {}
    
    # Get all parameter names
    param_names = list(all_configs[0].keys())
    aggregated = {}
    
    for param in param_names:
        values = [config[param] for config in all_configs]
        
        if method == 'mode':
            # Most frequent value
            from collections import Counter
            counter = Counter(values)
            aggregated[param] = counter.most_common(1)[0][0]
        elif method == 'median':
            # Median value
            aggregated[param] = sorted(values)[len(values) // 2]
        elif method == 'mean':
            # Round to nearest valid value (for discrete parameters)
            mean_val = sum(values) / len(values)
            # Find closest value to mean
            unique_vals = sorted(set(values))
            aggregated[param] = min(unique_vals, key=lambda x: abs(x - mean_val))
        elif method == 'weighted':
            # Weight by inverse of performance error (lower error = higher weight)
            # This requires error values, so we'll use mode as fallback
            from collections import Counter
            counter = Counter(values)
            aggregated[param] = counter.most_common(1)[0][0]
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
    
    return aggregated

def main():
    num_trials = 25  # Increased for more stable ensemble
    iterations_per_trial = 5000
    
    print("=" * 70)
    print("Multiple Autotuning Trials")
    print("=" * 70)
    print(f"Running {num_trials} trials with {iterations_per_trial} iterations each")
    print()
    
    # Get actual parameters for comparison
    system_profiler = SystemProfiler()
    actual_params = system_profiler.extract_cpu_parameters()
    print(f"Actual CPU parameters: {actual_params}")
    print()
    
    best_result = None
    best_matches = -1
    best_trial = 0
    all_results = []
    all_configs = []  # Store all configurations for ensemble
    all_errors = []  # Store all errors for weighted aggregation
    
    for trial in range(1, num_trials + 1):
        print(f"\n{'=' * 70}")
        print(f"TRIAL {trial}/{num_trials}")
        print(f"{'=' * 70}")
        
        # Run autotuning
        best_config, best_error, error_history, best_iteration, actual_params_check, match_history, search_info = run_maximized_autotuning(
            max_iterations=iterations_per_trial,
            use_multi_metric=True
        )
        
        # Count matches
        matches = count_matches(best_config, actual_params)
        match_pct = (matches / len(actual_params)) * 100
        
        result = {
            'trial': trial,
            'best_config': best_config,
            'best_error': best_error,
            'best_iteration': best_iteration,
            'matches': matches,
            'match_percent': match_pct,
            'search_info': search_info
        }
        all_results.append(result)
        all_configs.append(best_config)  # Store for ensemble
        all_errors.append(best_error)  # Store error for weighted aggregation
        
        print(f"\nTrial {trial} Results:")
        print(f"  Matches: {matches}/{len(actual_params)} ({match_pct:.1f}%)")
        print(f"  Best error: {best_error:.9f}")
        print(f"  Found at iteration: {best_iteration}")
        
        # Update best result
        if matches > best_matches:
            best_matches = matches
            best_result = result
            best_trial = trial
            print(f"  [NEW BEST RESULT!]")
        elif matches == best_matches and best_error < best_result['best_error']:
            best_result = result
            best_trial = trial
            print(f"  [NEW BEST RESULT (same matches, lower error)!]")
    
    # ENSEMBLE PREDICTIONS: Test all aggregation methods
    print("\n" + "=" * 70)
    print("ENSEMBLE PREDICTIONS (Testing All Aggregation Methods)")
    print("=" * 70)
    
    aggregation_methods = ['mode', 'median', 'mean', 'weighted']
    ensemble_results = {}
    
    for method in aggregation_methods:
        ensemble_config = aggregate_predictions(all_configs, all_errors=all_errors, method=method)
        ensemble_matches = count_matches(ensemble_config, actual_params)
        ensemble_match_pct = (ensemble_matches / len(actual_params)) * 100
        
        ensemble_results[method] = {
            'config': ensemble_config,
            'matches': ensemble_matches,
            'match_percent': ensemble_match_pct
        }
        
        print(f"\n{method.upper()} Aggregation ({num_trials} runs):")
        print(f"  Configuration: {ensemble_config}")
        print(f"  Matches: {ensemble_matches}/{len(actual_params)} ({ensemble_match_pct:.1f}%)")
    
    # Find best ensemble method
    best_ensemble_method = max(ensemble_results.items(), key=lambda x: (x[1]['matches'], -x[1]['match_percent']))
    best_ensemble_config = best_ensemble_method[1]['config']
    best_ensemble_matches = best_ensemble_method[1]['matches']
    best_ensemble_match_pct = best_ensemble_method[1]['match_percent']
    
    print("\n" + "=" * 70)
    print(f"BEST ENSEMBLE METHOD: {best_ensemble_method[0].upper()}")
    print("=" * 70)
    print(f"Configuration: {best_ensemble_config}")
    print(f"Matches: {best_ensemble_matches}/{len(actual_params)} ({best_ensemble_match_pct:.1f}%)")
    print()
    
    print("Parameter Comparison (Best Ensemble):")
    print("-" * 70)
    print(f"{'Parameter':<20} {'Ensemble Pred':<15} {'Actual':<15} {'Match':<10}")
    print("-" * 70)
    for param in actual_params:
        pred_val = best_ensemble_config[param]
        actual_val = actual_params[param]
        match = "YES" if pred_val == actual_val else "NO"
        print(f"{param:<20} {str(pred_val):<15} {str(actual_val):<15} {match:<10}")
    print("-" * 70)
    
    print("\nAll Ensemble Methods Comparison:")
    print("-" * 70)
    print(f"{'Method':<15} {'Matches':<10} {'Match %':<10}")
    print("-" * 70)
    for method, result in ensemble_results.items():
        print(f"{method:<15} {result['matches']}/{len(actual_params):<9} {result['match_percent']:<10.1f}")
    print("-" * 70)
    
    # INDIVIDUAL BEST RESULT (for comparison)
    print("\n" + "=" * 70)
    print("BEST INDIVIDUAL RESULT (for comparison)")
    print("=" * 70)
    print(f"Best result from Trial {best_trial}:")
    print(f"  Matches: {best_matches}/{len(actual_params)} ({best_result['match_percent']:.1f}%)")
    print(f"  Best error: {best_result['best_error']:.9f}")
    print(f"  Configuration: {best_result['best_config']}")
    print()
    
    print("Parameter Comparison (Best Individual Result):")
    print("-" * 70)
    print(f"{'Parameter':<20} {'Predicted':<15} {'Actual':<15} {'Match':<10}")
    print("-" * 70)
    for param in actual_params:
        pred_val = best_result['best_config'][param]
        actual_val = actual_params[param]
        match = "YES" if pred_val == actual_val else "NO"
        print(f"{param:<20} {str(pred_val):<15} {str(actual_val):<15} {match:<10}")
    print("-" * 70)
    
    print("\nAll Trials Summary:")
    print("-" * 70)
    print(f"{'Trial':<10} {'Matches':<10} {'Match %':<10} {'Best Error':<15} {'Found At':<10}")
    print("-" * 70)
    for r in all_results:
        print(f"{r['trial']:<10} {r['matches']}/{len(actual_params):<9} {r['match_percent']:<10.1f} {r['best_error']:<15.9f} {r['best_iteration']:<10}")
    print("-" * 70)
    
    # Save results
    results_file = Path(__file__).parent.parent / 'data' / 'results' / 'multiple_trials_results.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(v) for v in obj]
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        else:
            return str(obj)
    
    output = {
        'num_trials': num_trials,
        'iterations_per_trial': iterations_per_trial,
        'actual_parameters': actual_params,
        'ensemble_predictions': {
            method: {
                'config': result['config'],
                'matches': result['matches'],
                'match_percent': result['match_percent']
            }
            for method, result in ensemble_results.items()
        },
        'best_ensemble_method': best_ensemble_method[0],
        'best_ensemble_result': {
            'config': best_ensemble_config,
            'matches': best_ensemble_matches,
            'match_percent': best_ensemble_match_pct
        },
        'best_individual_result': convert_to_native(best_result),
        'all_results': convert_to_native(all_results)
    }
    
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == '__main__':
    main()
