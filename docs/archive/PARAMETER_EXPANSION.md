# Parameter and Workload Expansion

## Overview

The autotuning framework has been expanded to support **16 tunable parameters** (up from 6) and **30 workloads** (up from 15), providing comprehensive coverage of CPU microarchitecture characteristics.

## New Parameters Added

### 1. L3 Cache Parameters
- **`l3_cache_size`**: L3 cache size in KB (1024-8192 KB)
- **`l3_latency`**: L3 cache access latency in cycles (30-60 cycles)

### 2. Memory System Parameters
- **`memory_latency`**: Main memory access latency in cycles (100-400 cycles)
- **`memory_bandwidth`**: Memory bandwidth in GB/s (10-40 GB/s)

### 3. Branch Prediction
- **`branch_predictor_size`**: Number of branch predictor entries (512-32768)

### 4. Translation Lookaside Buffer (TLB)
- **`tlb_size`**: Number of TLB entries (64-4096)

### 5. Execution Resources
- **`execution_units`**: Number of execution units (2-8)
- **`simd_width`**: SIMD width in bits (128=SSE, 256=AVX2, 512=AVX-512)

### 6. Prefetching
- **`prefetcher_lines`**: Number of prefetcher lines per request (4-32)

### 7. Simultaneous Multi-Threading (SMT)
- **`smt_threads`**: Number of SMT threads per core (1, 2, 4, 8)

## New Workloads Added

### HPC Workloads
- **w17_linpack**: Dense linear algebra (LINPACK-like)
- **w26_nbody_simulation**: Physics simulation

### Algorithm Workloads
- **w16_quicksort**: Quick sort algorithm
- **w18_fft_2d**: 2D Fast Fourier Transform
- **w19_monte_carlo**: Monte Carlo simulation
- **w21_tree_traversal**: Binary tree operations
- **w22_graph_bfs**: Graph breadth-first search

### Data Processing Workloads
- **w20_sparse_matrix**: Sparse matrix operations
- **w23_image_processing**: Image convolution and filtering
- **w25_database_query**: Database join and aggregation
- **w27_compression**: Data compression (LZ-like)

### Specialized Workloads
- **w24_cryptographic**: Cryptographic hash operations
- **w28_neural_network**: Neural network forward pass
- **w29_particle_filter**: Monte Carlo particle filter
- **w30_ray_tracing**: Simple ray tracing

## Impact on Search Space

### Configuration Space Size
- **Original**: 50,421 configurations (6 parameters)
- **Expanded**: ~1.1 × 10¹⁵ configurations (16 parameters)

### Search Strategy
With such a large search space, the UCB1 Multi-Armed Bandit algorithm becomes even more critical for efficient exploration. The framework:
- Uses intelligent exploration-exploitation balance
- Focuses on high-impact parameters first
- Can be configured to prioritize certain parameter subsets

## Performance Model Updates

The enhanced performance model now accounts for:
- L3 cache hit/miss rates
- Memory bandwidth limitations
- Branch predictor accuracy
- TLB hit rates
- SIMD utilization
- Prefetcher effectiveness
- SMT thread contention

## Usage

All new parameters and workloads are automatically available when using the framework:

```python
from autotuner.mab_autotuner import run_maximized_autotuning

# All 16 parameters will be tuned
best_config, best_error, ... = run_maximized_autotuning(
    max_iterations=5000,
    use_multi_metric=True
)
```

## Recommendations

1. **For faster convergence**: Focus on the original 6 high-impact parameters first
2. **For maximum accuracy**: Use all 16 parameters with more iterations (10,000+)
3. **For specific workloads**: The framework automatically selects relevant parameters based on workload characteristics

## Backward Compatibility

The framework maintains backward compatibility:
- Existing code using 6 parameters continues to work
- Default parameter extraction includes all 16 parameters
- Performance model handles missing parameters gracefully
