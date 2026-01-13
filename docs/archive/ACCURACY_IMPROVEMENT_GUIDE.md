# Accuracy Improvement Guide

## Current Status
- **Current Match**: 66.67% (4/6 parameters)
- **Matching**: ROB Size (128), L1 Cache (64 KB), L2 Cache (256 KB), Issue Width (4)
- **Different**: L1 Latency (2 vs 3), L2 Latency (16 vs 12)

## Root Cause Analysis

### Why Accuracy is Limited

1. **Performance Model Limitations**
   - Model uses fixed impact factors that may not match real hardware
   - Linear scaling assumptions may not hold
   - Parameter interactions not fully modeled

2. **Ground Truth Quality**
   - VTune profiling failing → using simple timing (less accurate)
   - All workloads getting same execution time (1.0s) due to fallback
   - No actual performance variation captured

3. **Parameter Space**
   - Limited granularity (only 3 options per parameter)
   - May not include actual hardware values
   - Issue width and latencies have limited options

4. **Error Metric**
   - Equal weight to all workloads
   - Doesn't account for workload importance
   - May be optimizing for wrong objective

## Improvement Strategies (Ranked by Impact)

### 🔥 HIGH IMPACT - Quick Wins

#### 1. **Fix VTune Integration** (Expected: +10-15% accuracy)
**Problem**: VTune can't profile Python scripts on Windows
**Solution**: 
- Create compiled C/C++ benchmarks instead of Python scripts
- Use proper Python executable (not Windows Store launcher)
- Run as Administrator for full VTune features

**Implementation**:
```python
# Create C++ benchmark executables
# Compile with: g++ -O2 benchmark.cpp -o benchmark.exe
# Then profile: vtune -collect hotspots -- benchmark.exe
```

#### 2. **More Iterations** (Expected: +5-10% accuracy)
**Current**: 100-200 iterations
**Recommended**: 300-500 iterations
**Why**: More exploration = better chance to find optimal config

**Command**:
```bash
python scripts/comprehensive_autotuning.py --iterations 500
```

#### 3. **Workload Weighting** (Expected: +5-8% accuracy)
**Status**: ✅ Already implemented
**Usage**: Already active in improved_autotuning.py
**Next Step**: Fine-tune weights based on workload importance

### 🎯 MEDIUM IMPACT - Model Improvements

#### 4. **Refine Parameter Space** (Expected: +8-12% accuracy)
**Problem**: Current ranges may not include optimal values
**Solution**: Add more granular options, especially around actual hardware values

**Implementation**:
```python
TUNABLE_PARAMETERS = {
    "rob_size": [96, 128, 160, 192, 224, 256],  # More options
    "l1_cache_size": [48, 64, 80, 96, 112, 128],
    "l2_cache_size": [192, 256, 320, 384, 448, 512],
    "issue_width": [3, 4, 5, 6, 7, 8],  # Include actual value 4
    "l1_latency": [2, 3, 4],  # Keep current
    "l2_latency": [10, 12, 14, 16],  # Include actual value 12
}
```

#### 5. **Model Calibration** (Expected: +10-15% accuracy)
**Problem**: Model impact factors are generic
**Solution**: Calibrate using collected autotuning data

**Implementation**:
- Use collected (config, error) pairs to fit model parameters
- Apply regression to adjust impact factors
- Validate on held-out data

#### 6. **Non-Linear Modeling** (Expected: +5-10% accuracy)
**Problem**: Current model is mostly linear
**Solution**: Add non-linear effects (diminishing returns, thresholds)

**Example**:
```python
# Cache size effect with diminishing returns
if cache_size > baseline:
    benefit = 1 - (1 - impact_factor) ** (cache_size / baseline)
```

### 🚀 ADVANCED - Long-term Improvements

#### 7. **Machine Learning Model** (Expected: +15-25% accuracy)
**Replace analytical model with ML model trained on collected data**

**Implementation**:
```python
from sklearn.ensemble import RandomForestRegressor

class MLPerformanceModel:
    def train(self, configs, execution_times):
        # Train on collected autotuning data
        self.model.fit(configs, execution_times)
    
    def estimate(self, config):
        return self.model.predict([config])[0]
```

#### 8. **Multi-Objective Optimization**
**Optimize for multiple metrics**: execution time, accuracy, parameter similarity

#### 9. **Hardware-Specific Models**
**Detect CPU family and use architecture-specific models**

## Immediate Action Plan

### Step 1: Quick Test (5 minutes)
Run with more iterations to see if it helps:
```bash
python scripts/comprehensive_autotuning.py --iterations 500
```

### Step 2: Refine Parameter Space (30 minutes)
Update `TUNABLE_PARAMETERS` to include more granular options around actual hardware values:
- Add values closer to actual hardware (e.g., 12 for L2 latency)
- Add intermediate values (e.g., 96, 160 for ROB size)

### Step 3: Improve Ground Truth (1-2 hours)
**Option A**: Fix VTune integration
- Create C++ benchmark executables
- Use proper Python path

**Option B**: Improve fallback timing
- Run multiple times and average
- Use more accurate timing methods
- Add warm-up runs

### Step 4: Model Calibration (2-3 hours)
- Collect data from multiple autotuning runs
- Use regression to calibrate model parameters
- Validate calibration

## Expected Improvements

| Strategy | Expected Improvement | Effort | Priority |
|----------|---------------------|--------|----------|
| More iterations (500) | +5-10% | Low | 🔥 High |
| Refine parameter space | +8-12% | Medium | 🔥 High |
| Fix VTune integration | +10-15% | Medium | 🔥 High |
| Model calibration | +10-15% | Medium | 🎯 Medium |
| ML-based model | +15-25% | High | 🚀 Advanced |

## Testing Improvements

After implementing each improvement, test with:
```bash
python scripts/comprehensive_autotuning.py --iterations 200
python scripts/improved_autotuning.py --iterations 300
```

Compare match percentages to track improvement.

## Key Insight

The **biggest issue** is likely the **ground truth quality**. Since VTune profiling is failing and all workloads get the same execution time (1.0s), the model can't learn meaningful differences. **Fixing VTune integration should have the biggest impact**.

## Next Steps

1. ✅ **More workloads** - Done (15 workloads)
2. ✅ **Weighted error** - Implemented
3. 🔄 **More iterations** - Test with 500 iterations
4. 🔄 **Refine parameter space** - Add more granular options
5. 🔄 **Fix VTune** - Create compiled benchmarks or fix Python path
6. 🔄 **Model calibration** - Use collected data to improve model
