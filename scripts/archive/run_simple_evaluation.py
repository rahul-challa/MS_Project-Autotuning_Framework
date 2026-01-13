#!/usr/bin/env python3
"""
Simplified Evaluation Script

This script runs a simplified evaluation that works even when VTune has limitations.
It uses direct timing measurements and makes predictions based on available data.
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vtune_autotuner.cpu_info_extractor import CPUInfoExtractor
from vtune_autotuner.benchmarks import BenchmarkWorkloads
from vtune_autotuner.config import Config
from vtune_autotuner.evaluate_predictions import (
    compare_predictions_vs_actual,
    print_comparison_report,
    create_comparison_plot
)


def run_simple_evaluation():
    """Run simplified evaluation using direct timing."""
    print("="*80)
    print("Simplified CPU Parameter Evaluation")
    print("="*80)
    
    # Step 1: Extract actual CPU parameters
    print("\n[Step 1/3] Extracting actual CPU parameters...")
    extractor = CPUInfoExtractor()
    actual = extractor.get_actual_parameters()
    
    print("\nActual CPU Parameters:")
    print("-" * 60)
    for key, value in actual.items():
        if value is not None:
            print(f"  {key}: {value}")
    
    # Save actual parameters
    actual_file = Config.DATASETS_DIR / "actual_cpu_parameters.json"
    actual_file.parent.mkdir(parents=True, exist_ok=True)
    extractor.save_to_file(str(actual_file))
    
    # Step 2: Run benchmarks and collect basic metrics
    print("\n[Step 2/3] Running benchmarks to collect performance metrics...")
    workloads = BenchmarkWorkloads()
    
    # Run each workload and collect timing
    benchmark_metrics = {}
    for workload_id in workloads.get_workload_ids():
        print(f"  Running {workload_id}...")
        times = []
        for _ in range(3):  # Run 3 times for average
            start = time.perf_counter()
            workloads.run_workload(workload_id)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        benchmark_metrics[workload_id] = {
            "avg_time": avg_time,
            "min_time": min(times),
            "max_time": max(times),
        }
        print(f"    Average time: {avg_time:.6f}s")
    
    # Step 3: Predict parameters based on benchmark performance
    print("\n[Step 3/3] Predicting CPU parameters...")
    
    # Calculate derived metrics from benchmark performance
    # Use matrix multiplication as baseline (cache-friendly)
    baseline_time = benchmark_metrics["w1_matrix_mult"]["avg_time"]
    
    # Use bubble sort for cache-unfriendly comparison
    cache_unfriendly_time = benchmark_metrics["w2_bubble_sort"]["avg_time"]
    
    # Calculate cache efficiency ratio
    cache_efficiency = baseline_time / cache_unfriendly_time if cache_unfriendly_time > 0 else 1.0
    
    # Predict based on performance characteristics
    predictions = {}
    
    # Predict cache sizes based on performance ratios
    if cache_efficiency > 0.3:  # Good cache efficiency
        predictions["predicted_l3_cache_size_kb"] = 16384.0  # Large cache
    elif cache_efficiency > 0.2:
        predictions["predicted_l3_cache_size_kb"] = 8192.0
    elif cache_efficiency > 0.1:
        predictions["predicted_l3_cache_size_kb"] = 4096.0
    else:
        predictions["predicted_l3_cache_size_kb"] = 2048.0
    
    predictions["predicted_l2_cache_size_kb"] = predictions["predicted_l3_cache_size_kb"] / 32
    predictions["predicted_l1_cache_size_kb"] = 32.0  # Typical per core
    
    # Predict ROB and issue width based on overall performance
    # Faster execution suggests better out-of-order execution
    if baseline_time < 0.05:
        predictions["predicted_rob_size"] = 224
        predictions["predicted_issue_width"] = 6
    elif baseline_time < 0.1:
        predictions["predicted_rob_size"] = 192
        predictions["predicted_issue_width"] = 4
    else:
        predictions["predicted_rob_size"] = 160
        predictions["predicted_issue_width"] = 4
    
    # Branch predictor (use default, would need branch-intensive workload analysis)
    predictions["predicted_branch_predictor_accuracy"] = 0.95
    
    print("\nPredicted Parameters:")
    print("-" * 60)
    for key, value in predictions.items():
        print(f"  {key}: {value}")
    
    # Step 4: Compare
    print("\n[Step 4/4] Comparing predictions with actual...")
    comparison = compare_predictions_vs_actual(predictions, actual)
    
    # Print report
    print_comparison_report(comparison)
    
    # Create visualization
    plot_file = "prediction_comparison.png"
    create_comparison_plot(comparison, plot_file)
    
    # Save results
    results = {
        "predictions": predictions,
        "actual_parameters": actual,
        "comparison": comparison,
        "benchmark_metrics": benchmark_metrics,
        "timestamp": time.time()
    }
    
    results_file = Config.RESULTS_DIR / f"simple_evaluation_{int(time.time())}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print("Evaluation Complete!")
    print("="*80)
    print(f"Results saved to: {results_file}")
    print(f"Comparison plot: {plot_file}")
    
    if "_summary" in comparison:
        summary = comparison["_summary"]
        print(f"\nFramework Accuracy Summary:")
        print(f"  Mean Accuracy: {summary['mean_accuracy']:.2f}%")
        print(f"  Mean Relative Error: {summary['mean_relative_error']:.2f}%")
        print(f"  Parameters Compared: {summary['num_parameters_compared']}")


if __name__ == "__main__":
    try:
        run_simple_evaluation()
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nEvaluation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
