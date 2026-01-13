#!/usr/bin/env python3
"""
Analyze Sequential Tuning Results

Compare predicted parameters vs actual parameters and provide detailed analysis.
"""

import json
from pathlib import Path

def analyze_results(results_file):
    """Analyze and compare predicted vs actual parameters."""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    predicted = data['best_config']
    actual = data['actual_parameters']
    matches = data['matches']
    match_percent = data['match_percent']
    best_error = data['best_error']
    
    print("=" * 80)
    print("SEQUENTIAL TUNING RESULTS ANALYSIS")
    print("=" * 80)
    print(f"\nOverall Accuracy: {matches}/{len(actual)} parameters ({match_percent:.2f}%)")
    print(f"Best Performance Error: {best_error:.9f}")
    print()
    
    # Detailed comparison
    print("=" * 80)
    print("DETAILED PARAMETER COMPARISON")
    print("=" * 80)
    print(f"{'Parameter':<25} {'Predicted':<15} {'Actual':<15} {'Match':<10} {'Error %':<15}")
    print("-" * 80)
    
    correct_params = []
    incorrect_params = []
    close_params = []  # Within 20% of actual value
    
    for param in sorted(actual.keys()):
        pred_val = predicted.get(param, 'N/A')
        actual_val = actual.get(param, 'N/A')
        
        if pred_val == actual_val:
            match = "YES"
            correct_params.append(param)
            error_pct = "0.0%"
        else:
            match = "NO"
            incorrect_params.append(param)
            
            # Calculate percentage error
            if isinstance(pred_val, (int, float)) and isinstance(actual_val, (int, float)) and actual_val != 0:
                error_pct = abs((pred_val - actual_val) / actual_val) * 100
                if error_pct <= 20:
                    close_params.append(param)
                error_pct = f"{error_pct:.1f}%"
            else:
                error_pct = "N/A"
        
        print(f"{param:<25} {str(pred_val):<15} {str(actual_val):<15} {match:<10} {error_pct:<15}")
    
    print("-" * 80)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"[CORRECT] Correctly Predicted: {len(correct_params)}/{len(actual)} ({len(correct_params)/len(actual)*100:.1f}%)")
    print(f"  Parameters: {', '.join(correct_params)}")
    print()
    print(f"[INCORRECT] Incorrectly Predicted: {len(incorrect_params)}/{len(actual)} ({len(incorrect_params)/len(actual)*100:.1f}%)")
    print(f"  Parameters: {', '.join(incorrect_params)}")
    print()
    
    if close_params:
        close_but_wrong = [p for p in close_params if p not in correct_params]
        if close_but_wrong:
            print(f"≈ Close Predictions (within 20%): {len(close_but_wrong)} parameters")
            print(f"  Parameters: {', '.join(close_but_wrong)}")
            print()
    
    # Calculate average error for incorrect parameters
    errors = []
    for param in incorrect_params:
        pred_val = predicted.get(param)
        actual_val = actual.get(param)
        if isinstance(pred_val, (int, float)) and isinstance(actual_val, (int, float)) and actual_val != 0:
            error_pct = abs((pred_val - actual_val) / actual_val) * 100
            errors.append(error_pct)
    
    if errors:
        avg_error = sum(errors) / len(errors)
        max_error = max(errors)
        min_error = min(errors)
        print(f"Error Analysis (for incorrect parameters):")
        print(f"  Average error: {avg_error:.1f}%")
        print(f"  Minimum error: {min_error:.1f}%")
        print(f"  Maximum error: {max_error:.1f}%")
        print()
    
    # Parameter categories
    print("=" * 80)
    print("PARAMETER CATEGORY ANALYSIS")
    print("=" * 80)
    
    categories = {
        'Cache Parameters': ['l1_cache_size', 'l2_cache_size', 'l3_cache_size', 'l1_latency', 'l2_latency', 'l3_latency'],
        'Memory Parameters': ['memory_latency', 'memory_bandwidth'],
        'Pipeline Parameters': ['rob_size', 'issue_width', 'execution_units'],
        'Branch & TLB': ['branch_predictor_size', 'tlb_size'],
        'SIMD & Prefetching': ['simd_width', 'prefetcher_lines'],
        'SMT': ['smt_threads']
    }
    
    for category, params in categories.items():
        category_params = [p for p in params if p in actual]
        category_correct = [p for p in category_params if p in correct_params]
        category_accuracy = len(category_correct) / len(category_params) * 100 if category_params else 0
        
        print(f"\n{category}:")
        print(f"  Accuracy: {len(category_correct)}/{len(category_params)} ({category_accuracy:.1f}%)")
        print(f"  Correct: {', '.join(category_correct) if category_correct else 'None'}")
        incorrect_in_category = [p for p in category_params if p in incorrect_params]
        if incorrect_in_category:
            print(f"  Incorrect: {', '.join(incorrect_in_category)}")
    
    # Tuning info
    if 'tuning_info' in data:
        tuning_info = data['tuning_info']
        print("\n" + "=" * 80)
        print("TUNING INFORMATION")
        print("=" * 80)
        print(f"Total iterations: {tuning_info.get('total_iterations', 'N/A'):,}")
        print(f"Iterations per parameter: {tuning_info.get('iterations_per_param', 'N/A'):,}")
        print(f"Number of rounds: {tuning_info.get('num_rounds', 'N/A')}")
        print(f"Number of workloads: {tuning_info.get('num_workloads', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    if match_percent >= 50:
        print(f"[GOOD] Good accuracy: {match_percent:.1f}% parameters correctly predicted")
    elif match_percent >= 30:
        print(f"[MODERATE] Moderate accuracy: {match_percent:.1f}% parameters correctly predicted")
    else:
        print(f"[LOW] Low accuracy: {match_percent:.1f}% parameters correctly predicted")
    
    print(f"\nThe sequential tuning approach with 5 rounds and 5000 iterations per parameter")
    print(f"achieved {match_percent:.1f}% accuracy, correctly predicting {matches} out of {len(actual)} parameters.")
    
    if len(close_params) > len(correct_params):
        print(f"\nAdditionally, {len(close_params) - len(correct_params)} parameters were within 20% of actual values,")
        print(f"suggesting the model is learning the approximate ranges even when not exact.")

if __name__ == '__main__':
    results_file = Path(__file__).parent.parent / 'data' / 'results' / 'sequential_autotuning_results.json'
    if results_file.exists():
        analyze_results(results_file)
    else:
        print(f"Results file not found: {results_file}")
