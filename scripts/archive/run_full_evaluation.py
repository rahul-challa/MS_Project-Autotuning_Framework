#!/usr/bin/env python3
"""
Full Evaluation Script with All Parameters

This script runs a comprehensive evaluation:
1. Extracts actual CPU parameters (including Ryzen 5 2600 specs)
2. Discovers all VTune and EMON parameters
3. Runs autotuning for 100 iterations with all parameters
4. Generates convergence plot
5. Compares predictions vs actual
"""

import sys
import json
import time
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vtune_autotuner.cpu_info_extractor import CPUInfoExtractor
from vtune_autotuner.discovery import VTuneMetricsDiscovery
from vtune_autotuner.emon_runner import EMONRunner
from vtune_autotuner.config import Config
from vtune_autotuner.autotuner import (
    run_autotuning,
    create_convergence_plot,
    predict_cpu_parameters
)
from vtune_autotuner.evaluate_predictions import (
    compare_predictions_vs_actual,
    print_comparison_report,
    create_comparison_plot
)


def update_cpu_specs():
    """Update CPU info extractor with actual Ryzen 5 2600 specifications."""
    print("\n[Step 0/6] Updating CPU specifications...")
    
    extractor = CPUInfoExtractor()
    actual = extractor.get_actual_parameters()
    
    # Add Ryzen 5 2600 specific specs
    cpu_name = actual.get("cpu_name", "").upper()
    if "FAMILY 26" in cpu_name and "MODEL 36" in cpu_name:
        print("  Detected AMD Ryzen 5 2600 - applying specifications...")
        # These are the actual specs from web search
        actual["l1_data_cache_size_kb"] = 32  # Per core
        actual["l1_instruction_cache_size_kb"] = 64  # Per core
        actual["l2_cache_size_kb"] = 512  # Per core (3MB total for 6 cores)
        actual["l3_cache_size_kb"] = 16384  # 16MB total (shared)
        actual["l1_cache_size_kb"] = 96  # 32+64 per core
        actual["rob_size"] = 192
        actual["issue_width"] = 4
        actual["branch_predictor_accuracy"] = 0.95
        actual["l1_latency_cycles"] = 3
        actual["l2_latency_cycles"] = 12
        actual["l3_latency_cycles"] = 40
        
        # Save updated specs
        actual_file = Config.DATASETS_DIR / "actual_cpu_parameters.json"
        actual_file.parent.mkdir(parents=True, exist_ok=True)
        extractor.save_to_file(str(actual_file))
        print("  [OK] CPU specifications updated")
    
    return actual


def discover_all_parameters():
    """Discover all available VTune and EMON parameters."""
    print("\n[Step 1/6] Discovering all VTune and EMON parameters...")
    
    # Discover VTune parameters
    print("  Discovering VTune parameters...")
    try:
        discovery = VTuneMetricsDiscovery()
        tunable_params = discovery.get_tunable_parameters()
        analysis_types = discovery.get_analysis_types()
        
        print(f"    Analysis types: {analysis_types}")
        print(f"    Tunable parameters: {list(tunable_params.keys())}")
        
        # Expand to use all available parameters
        full_params = {
            "analysis_type": analysis_types,
            "sampling_interval": [1, 10, 100, 1000],
            "stack_size": [0, 1, 2, 4, 8],
            "enable_callstack": [False],  # Keep False to avoid errors
            "enable_user_mode": [True, False],
            "enable_kernel_mode": [True, False],
        }
        
        print(f"    Total parameter combinations: {_count_combinations(full_params)}")
        print("  [OK] VTune parameters discovered")
        
    except Exception as e:
        print(f"  [WARNING] VTune discovery failed: {e}")
        full_params = {
            "analysis_type": ["hotspots"],
            "sampling_interval": [10],
            "enable_callstack": [False],
        }
    
    # Discover EMON events
    print("  Discovering EMON events...")
    try:
        emon_runner = EMONRunner()
        events = emon_runner.get_available_events()
        print(f"    Available events: {len(events)}")
        for event in events[:10]:
            print(f"      - {event}")
        if len(events) > 10:
            print(f"      ... and {len(events) - 10} more")
        print("  [OK] EMON events discovered")
    except Exception as e:
        print(f"  [WARNING] EMON discovery failed: {e}")
    
    return full_params


def _count_combinations(params_dict):
    """Count total number of parameter combinations."""
    total = 1
    for values in params_dict.values():
        total *= len(values)
    return total


def run_full_autotuning(tunable_params, iterations=100):
    """Run full autotuning with all parameters."""
    print(f"\n[Step 2/6] Running autotuning ({iterations} iterations)...")
    print("="*80)
    
    try:
        best_config, best_error, error_history, collected_metrics = run_autotuning(
            max_iterations=iterations,
            tunable_params=tunable_params,
            use_emon=True
        )
        
        print("\n" + "="*80)
        print("Autotuning Complete!")
        print("="*80)
        print(f"Best configuration: {json.dumps(best_config, indent=2)}")
        print(f"Best error: {best_error:.9f}")
        print(f"Total iterations: {len(error_history)}")
        
        return best_config, best_error, error_history, collected_metrics
        
    except KeyboardInterrupt:
        print("\n\n[WARNING] Autotuning interrupted by user")
        raise
    except Exception as e:
        print(f"\n[ERROR] Autotuning failed: {e}")
        traceback.print_exc()
        raise


def create_convergence_visualization(error_history, best_error, best_config):
    """Create convergence plot."""
    print("\n[Step 3/6] Creating convergence visualization...")
    
    try:
        output_file = "mab_convergence_plot.png"
        create_convergence_plot(
            error_history,
            best_error,
            best_config,
            output_file=output_file
        )
        print(f"  [OK] Convergence plot saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"  [ERROR] Failed to create plot: {e}")
        traceback.print_exc()
        return None


def predict_parameters(collected_metrics):
    """Predict CPU parameters from collected metrics."""
    print("\n[Step 4/6] Predicting CPU parameters...")
    
    try:
        predictions = predict_cpu_parameters(collected_metrics)
        
        print("\nPredicted Parameters:")
        print("-" * 60)
        for key, value in predictions.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        return predictions
    except Exception as e:
        print(f"  [ERROR] Prediction failed: {e}")
        traceback.print_exc()
        return {}


def compare_and_evaluate(predictions, actual):
    """Compare predictions with actual parameters."""
    print("\n[Step 5/6] Comparing predictions with actual parameters...")
    
    try:
        comparison = compare_predictions_vs_actual(predictions, actual)
        
        # Print report
        print_comparison_report(comparison)
        
        # Create visualization
        plot_file = "prediction_comparison_full.png"
        create_comparison_plot(comparison, plot_file)
        print(f"\n  [OK] Comparison plot saved: {plot_file}")
        
        return comparison
    except Exception as e:
        print(f"  [ERROR] Comparison failed: {e}")
        traceback.print_exc()
        return {}


def save_results(best_config, best_error, error_history, predictions, actual, comparison):
    """Save all results to JSON file."""
    print("\n[Step 6/6] Saving results...")
    
    results = {
        "timestamp": time.time(),
        "best_configuration": best_config,
        "best_error": best_error,
        "error_history": error_history,
        "predictions": predictions,
        "actual_parameters": actual,
        "comparison": comparison,
        "iterations": len(error_history),
    }
    
    results_file = Config.RESULTS_DIR / f"full_evaluation_{int(time.time())}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"  [OK] Results saved to: {results_file}")
    return results_file


def main():
    """Main evaluation function."""
    print("="*80)
    print("FULL EVALUATION: All Parameters, 100 Iterations")
    print("="*80)
    
    start_time = time.time()
    
    try:
        # Step 0: Update CPU specs
        actual = update_cpu_specs()
        
        # Step 1: Discover all parameters
        tunable_params = discover_all_parameters()
        
        # Step 2: Run autotuning
        best_config, best_error, error_history, collected_metrics = run_full_autotuning(
            tunable_params,
            iterations=100
        )
        
        # Step 3: Create convergence plot
        convergence_plot = create_convergence_visualization(
            error_history,
            best_error,
            best_config
        )
        
        # Step 4: Predict parameters
        predictions = predict_parameters(collected_metrics)
        
        # Step 5: Compare and evaluate
        comparison = compare_and_evaluate(predictions, actual)
        
        # Step 6: Save results
        results_file = save_results(
            best_config,
            best_error,
            error_history,
            predictions,
            actual,
            comparison
        )
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("EVALUATION COMPLETE!")
        print("="*80)
        print(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print(f"Results file: {results_file}")
        if convergence_plot:
            print(f"Convergence plot: {convergence_plot}")
        
        if "_summary" in comparison:
            summary = comparison["_summary"]
            print(f"\nFramework Accuracy Summary:")
            print(f"  Mean Accuracy: {summary.get('mean_accuracy', 0):.2f}%")
            print(f"  Mean Relative Error: {summary.get('mean_relative_error', 0):.2f}%")
            print(f"  Parameters Compared: {summary.get('num_parameters_compared', 0)}")
        
    except KeyboardInterrupt:
        print("\n\n[WARNING] Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Evaluation failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
