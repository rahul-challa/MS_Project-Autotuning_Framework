# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │   CLI Interface   │  │   Standalone Scripts          │  │
│  │  (interfaces.cli) │  │  (scripts/*.py)               │  │
│  └──────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Autotuning Engine                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         MAB Autotuner (mab_autotuner.py)             │  │
│  │  • Standard UCB1 Algorithm                            │  │
│  │  • Maximized UCB1 (for parameter matching)           │  │
│  │  • Combined Error Calculation                        │  │
│  │  • Parameter Range Refinement                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Performance  │    │   VTune      │    │   System     │
│   Model      │    │  Profiler    │    │  Profiler    │
│              │    │              │    │              │
│ Estimates    │    │ Collects     │    │ Extracts     │
│ execution    │    │ ground truth │    │ actual CPU   │
│ time for     │    │ metrics      │    │ parameters   │
│ parameters   │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Benchmark Runner                             │  │
│  │  • Workload Execution                                │  │
│  │  • Ground Truth Collection                           │  │
│  │  • Multi-Collection Type Support                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Workload Registry                            │  │
│  │  • 15 Diverse Workloads                             │  │
│  │  • Collection Type Mapping                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Ground Truth Collection**
   ```
   Workloads → Benchmark Runner → VTune Profiler → Metrics → Ground Truth JSON
   ```

2. **System Profiling**
   ```
   System → System Profiler → Actual CPU Parameters → JSON
   ```

3. **Autotuning**
   ```
   Ground Truth + Actual Params → Performance Model → UCB1 Bandit → 
   Parameter Config → Error Calculation → Best Config → Results
   ```

## Key Components

### 1. MAB Autotuner (`mab_autotuner.py`)
- **Standard Autotuning**: Performance-focused optimization
- **Maximized Autotuning**: Parameter matching optimization (default)
- **UCB1 Algorithm**: Exploration-exploitation balance
- **Error Calculation**: Combined performance + parameter error

### 2. Performance Model (`performance_model.py`)
- Analytical model for execution time estimation
- Parameter impact modeling
- Multi-metric prediction
- Model calibration

### 3. VTune Profiler (`vtune_profiler.py`)
- VTune integration
- Multi-collection type support
- Comprehensive metric extraction
- Fallback to timing

### 4. Benchmark Runner (`benchmark_runner.py`)
- Workload execution
- Ground truth collection
- Multi-metric aggregation
- Timing fallback

### 5. Parameter Matching Optimizer (`parameter_matching_optimizer.py`)
- Combined error calculation
- Parameter matching error
- Model optimization
- Weight management

## Algorithm Flow

```
1. Initialize
   ├─ Load ground truth
   ├─ Extract actual parameters
   ├─ Refine parameter ranges (optional)
   └─ Calibrate performance model

2. UCB1 Loop (for each iteration)
   ├─ Select configuration (UCB1)
   ├─ Calculate combined error
   │  ├─ Performance error
   │  └─ Parameter matching error
   ├─ Update bandit statistics
   └─ Track best configuration

3. Return Results
   ├─ Best configuration
   ├─ Error history
   ├─ Match history
   └─ Actual parameters
```

## Error Calculation

### Combined Error
```
combined_error = α × normalized_perf_error + β × param_error
```

Where:
- `α` = performance_weight (default: 0.2)
- `β` = parameter_weight (default: 0.8)
- `normalized_perf_error` = performance error normalized to 0-1
- `param_error` = normalized parameter matching error

### Performance Error
```
perf_error = sqrt(Σ(weight_m × |Cwi_m - Swi,AP_m|²) for all metrics m)
```

### Parameter Error
```
param_error = sqrt(Σ(weight_p × |predicted_p - actual_p|² / actual_p²) for all params p)
```

## Configuration Space

- **Total Configurations**: 50,421 (7×7×7×7×3×7)
- **Refined Configurations**: ~9,375 (when using refined ranges)
- **Search Strategy**: UCB1 Multi-Armed Bandit
- **Convergence**: Typically 200-300 iterations for best result

## Extension Points

1. **New Workloads**: Add to `workload_registry.py`
2. **New Parameters**: Update `TUNABLE_PARAMETERS` and performance model
3. **New Metrics**: Extend `vtune_profiler.py` extraction
4. **New Algorithms**: Implement in `mab_autotuner.py`
5. **New Optimizers**: Add to `parameter_matching_optimizer.py`
