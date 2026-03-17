# CPU Microarchitecture Autotuning Framework

An autotuning framework that uses **sequential parameter tuning** and (optionally) the **MacSim CPU simulator** to predict CPU microarchitecture parameters from **performance metrics only**. The included example run achieves **56.25% parameter matching accuracy** via multi-round refinement.

## Key Features

- **Sequential Tuning**: Optimizes one parameter at a time for maximum accuracy
- **Multi-Round Refinement**: Uses 5 rounds to iteratively refine parameter predictions
- **Correct Methodology**: Predicts CPU parameters using ONLY performance metrics (ground truth)
- **Multi-Metric Support**: Uses comprehensive MacSim simulation metrics for profiling
- **15 Diverse Workloads**: Comprehensive benchmark suite covering various CPU characteristics
- **CPU Simulation**: Uses MacSim CPU simulator for ground truth collection
- **Performance Model**: Analytical model estimates execution time for different CPU configurations
- **Validation**: Compares predicted vs actual parameters at the end (actual params NOT used during optimization)

## Methodology

The framework predicts CPU microarchitecture parameters using **ONLY performance metrics**:

1. **Collect Ground Truth**: Simulate workloads with MacSim to get performance metrics
2. **Sequential Optimization**: Tune one parameter at a time, keeping others fixed at their best values
3. **Multi-Round Refinement**: Repeat the sequential process for multiple rounds to refine predictions
4. **Validate**: Compare predicted parameters vs actual parameters (actual params NOT used during optimization)

**Important**: Actual CPU parameters are **NOT** used during optimization - they are only retrieved at the end for validation. This makes the framework suitable for predicting parameters of **unknown CPUs**.

## Quick Start

Get started with the CPU Microarchitecture Autotuning Framework in minutes.

### Prerequisites

- **Python 3.7+**
- **MacSim CPU Simulator** (optional; if absent, the framework falls back to direct timing)
- **NumPy, Matplotlib** (installed automatically with package)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd MS_Project-Autotuning_Framework

# Install (recommended)
python3 -m pip install -e .

# Or install dependencies only
python3 -m pip install -r requirements.txt
```

If your OS uses an “externally managed” Python environment (PEP 668), install in a virtual environment or via `pipx`.

### Step-by-Step Usage

#### Step 1: Collect Ground Truth

Collect performance metrics for all workloads:

```bash
autotune collect-ground-truth
```

This will:
- Profile all 15 workloads
- Collect execution times and performance metrics
- Save to `data/results/ground_truth.json`

#### Step 2: Run Sequential Autotuning

Run the sequential autotuning (default: 5 rounds × 5000 iterations per parameter):

```bash
# Default configuration (recommended for best accuracy)
autotune autotune

# Or simply (defaults to autotune)
autotune

# Custom configuration
autotune autotune --rounds 3 --iterations-per-param 3000
```

This will:
- Extract actual CPU parameters (for validation only)
- Run sequential parameter tuning (one parameter at a time)
- Find best parameter configuration
- Generate convergence plot
- Save results to `data/results/sequential_autotuning_results.json`

#### Step 3: View Results

Check the results:

```bash
# View JSON results
cat data/results/sequential_autotuning_results.json

# View convergence plot
# Open: data/results/sequential_autotuning_convergence.png
```

### Advanced Usage

#### Custom Rounds and Iterations

```bash
# More rounds for better refinement
autotune autotune --rounds 10 --iterations-per-param 5000

# Faster run with fewer iterations
autotune autotune --rounds 3 --iterations-per-param 2000
```

#### List Available Workloads

```bash
python scripts/list_workloads.py
```

## Packaging / Distribution

Build a wheel + sdist:

```bash
python3 -m pip install --upgrade build
python3 -m build
```

Install the built wheel (example):

```bash
python3 -m pip install dist/autotuning_framework-*.whl
autotune --help
```

## Report graphs (experiments)

The `report/` folder contains an experiment runner that executes multiple autotuning runs and generates figures:

```bash
python3 report/run_experiments.py
```

Outputs:
- Figures: `report/images/rounds_sweep.png`, `report/images/iters_sweep.png`
- Logs: `report/results/experiments.csv`, `report/results/experiments.jsonl`

### Expected Results

With default settings (5 rounds × 5000 iterations per parameter):
- **Parameter Matching**: ~56% (9/16 parameters)
- **Best Performance Error**: ~1.72 (lower is better)
- **Total Iterations**: 400,000 (5 rounds × 16 parameters × 5000)
- **Convergence**: Progressive improvement across rounds

### Troubleshooting

#### MacSim Not Found

Ensure MacSim is installed in the parent directory of the project folder. The framework will automatically locate it.

#### Low Accuracy

1. Increase rounds: `--rounds 10`
2. Increase iterations per parameter: `--iterations-per-param 10000`
3. Ensure ground truth has diverse execution times

#### Simulation Errors

If MacSim simulation fails, the framework will fall back to direct timing measurements.

### Programmatic Usage

```python
from autotuner.sequential_tuner import run_sequential_autotuning
from autotuner.benchmark_runner import BenchmarkRunner

# Collect ground truth
runner = BenchmarkRunner()
ground_truth = runner.collect_ground_truth()

# Run sequential autotuning
best_config, best_error, error_history, actual_params, tuning_info = \
    run_sequential_autotuning(
        iterations_per_param=5000,
        num_rounds=5,
        use_multi_metric=True
    )

print(f"Best configuration: {best_config}")
print(f"Parameter matches: {tuning_info['final_matches']}/{len(actual_params)}")
print(f"Match percentage: {tuning_info['final_match_percent']:.1f}%")
```

## Architecture (brief)

- **Interface layer**: CLI (`src/interfaces/cli.py`), utility scripts (`scripts/`)
- **Autotuning engine**: `sequential_tuner.py` (main), `mab_autotuner.py` (legacy), `enhanced_performance_model.py`
- **Profilers**: `vtune_profiler.py` for metrics (timing fallback), `system_profiler.py` for actual CPU parameters
- **Benchmarks**: `benchmark_runner.py` + `workload_registry.py` (15 workloads)
- **Data flow**:
  1) Collect ground truth (`python main.py collect-ground-truth`)
  2) Run sequential autotuning (`python main.py autotune`) → best config + match stats
  3) Results saved to `data/results/` (JSON + convergence plot)

## Project Structure

```
MS_Project-Autotuning_Framework/
├── src/                          # Source code
│   ├── autotuner/               # Core autotuning modules
│   │   ├── sequential_tuner.py  # Sequential parameter tuning (main)
│   │   ├── mab_autotuner.py     # Multi-Armed Bandit autotuner (legacy)
│   │   ├── enhanced_performance_model.py
│   │   ├── system_profiler.py
│   │   ├── benchmark_runner.py
│   │   ├── workload_registry.py
│   │   └── ...
│   ├── interfaces/              # User interfaces
│   │   └── cli.py               # Command-line interface
│   └── archive/                 # Archived legacy code
│       └── archive/              # Archived code (including legacy VTune integration)
│
├── scripts/                      # Utility scripts
│   ├── collect_ground_truth.py
│   ├── analyze_sequential_results.py
│   ├── list_workloads.py
│   └── archive/                  # Archived unused scripts
│
├── data/                         # Data files
│   ├── benchmarks/              # Benchmark workloads (generated at runtime)
│   │   └── archive/             # Archived unused workloads (w16-w30)
│   └── results/                  # Output results
│       ├── ground_truth.json     # Ground truth data (required)
│       ├── sequential_autotuning_results.json
│       ├── sequential_autotuning_convergence.png
│       └── archive/              # Archived old results
│
├── docs/                         # Documentation
│   └── archive/                  # Archived old documentation
│
├── logs/                         # Log files
│   ├── sequential_5rounds_output.txt  # Main run log
│   └── archive/                  # Archived old logs
│
├── configs/                      # Configuration files
│   └── archive/                  # Archived unused configs
│
├── main.py                       # Main entry point
├── README.md                     # Main documentation
├── pyproject.toml                # Package configuration (dependencies defined here)
└── LICENSE                        # License file
```

### Key Files

**Entry Points:**
- `main.py` - Main CLI entry point
- `src/interfaces/cli.py` - CLI implementation

**Core Modules:**
- `src/autotuner/sequential_tuner.py` - Sequential tuning approach (main)
- `src/autotuner/enhanced_performance_model.py` - Performance prediction model
- `src/autotuner/mab_autotuner.py` - Multi-Armed Bandit autotuner (legacy)

**Scripts:**
- `scripts/analyze_sequential_results.py` - Analyze tuning results
- `scripts/list_workloads.py` - List all available workloads
- `scripts/collect_ground_truth.py` - Standalone ground truth collection (CLI alternative)

## Tunable Parameters

The framework tunes 16 CPU microarchitecture parameters:

| Parameter                 | Options                                   | Description                     |
|---------------------------|-------------------------------------------|---------------------------------|
| **rob_size**              | 64, 96, 128, 160, 192, 224, 256           | Reorder Buffer size             |
| **l1_cache_size**         | 32, 48, 64, 80, 96, 112, 128 KB           | L1 cache size                   |
| **l2_cache_size**         | 128, 192, 256, 320, 384, 448, 512 KB      | L2 cache size                   |
| **issue_width**           | 2, 3, 4, 5, 6, 7, 8                       | Instruction issue width         |
| **l1_latency**            | 2, 3, 4 cycles                            | L1 cache access latency         |
| **l2_latency**            | 8, 10, 11, 12, 13, 14, 16 cycles          | L2 cache access latency         |
| **l3_cache_size**         | 512, 1024, 1536, 2048, 3072, 4096, 8192 KB| L3 cache size                   |
| **l3_latency**            | 30, 35, 40, 45, 50, 55, 60 cycles         | L3 cache access latency         |
| **memory_latency**        | 100, 150, 200, 250, 300 cycles            | Main memory access latency      |
| **memory_bandwidth**      | 10, 15, 20, 25, 30, 35, 40 GB/s           | Main memory bandwidth           |
| **branch_predictor_size** | 512, 1024, 2048, 4096, 8192, 16384, 32768 | Branch predictor entries        |
| **tlb_size**              | 64, 128, 256, 512, 1024, 2048, 4096       | Translation Lookaside Buffer size|
| **execution_units**       | 2, 3, 4, 5, 6, 7, 8                       | Number of execution units       |
| **simd_width**            | 128, 256, 512                             | SIMD instruction width          |
| **prefetcher_lines**      | 4, 8, 12, 16, 20, 24, 32                  | Cache prefetcher lines          |
| **smt_threads**           | 1, 2, 4, 8                                | Simultaneous Multi-threading threads |

**Total Configuration Space**: 490,930,300 configurations

## Workloads

The framework includes **15 diverse workloads**:

1. **w1_matrix_mult** - Matrix multiplication (FPU, memory bandwidth)
2. **w2_bubble_sort** - Bubble sort (branch prediction, cache)
3. **w3_fft_calc** - FFT computation (complex math, memory patterns)
4. **w4_memory_intensive** - Strided memory access (cache misses)
5. **w5_compute_intensive** - Heavy math operations (FPU throughput)
6. **w6_branch_intensive** - Heavy branching (branch prediction)
7. **w7_cache_friendly** - Sequential access (cache hits)
8. **w8_mixed_workload** - Combined patterns
9. **w9_vector_ops** - SIMD-friendly operations
10. **w10_nested_loops** - Deeply nested loops (instruction scheduling)
11. **w11_string_processing** - String manipulation (integer ALU)
12. **w12_recursive** - Recursive algorithms (call stack)
13. **w13_hash_table** - Hash operations (memory access patterns)
14. **w14_matrix_decomp** - Matrix decomposition (numerical algorithms)
15. **w15_pattern_matching** - String search (branch, memory)

## Algorithm: Sequential Tuning

The framework uses a **sequential tuning** approach:

1. **Initialization**: Start with a default configuration.
2. **Parameter Iteration**: For each parameter, iterate through its possible values while keeping all other parameters fixed at their current best values.
3. **Best Value Selection**: Select the value that yields the lowest performance error for the current parameter.
4. **Configuration Update**: Update the overall configuration with the best value found for the current parameter.
5. **Multi-Round Refinement**: Repeat steps 2-4 for multiple rounds (default: 5 rounds) to iteratively refine the entire configuration.

This systematic approach ensures focused optimization for each parameter and allows for refinement over multiple passes.

## Output

The autotuning process generates:

1. **Convergence Plot** (`data/results/sequential_autotuning_convergence.png`)
   - Error convergence over iterations
   - Shows improvement across rounds

2. **Results JSON** (`data/results/sequential_autotuning_results.json`)
   - Best configuration
   - Actual parameters
   - Error history
   - Parameter matches and match percentage
   - Round-by-round results

3. **Ground Truth** (`data/results/ground_truth.json`)
   - Execution times for all workloads
   - Comprehensive metrics (when MacSim available)

## Configuration Options

### Rounds and Iterations

More rounds and iterations = better refinement = higher accuracy:

```bash
# Default (recommended for best results)
python main.py autotune --rounds 5 --iterations-per-param 5000

# Maximum accuracy (may take longer)
python main.py autotune --rounds 10 --iterations-per-param 10000

# Faster run for testing
python main.py autotune --rounds 3 --iterations-per-param 2000
```

## MacSim CPU Simulator Integration

The framework uses MacSim CPU simulator for comprehensive performance profiling:

### Simulation Features

- **Configurable CPU Parameters** - Simulate different microarchitecture configurations
- **Performance Metrics** - Extract execution time, CPI, IPC, cache metrics
- **Trace-based Simulation** - Supports trace-driven simulation for accurate results

### Fallback Mode

If MacSim simulation is not available, the framework automatically falls back to direct timing measurements:
- Works on Windows, Linux, macOS
- No special privileges required
- Still achieves high accuracy (56.25% parameter matching)

## How It Works

1. **Ground Truth Collection**: Simulates workloads with MacSim (or timing fallback) to get performance metrics
2. **Sequential Optimization**: Tunes one parameter at a time, keeping others fixed at their best values
3. **Multi-Round Refinement**: Repeats the sequential process for multiple rounds to refine predictions
4. **System Profiling**: Extracts actual CPU parameters from the system (for validation only)
5. **Validation**: Compares predicted vs actual parameters to calculate accuracy
6. **Results**: Returns best configuration with match percentage and convergence plot

## Performance Metrics

- **Parameter Matching**: 56.25% (9/16 parameters)
- **Configuration Space**: 490,930,300 total configurations
- **Workloads**: 15 diverse benchmarks
- **Tuning Strategy**: 5 rounds × 5000 iterations per parameter = 400,000 total iterations
- **Best Performance Error**: ~1.72 (lower is better)

## Evaluation

1) **Collect ground truth (if not present)**  
```bash
python main.py collect-ground-truth
```

2) **Run evaluation (sequential autotuning)**  
```bash
python main.py autotune
```
- Default: 5 rounds × 5000 iterations per parameter (400,000 total iterations)
- Uses performance metrics only; actual parameters are fetched at the end for validation

3) **View results**  
- JSON: `data/results/sequential_autotuning_results.json`  
  - `best_config`, `best_error`, `final_matches`, `final_match_percent`, `error_history`
- Plot: `data/results/sequential_autotuning_convergence.png`

4) **Interpretation**  
- Higher `final_match_percent` = better parameter prediction accuracy  
- Lower `best_error` = closer performance match to ground truth  
- Inspect per-parameter matches in the JSON for detailed comparison

5) **Improve accuracy**  
- Increase rounds: `--rounds 8` (more refinement passes)  
- Increase iterations per parameter: `--iterations-per-param 8000`  
- Ensure ground truth covers all 15 workloads

## Troubleshooting

### MacSim Not Available

The framework automatically falls back to direct timing if MacSim is unavailable:
- Works on Windows, Linux, macOS
- No special privileges required
- Still achieves high accuracy

### Low Match Percentage

If parameter matching is low:
1. Increase rounds: `--rounds 10` or more
2. Increase iterations per parameter: `--iterations-per-param 10000`
3. Check ground truth diversity (should have varied execution times)

### MacSim Installation

MacSim should be installed in the parent directory of the project folder:
- Expected path: `../macsim/bin/macsim`
- The framework will automatically locate MacSim if installed correctly

## Project Requirements

- **Objective**: Find parameter assignment AP that minimizes performance prediction error
- **Error Metric**: Performance prediction error (actual parameters NOT used during optimization)
- **Algorithm**: Sequential Tuning with Multi-Round Refinement
- **Profiler**: MacSim CPU Simulator (with timing fallback)
- **Workloads**: 15 diverse benchmarks
- **Accuracy Target**: Maximize parameter matching percentage (currently 56.25%)

## Contributing

We welcome contributions! Here's how to get started:

### Code Structure

- **`src/autotuner/`**: Core autotuning framework
  - `sequential_tuner.py`: Main sequential autotuning logic
  - `mab_autotuner.py`: Multi-Armed Bandit autotuning (legacy)
  - `enhanced_performance_model.py`: Performance estimation model
  - `macsim_profiler.py`: MacSim integration
  - `benchmark_runner.py`: Benchmark execution
  - `workload_registry.py`: Workload definitions

- **`src/interfaces/`**: User interfaces
  - `cli.py`: Command-line interface

- **`scripts/`**: Utility scripts
  - `collect_ground_truth.py`: Standalone ground truth collection
  - `analyze_sequential_results.py`: Results analysis
  - `list_workloads.py`: List available workloads

### Adding New Workloads

Add workloads to `src/autotuner/workload_registry.py`:

```python
'w16_new_workload': {
    'name': 'New Workload',
    'description': 'Description of what it tests',
    'code': '''
# Python code here
import time
# ...
''',
    'collection_types': ['hotspots', 'memory-access']
}
```

### Adding New Parameters

Update `TUNABLE_PARAMETERS` in `src/autotuner/mab_autotuner.py`:

```python
TUNABLE_PARAMETERS = {
    # ... existing parameters
    'new_param': [value1, value2, value3]
}
```

Update the performance model in `src/autotuner/enhanced_performance_model.py` to account for the new parameter.

### Testing

Run the test suite:

```bash
# Collect ground truth
python main.py collect-ground-truth

# Run autotuning with reduced iterations for testing
python main.py autotune --rounds 1 --iterations-per-param 100
```

### Code Style

- Follow PEP 8
- Use type hints
- Document all functions and classes
- Keep functions focused and modular

## License

See LICENSE file for details.

## Author

Viswanadh Rahul Challa

## Acknowledgments

- MacSim CPU Simulator for performance simulation capabilities
- Sequential tuning approach for systematic optimization

## References

- MacSim CPU Simulator: https://github.com/gthparch/macsim
