#!/usr/bin/env python3
"""
Run Complete Evaluation

This script runs the autotuning framework, extracts actual CPU parameters,
and compares predictions with actual values to evaluate framework accuracy.
"""

import sys
import json
import time
from pathlib import Path

try:
    # Try importing as installed package
    from vtune_autotuner import (
        run_autotuning,
        create_convergence_plot,
        predict_cpu_parameters,
        load_vtune_discovery,
        Config,
        CPUInfoExtractor,
        compare_predictions_vs_actual
    )
    from vtune_autotuner.evaluate_predictions import (
        evaluate_framework,
        print_comparison_report,
        create_comparison_plot
    )
except ImportError:
    # Fallback to direct import for development
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from src.vtune_autotuner import (
        run_autotuning,
        create_convergence_plot,
        predict_cpu_parameters,
        load_vtune_discovery,
        Config
    )
    from src.vtune_autotuner.cpu_info_extractor import CPUInfoExtractor
    from src.vtune_autotuner.evaluate_predictions import (
        evaluate_framework,
        compare_predictions_vs_actual,
        print_comparison_report,
        create_comparison_plot
    )


def main():
    """Run complete evaluation pipeline."""
    print("="*80)
    print("VTune/EMON Autotuning Framework - Complete Evaluation")
    print("="*80)
    
    # Step 1: Extract actual CPU parameters
    print("\n[Step 1/5] Extracting actual CPU parameters...")
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
    
    # Step 2: Run autotuning
    print("\n[Step 2/5] Running autotuning...")
    print("This may take a while (10-50 iterations recommended for testing)...")
    
    max_iterations = 10  # Start with fewer iterations for testing
    if len(sys.argv) > 1:
        try:
            max_iterations = int(sys.argv[1])
        except:
            pass
    
    print(f"Running {max_iterations} iterations...")
    
    best_config, best_error, error_history, collected_metrics = run_autotuning(
        max_iterations=max_iterations,
        use_emon=True
    )
    
    # Step 3: Create convergence plot
    print("\n[Step 3/5] Creating convergence visualization...")
    create_convergence_plot(error_history, best_error, best_config)
    
    # Step 4: Predict CPU parameters
    print("\n[Step 4/5] Predicting CPU parameters...")
    discovery = load_vtune_discovery()
    predictions = predict_cpu_parameters(
        best_config,
        discovery,
        Config.BENCHMARKS_DIR,
        collected_metrics=collected_metrics
    )
    
    # Step 5: Compare and evaluate
    print("\n[Step 5/5] Comparing predictions with actual parameters...")
    comparison = compare_predictions_vs_actual(predictions, actual)
    
    # Print detailed report
    print_comparison_report(comparison)
    
    # Create comparison visualization
    comparison_plot = "prediction_comparison.png"
    create_comparison_plot(comparison, comparison_plot)
    
    # Save all results
    results = {
        "best_config": best_config,
        "best_error": best_error,
        "error_history": error_history,
        "predictions": predictions,
        "actual_parameters": actual,
        "comparison": comparison,
        "timestamp": time.time()
    }
    
    results_file = Config.RESULTS_DIR / f"complete_evaluation_{int(time.time())}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {results_file}")
    print(f"Convergence plot: vtune_convergence.png")
    print(f"Comparison plot: {comparison_plot}")
    
    if "_summary" in comparison:
        summary = comparison["_summary"]
        print(f"\nFramework Accuracy Summary:")
        print(f"  Mean Accuracy: {summary['mean_accuracy']:.2f}%")
        print(f"  Mean Relative Error: {summary['mean_relative_error']:.2f}%")
        print(f"  Parameters Compared: {summary['num_parameters_compared']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nEvaluation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
