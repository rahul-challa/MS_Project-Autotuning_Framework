#!/usr/bin/env python3
"""
Sequential Parameter Tuning

This module implements a sequential optimization approach where parameters
are tuned one at a time, keeping other parameters fixed at their best values.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from .mab_autotuner import (
    TUNABLE_PARAMETERS,
    load_ground_truth,
    calculate_aggregate_error
)
from .enhanced_performance_model import EnhancedPerformanceModel
from .system_profiler import SystemProfiler


def run_sequential_autotuning(
    iterations_per_param: int = 5000,
    num_rounds: int = 1,
    use_multi_metric: bool = True,
    metric_weights: Optional[Dict[str, float]] = None,
    param_order: Optional[List[str]] = None
) -> Tuple[Dict[str, int], float, List[float], Dict[str, int], Dict[str, any]]:
    """
    Run sequential autotuning: optimize one parameter at a time.
    
    Strategy:
    1. Start with default/initial values for all parameters
    2. Optimize parameter 1 while keeping others fixed
    3. Fix parameter 1 at its best value, optimize parameter 2
    4. Continue for all parameters
    5. Repeat for multiple rounds
    
    Args:
        iterations_per_param: Number of iterations to spend on each parameter
        num_rounds: Number of rounds (each round tunes all parameters)
        use_multi_metric: Use all available metrics for better accuracy
        metric_weights: Weights for performance metrics
        param_order: Order in which to tune parameters (default: all parameters)
    
    Returns:
        Tuple of (best_config, best_error, error_history, actual_params, tuning_info)
    """
    # Load ground truth (should have all 15 workloads)
    ground_truth = load_ground_truth()
    print(f"Loaded ground truth for {len(ground_truth)} workloads")
    if len(ground_truth) < 15:
        print(f"Warning: Expected 15 workloads, found {len(ground_truth)}")
        print("Consider running collect-ground-truth to ensure all workloads are profiled")
    print("Using sequential parameter tuning (one parameter at a time)")
    print(f"Number of rounds: {num_rounds}")
    print("=" * 70)
    
    # Initialize performance model
    performance_model = EnhancedPerformanceModel()
    execution_times = [
        metrics.get('execution_time', 1.0) if isinstance(metrics, dict) else metrics
        for metrics in ground_truth.values()
    ]
    avg_ground_truth = np.mean(execution_times)
    performance_model.set_base_execution_time(avg_ground_truth)
    performance_model.calibrate_from_ground_truth(ground_truth)
    
    # Determine parameter order
    if param_order is None:
        param_order = list(TUNABLE_PARAMETERS.keys())
    
    print(f"\nParameter tuning order: {param_order}")
    print(f"Iterations per parameter: {iterations_per_param}")
    print(f"Number of rounds: {num_rounds}")
    print(f"Total iterations per round: {len(param_order) * iterations_per_param:,}")
    print(f"Total iterations across all rounds: {num_rounds * len(param_order) * iterations_per_param:,}")
    print()
    
    # Start with default/initial configuration
    # Use middle values as starting point
    current_config = {}
    for param_name, param_values in TUNABLE_PARAMETERS.items():
        # Use middle value as starting point
        current_config[param_name] = param_values[len(param_values) // 2]
    
    print("Initial configuration (using middle values):")
    for param, value in current_config.items():
        print(f"  {param}: {value}")
    print()
    
    # Track best error and configuration
    best_error = float('inf')
    best_config = current_config.copy()
    error_history = []
    
    # Track per-parameter results (across all rounds)
    param_results = {}
    round_results = []
    
    # Multiple rounds of sequential tuning
    for round_num in range(1, num_rounds + 1):
        print("\n" + "=" * 70)
        print(f"ROUND {round_num}/{num_rounds}")
        print("=" * 70)
        print(f"Starting configuration for round {round_num}:")
        for param, value in current_config.items():
            print(f"  {param}: {value}")
        print()
        
        # Sequential tuning: optimize one parameter at a time
        for param_idx, param_name in enumerate(param_order):
            print("=" * 70)
            print(f"TUNING PARAMETER {param_idx + 1}/{len(param_order)}: {param_name} (Round {round_num})")
            print("=" * 70)
            print(f"Possible values: {TUNABLE_PARAMETERS[param_name]}")
            print(f"Current value: {current_config[param_name]}")
            print(f"Other parameters fixed at: {[f'{k}={v}' for k, v in current_config.items() if k != param_name]}")
            print()
            
            # Get possible values for this parameter
            param_values = TUNABLE_PARAMETERS[param_name]
            
            # Track best value for this parameter
            param_best_value = current_config[param_name]
            param_best_error = float('inf')
            param_error_history = []
            
            # Test each value for this parameter
            for iteration in range(iterations_per_param):
                # Select a value to test (use UCB1-like exploration)
                if iteration < len(param_values):
                    # Initial exploration: try each value at least once
                    test_value = param_values[iteration]
                else:
                    # UCB1-like selection: balance exploration and exploitation
                    # For simplicity, use epsilon-greedy: 10% random, 90% best so far
                    if np.random.random() < 0.1:
                        # Explore: random value
                        test_value = np.random.choice(param_values)
                    else:
                        # Exploit: use best value found so far
                        test_value = param_best_value
                
                # Create test configuration with this parameter value
                test_config = current_config.copy()
                test_config[param_name] = test_value
                
                # Calculate performance error
                perf_error = calculate_aggregate_error(
                    test_config,
                    ground_truth,
                    performance_model,
                    use_multi_metric=use_multi_metric,
                    metric_weights=metric_weights
                )
                
                # Track error
                param_error_history.append(perf_error)
                error_history.append(perf_error)
                
                # Update best for this parameter
                if perf_error < param_best_error:
                    param_best_error = perf_error
                    param_best_value = test_value
                    
                    if iteration < 10 or (iteration + 1) % 500 == 0:
                        print(f"  Iteration {iteration+1}: NEW BEST for {param_name}")
                        print(f"    Value: {test_value}, Error: {perf_error:.6f}")
                
                # Update global best
                if perf_error < best_error:
                    best_error = perf_error
                    best_config = test_config.copy()
                    print(f"  Iteration {iteration+1}: NEW GLOBAL BEST")
                    print(f"    {param_name}={test_value}, Error: {perf_error:.6f}")
            
            # Update current configuration with best value for this parameter
            current_config[param_name] = param_best_value
            
            # Store results for this parameter (accumulate across rounds)
            if param_name not in param_results:
                param_results[param_name] = {
                    'best_value': param_best_value,
                    'best_error': param_best_error,
                    'rounds_tuned': 1,
                    'error_history': []
                }
            else:
                # Update if this round found a better value
                if param_best_error < param_results[param_name]['best_error']:
                    param_results[param_name]['best_value'] = param_best_value
                    param_results[param_name]['best_error'] = param_best_error
                param_results[param_name]['rounds_tuned'] += 1
            
            param_results[param_name]['error_history'].extend(param_error_history)
            
            print(f"\nBest value for {param_name} (Round {round_num}): {param_best_value} (error: {param_best_error:.6f})")
            print(f"Updated configuration: {current_config}")
            print()
        
        # Store round results
        round_best_error = best_error
        round_results.append({
            'round': round_num,
            'best_config': current_config.copy(),
            'best_error': round_best_error,
            'final_config': current_config.copy()
        })
        
        print(f"\nRound {round_num} complete!")
        print(f"Best error after round {round_num}: {round_best_error:.6f}")
        print(f"Best configuration: {current_config}")
        print()
    
    # Get actual parameters for validation
    print("=" * 70)
    print("VALIDATION: Comparing predicted vs actual parameters")
    print("=" * 70)
    system_profiler = SystemProfiler()
    actual_params = system_profiler.get_actual_parameters()
    print(f"Actual CPU parameters: {actual_params}")
    
    # Calculate matches
    matches = sum(1 for k in actual_params.keys() 
                 if best_config.get(k) == actual_params.get(k))
    match_pct = matches / len(actual_params) * 100
    
    print(f"\nFinal predicted parameters: {best_config}")
    print(f"Parameter matches: {matches}/{len(actual_params)} ({match_pct:.1f}%)")
    
    # Parameter-by-parameter comparison
    print("\nParameter-by-Parameter Comparison:")
    print("-" * 70)
    print(f"{'Parameter':<25} {'Predicted':<15} {'Actual':<15} {'Match':<10}")
    print("-" * 70)
    for param in param_order:
        pred_val = best_config.get(param, 'N/A')
        actual_val = actual_params.get(param, 'N/A')
        match = "YES" if pred_val == actual_val else "NO"
        print(f"{param:<25} {str(pred_val):<15} {str(actual_val):<15} {match:<10}")
    print("-" * 70)
    
    # Tuning info
    tuning_info = {
        'param_order': param_order,
        'iterations_per_param': iterations_per_param,
        'num_rounds': num_rounds,
        'total_iterations': num_rounds * len(param_order) * iterations_per_param,
        'param_results': param_results,
        'round_results': round_results,
        'final_matches': matches,
        'final_match_percent': match_pct,
        'num_workloads': len(ground_truth)
    }
    
    return best_config, best_error, error_history, actual_params, tuning_info
