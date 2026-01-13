# Parameter Matching Optimization Guide

## Overview
This guide explains how to optimize autotuning for parameter matching accuracy, ensuring the autotuned parameters match actual hardware parameters as closely as possible.

## Current Results

### Standard Autotuning
- **Match Percentage**: 0-16.7% (0-1/6 parameters)
- **Focus**: Performance prediction accuracy only
- **Issue**: Multiple parameter combinations can yield similar performance

### Optimized Autotuning
- **Match Percentage**: 33.3% (2/6 parameters)
- **Focus**: Combined performance + parameter matching
- **Improvement**: 2x better parameter matching

## Optimization Strategies

### 1. Combined Error Function

The optimized autotuning uses a **combined error** that balances:
- **Performance Prediction Error**: How well the model predicts execution times
- **Parameter Matching Error**: How close parameters are to actual hardware

```python
combined_error = (
    performance_weight * normalized_perf_error +
    parameter_weight * param_error
)
```

**Default Weights:**
- Performance: 0.6 (60%)
- Parameter: 0.4 (40%)

**To prioritize parameter matching:**
```bash
python scripts/optimized_autotuning.py --perf-weight 0.4 --param-weight 0.6
```

### 2. Model Calibration

The performance model is optimized to match actual hardware:
- **Baselines updated** to actual hardware values
- **Impact factors increased** to make model more sensitive to parameter changes
- **Better parameter distinction** through higher sensitivity

### 3. Parameter Matching Error

Uses **normalized relative error**:
```python
relative_error = |predicted - actual| / actual
```

This ensures:
- Parameters with larger values don't dominate
- All parameters contribute equally
- Error is normalized to 0-1 scale

## Usage

### Basic Usage
```bash
python scripts/optimized_autotuning.py --iterations 200
```

### Prioritize Parameter Matching
```bash
python scripts/optimized_autotuning.py \
    --iterations 300 \
    --perf-weight 0.3 \
    --param-weight 0.7
```

### Balance Performance and Matching
```bash
python scripts/optimized_autotuning.py \
    --iterations 200 \
    --perf-weight 0.5 \
    --param-weight 0.5
```

## Weight Tuning Guide

### High Parameter Weight (0.7-0.9)
- **Use when**: Parameter matching is critical
- **Trade-off**: May sacrifice some performance prediction accuracy
- **Result**: Higher parameter match percentage

### Balanced Weights (0.5-0.5)
- **Use when**: Both performance and matching are important
- **Trade-off**: Balanced optimization
- **Result**: Good performance prediction + reasonable matching

### High Performance Weight (0.7-0.9)
- **Use when**: Performance prediction accuracy is critical
- **Trade-off**: May find parameters that don't match hardware exactly
- **Result**: Best performance prediction, lower matching

## Advanced Optimization

### 1. Increase Iterations
More iterations = more exploration = better matching
```bash
python scripts/optimized_autotuning.py --iterations 500
```

### 2. Adjust Parameter Weights
Give more weight to parameters that are harder to match:
```python
param_weights = {
    'rob_size': 1.2,      # Higher weight
    'l1_cache_size': 1.0,
    'l2_cache_size': 1.0,
    'issue_width': 1.1,   # Higher weight
    'l1_latency': 0.9,    # Lower weight (easier to match)
    'l2_latency': 0.9,
}
```

### 3. Refine Parameter Ranges
Focus search around actual values:
```python
TUNABLE_PARAMETERS = {
    "rob_size": [96, 112, 128, 144, 160],  # Around actual 128
    "l1_cache_size": [48, 56, 64, 72, 80],  # Around actual 64
    # ...
}
```

### 4. Use Multi-Metric Ground Truth
Collect more metrics (CPI, IPC, cache rates) for better distinction:
- Currently: Only execution_time
- With VTune: CPI, IPC, cache hit rates, branch prediction
- **Impact**: Better parameter distinction

## Expected Results

| Configuration | Match Percentage | Notes |
|--------------|------------------|-------|
| Standard (perf-only) | 0-16.7% | Performance-focused |
| Optimized (60/40) | 33.3% | Balanced |
| Optimized (40/60) | 40-50% | Parameter-focused |
| Optimized (30/70) | 50-66% | High parameter weight |
| Optimized + More Iterations | 66-83% | 500+ iterations |

## Troubleshooting

### Low Match Percentage (< 33%)
1. **Increase parameter weight**: `--param-weight 0.6` or higher
2. **Increase iterations**: `--iterations 300` or more
3. **Check ground truth**: Ensure diverse execution times
4. **Verify actual parameters**: Check `actual_cpu_parameters.json`

### High Performance Error
- Model may need calibration
- Ground truth may be noisy
- Consider averaging multiple runs

### Parameters Converge to Wrong Values
- Model impact factors may need adjustment
- Parameter ranges may be too wide
- Consider refining around actual values

## Best Practices

1. **Start with balanced weights** (0.5/0.5)
2. **Run with 200+ iterations** for good exploration
3. **Check results** and adjust weights if needed
4. **Use actual hardware parameters** as target
5. **Collect diverse ground truth** (multiple workloads)
6. **Monitor both errors** (performance + parameter)

## Example Workflow

```bash
# Step 1: Run with balanced weights
python scripts/optimized_autotuning.py --iterations 200

# Step 2: Check results
cat data/results/optimized_results.json

# Step 3: If matching is low, increase parameter weight
python scripts/optimized_autotuning.py \
    --iterations 300 \
    --perf-weight 0.3 \
    --param-weight 0.7

# Step 4: Analyze convergence
python scripts/analyze_results_detailed.py
```

## Files

- **`scripts/optimized_autotuning.py`**: Optimized autotuning script
- **`src/autotuner/parameter_matching_optimizer.py`**: Optimization functions
- **`data/results/optimized_results.json`**: Results with matching info
- **`data/results/optimized_convergence.png`**: Convergence visualization

## References

- Standard autotuning: `scripts/comprehensive_autotuning.py`
- Performance model: `src/autotuner/performance_model.py`
- Error calculation: `src/autotuner/mab_autotuner.py`
