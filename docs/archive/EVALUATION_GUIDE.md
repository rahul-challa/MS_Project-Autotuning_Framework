# Evaluation Guide - Predicting and Comparing CPU Parameters

This guide explains how to use the framework (legacy vtune_autotuner flow) to predict CPU parameters and compare them with actual values from your device.

> Note: The main, supported flow is now sequential autotuning via `python main.py autotune`. This document is archived for reference.

## Overview

The legacy flow can:
1. **Extract actual CPU parameters** from your system
2. **Predict CPU parameters** based on VTune/EMON metrics
3. **Compare predictions vs actual** to evaluate accuracy
4. **Generate detailed reports** and visualizations

## Quick Start (legacy commands)

### Method 1: One-Command Evaluation

```bash
# Install package
pip install -e .

# Run complete evaluation
vtune-autotune --evaluate --iterations 20
```

This single command will:
- Extract your actual CPU parameters
- Run autotuning (20 iterations)
- Predict CPU parameters
- Compare and generate accuracy report

### Method 2: Using Evaluation Script

```bash
python run_evaluation.py 20
```

### Method 3: Step-by-Step Python

```python
from vtune_autotuner import (
    run_autotuning,
    predict_cpu_parameters,
    load_vtune_discovery,
    CPUInfoExtractor,
    compare_predictions_vs_actual,
    Config
)
from vtune_autotuner.evaluate_predictions import (
    print_comparison_report,
    create_comparison_plot
)

# Step 1: Extract actual CPU parameters
extractor = CPUInfoExtractor()
actual = extractor.get_actual_parameters()
print("Actual CPU Parameters:", actual)

# Step 2: Run autotuning
best_config, best_error, error_history, collected_metrics = run_autotuning(
    max_iterations=20,
    use_emon=True
)

# Step 3: Predict parameters
discovery = load_vtune_discovery()
predictions = predict_cpu_parameters(
    best_config,
    discovery,
    Config.BENCHMARKS_DIR,
    collected_metrics=collected_metrics
)

# Step 4: Compare
comparison = compare_predictions_vs_actual(predictions, actual)
print_comparison_report(comparison)
create_comparison_plot(comparison, "comparison.png")
```

## Parameters Evaluated

The legacy comparison covers:

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| L1 Cache Size | Level 1 cache size | 32-64 KB per core |
| L2 Cache Size | Level 2 cache size | 256-512 KB per core |
| L3 Cache Size | Level 3 (LLC) cache size | 2-32 MB total |
| ROB Size | Reorder Buffer entries | 128-224 entries |
| Issue Width | Instructions per cycle | 2-6 instructions |
| Branch Predictor Accuracy | Branch prediction rate | 0.90-0.98 |

## Understanding Results

### Accuracy Metrics

- **Absolute Error**: `|predicted - actual|`
- **Relative Error**: `(|predicted - actual| / actual) * 100%`
- **Accuracy**: `(1 - normalized_error) * 100%`

### Interpretation

- **>80% Accuracy**: Excellent prediction
- **50-80% Accuracy**: Good prediction
- **<50% Accuracy**: Needs improvement

### Output Files

1. **prediction_comparison.png**
   - Bar chart: Predicted vs Actual values
   - Error chart: Relative error by parameter

2. **complete_evaluation_<timestamp>.json**
   - Full results including:
     - Best configuration
     - Predictions
     - Actual parameters
     - Comparison metrics
     - Accuracy statistics

3. **actual_cpu_parameters.json**
   - Extracted actual CPU parameters
   - CPU information

## Example Output

```
PREDICTION vs ACTUAL COMPARISON REPORT
================================================================================

L1 Cache Size Kb:
  Predicted:  32.00
  Actual:     32.00
  Error:      0.00 (0.00%)
  Accuracy:   100.00%

L2 Cache Size Kb:
  Predicted:  256.00
  Actual:     256.00
  Error:      0.00 (0.00%)
  Accuracy:   100.00%

L3 Cache Size Kb:
  Predicted:  8192.00
  Actual:     8192.00
  Error:      0.00 (0.00%)
  Accuracy:   100.00%

Rob Size:
  Predicted:  192.00
  Actual:     224.00
  Error:      32.00 (14.29%)
  Accuracy:   85.71%

Issue Width:
  Predicted:  4.00
  Actual:     4.00
  Error:      0.00 (0.00%)
  Accuracy:   100.00%

Branch Predictor Accuracy:
  Predicted:  0.95
  Actual:     0.96
  Error:      0.01 (1.04%)
  Accuracy:   98.96%

--------------------------------------------------------------------------------
SUMMARY:
  Parameters Compared: 6
  Mean Relative Error: 2.56%
  Median Relative Error: 0.00%
  Mean Accuracy: 97.44%
  Median Accuracy: 100.00%
================================================================================
```

## Tips for Better Accuracy

1. **More Iterations**: Run with 50-100 iterations for better metric collection
2. **Enable EMON**: Use EMON for additional hardware event metrics
3. **Multiple Workloads**: The framework uses multiple workloads for better coverage
4. **Verify Actual Parameters**: Check `actual_cpu_parameters.json` to ensure correct extraction

## Troubleshooting

### Actual Parameters Not Extracted

If some parameters show as `None`:
- Check CPU documentation
- Manually verify using CPU-Z or similar tools
- The framework uses heuristics for architecture-specific parameters

### Low Accuracy

If predictions have low accuracy:
- Run more iterations (50-100)
- Ensure EMON is working
- Check if VTune metrics are being collected properly
- Verify actual parameters are correct

### Missing Metrics

If certain metrics are missing:
- Check VTune version compatibility
- Verify CPU supports the events
- Some metrics may be CPU-specific

## Advanced Usage

### Custom Prediction Function

You can create custom prediction logic:

```python
from vtune_autotuner.autotuner import _predict_from_metrics

# Your custom metrics
my_metrics = {
    "CPI": 0.8,
    "LLC_MISS_RATE": 0.15,
    "BRANCH_PREDICT_RATE": 0.96
}

predictions = _predict_from_metrics(my_metrics, discovery)
```

### Batch Evaluation

Run evaluation on multiple systems:

```python
results = []
for system in systems:
    comparison = evaluate_framework(predictions=system_predictions[system])
    results.append({
        "system": system,
        "accuracy": comparison["_summary"]["mean_accuracy"]
    })
```

## Next Steps

After evaluation:
1. Review the accuracy report
2. Analyze which parameters are predicted well
3. Improve prediction heuristics if needed
4. Document results for your thesis/research
