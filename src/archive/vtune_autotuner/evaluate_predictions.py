"""
Evaluation and Comparison Module

Compares predicted CPU parameters with actual CPU parameters
to evaluate the framework's accuracy.
"""

import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from .cpu_info_extractor import CPUInfoExtractor
from .config import Config


def compare_predictions_vs_actual(
    predictions: Dict[str, float],
    actual: Dict[str, float]
) -> Dict[str, Dict]:
    """
    Compare predicted parameters with actual parameters.
    
    Args:
        predictions: Dictionary of predicted parameters
        actual: Dictionary of actual parameters
        
    Returns:
        Dictionary with comparison results including errors and accuracy
    """
    comparison = {}
    
    # Parameters to compare
    param_mapping = {
        "predicted_l1_cache_size_kb": "l1_cache_size_kb",
        "predicted_l2_cache_size_kb": "l2_cache_size_kb",
        "predicted_l3_cache_size_kb": "l3_cache_size_kb",
        "predicted_rob_size": "rob_size",
        "predicted_issue_width": "issue_width",
        "predicted_branch_predictor_accuracy": "branch_predictor_accuracy",
    }
    
    errors = []
    accuracies = []
    
    for pred_key, actual_key in param_mapping.items():
        if pred_key in predictions and actual_key in actual:
            pred_value = predictions[pred_key]
            actual_value = actual[actual_key]
            
            if actual_value is not None and actual_value != 0:
                # Calculate absolute error
                abs_error = abs(pred_value - actual_value)
                
                # Calculate relative error (percentage)
                rel_error = (abs_error / actual_value) * 100
                
                # Calculate accuracy (1 - normalized error)
                accuracy = max(0, 1 - (abs_error / max(actual_value, pred_value)))
                
                comparison[pred_key] = {
                    "predicted": pred_value,
                    "actual": actual_value,
                    "absolute_error": abs_error,
                    "relative_error_percent": rel_error,
                    "accuracy": accuracy * 100  # Convert to percentage
                }
                
                errors.append(rel_error)
                accuracies.append(accuracy * 100)
    
    # Overall statistics
    if errors:
        comparison["_summary"] = {
            "mean_relative_error": np.mean(errors),
            "median_relative_error": np.median(errors),
            "mean_accuracy": np.mean(accuracies),
            "median_accuracy": np.median(accuracies),
            "num_parameters_compared": len(errors)
        }
    
    return comparison


def print_comparison_report(comparison: Dict):
    """Print a formatted comparison report."""
    print("\n" + "="*80)
    print("PREDICTION vs ACTUAL COMPARISON REPORT")
    print("="*80)
    
    # Print individual parameter comparisons
    for key, value in comparison.items():
        if key.startswith("_"):
            continue
        
        param_name = key.replace("predicted_", "").replace("_", " ").title()
        print(f"\n{param_name}:")
        print(f"  Predicted:  {value['predicted']:.2f}")
        print(f"  Actual:     {value['actual']:.2f}")
        print(f"  Error:      {value['absolute_error']:.2f} ({value['relative_error_percent']:.2f}%)")
        print(f"  Accuracy:   {value['accuracy']:.2f}%")
    
    # Print summary
    if "_summary" in comparison:
        summary = comparison["_summary"]
        print("\n" + "-"*80)
        print("SUMMARY:")
        print(f"  Parameters Compared: {summary['num_parameters_compared']}")
        print(f"  Mean Relative Error: {summary['mean_relative_error']:.2f}%")
        print(f"  Median Relative Error: {summary['median_relative_error']:.2f}%")
        print(f"  Mean Accuracy: {summary['mean_accuracy']:.2f}%")
        print(f"  Median Accuracy: {summary['median_accuracy']:.2f}%")
        print("="*80)


def create_comparison_plot(comparison: Dict, output_file: str = "prediction_comparison.png"):
    """Create visualization comparing predictions vs actual values."""
    # Extract data for plotting
    params = []
    predicted = []
    actual = []
    errors = []
    
    for key, value in comparison.items():
        if key.startswith("_"):
            continue
        
        param_name = key.replace("predicted_", "").replace("_", " ").title()
        params.append(param_name)
        predicted.append(value['predicted'])
        actual.append(value['actual'])
        errors.append(value['relative_error_percent'])
    
    if not params:
        print("No data to plot")
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Top: Predicted vs Actual
    ax1 = axes[0]
    x = np.arange(len(params))
    width = 0.35
    
    ax1.bar(x - width/2, predicted, width, label='Predicted', alpha=0.8, color='skyblue')
    ax1.bar(x + width/2, actual, width, label='Actual', alpha=0.8, color='lightcoral')
    
    ax1.set_xlabel('Parameters', fontsize=12)
    ax1.set_ylabel('Values', fontsize=12)
    ax1.set_title('Predicted vs Actual CPU Parameters', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(params, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Bottom: Relative Error
    ax2 = axes[1]
    colors = ['green' if e < 20 else 'orange' if e < 50 else 'red' for e in errors]
    ax2.bar(params, errors, alpha=0.7, color=colors)
    ax2.axhline(y=20, color='green', linestyle='--', label='20% Error (Good)')
    ax2.axhline(y=50, color='orange', linestyle='--', label='50% Error (Moderate)')
    ax2.set_xlabel('Parameters', fontsize=12)
    ax2.set_ylabel('Relative Error (%)', fontsize=12)
    ax2.set_title('Prediction Error by Parameter', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(params, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"\nComparison plot saved: {output_file}")
    plt.close()


def save_comparison_results(comparison: Dict, output_file: str):
    """Save comparison results to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"Comparison results saved to {output_file}")


def evaluate_framework(
    predictions_file: Optional[str] = None,
    predictions: Optional[Dict] = None,
    output_dir: Optional[Path] = None
) -> Dict:
    """
    Complete evaluation: extract actual parameters, compare with predictions, generate report.
    
    Args:
        predictions_file: Path to JSON file with predictions
        predictions: Dictionary of predictions (if file not provided)
        output_dir: Directory to save results
        
    Returns:
        Comparison dictionary
    """
    if output_dir is None:
        output_dir = Config.RESULTS_DIR
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load predictions
    if predictions_file:
        with open(predictions_file, 'r') as f:
            data = json.load(f)
            predictions = data.get("predictions", data)
    elif predictions is None:
        raise ValueError("Either predictions_file or predictions must be provided")
    
    # Extract actual CPU parameters
    print("Extracting actual CPU parameters...")
    extractor = CPUInfoExtractor()
    actual = extractor.get_actual_parameters()
    
    # Save actual parameters
    actual_file = output_dir / "actual_cpu_parameters.json"
    extractor.save_to_file(str(actual_file))
    
    # Compare
    print("\nComparing predictions with actual parameters...")
    comparison = compare_predictions_vs_actual(predictions, actual)
    
    # Print report
    print_comparison_report(comparison)
    
    # Create visualization
    plot_file = output_dir / "prediction_comparison.png"
    create_comparison_plot(comparison, str(plot_file))
    
    # Save comparison
    comparison_file = output_dir / "prediction_comparison.json"
    save_comparison_results(comparison, str(comparison_file))
    
    return comparison


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        predictions_file = sys.argv[1]
        evaluate_framework(predictions_file=predictions_file)
    else:
        print("Usage: python evaluate_predictions.py <predictions_file.json>")
        print("\nOr use programmatically:")
        print("  from vtune_autotuner.evaluate_predictions import evaluate_framework")
        print("  comparison = evaluate_framework(predictions=my_predictions_dict)")
