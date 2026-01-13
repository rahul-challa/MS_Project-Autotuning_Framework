# Intel VTune Profiler Capabilities and Current Usage

## Overview
This document summarizes what Intel VTune Profiler supports and what our autotuning framework currently uses.

---

## VTune Collection Types (Supported by VTune)

VTune Profiler supports multiple collection types for different analysis purposes:

### Currently Implemented in Our Framework:
1. **`hotspots`** ✅ - Basic CPU hotspots analysis
   - Used by: All workloads
   - Purpose: Identify CPU bottlenecks

2. **`microarchitecture-exploration`** ✅ - Detailed microarchitecture analysis
   - Used by: w5_compute_intensive, w6_branch_intensive, w9_vector_ops
   - Purpose: Analyze CPU microarchitecture behavior
   - **Note**: Requires administrator privileges

3. **`memory-access`** ✅ - Memory access pattern analysis
   - Used by: w1_matrix_mult, w3_fft_calc, w4_memory_intensive, w7_cache_friendly, w13_hash_table, w14_matrix_decomp
   - Purpose: Analyze memory bottlenecks and cache behavior

4. **`threading`** ✅ - Threading and concurrency analysis
   - Defined but **NOT currently used** in any workload
   - Purpose: Analyze multi-threaded performance

### Additional VTune Collection Types (Not Currently Used):
- **`gpu-offload`** - GPU offload analysis (requires GPU)
- **`io`** - I/O performance analysis
- **`hpc-performance`** - HPC-specific analysis
- **`uarch-exploration`** - Alternative microarchitecture exploration
- **`memory-consumption`** - Memory usage analysis
- **`bandwidth`** - Memory bandwidth analysis

---

## VTune Metrics (What VTune Can Extract)

### Currently Extracted in Our Framework:
1. **`elapsed_time`** ✅ - Total wall-clock time
2. **`cpu_time`** ✅ - CPU time spent
3. **`execution_time`** ✅ - Primary metric (derived from elapsed_time or cpu_time)

### Additional Metrics VTune Can Provide (Not Currently Extracted):
- **CPU Utilization**: Percentage of CPU used
- **CPI (Cycles Per Instruction)**: Average cycles per instruction
- **IPC (Instructions Per Cycle)**: Average instructions per cycle
- **Cache Metrics**:
  - L1 cache hit/miss rates
  - L2 cache hit/miss rates
  - L3 cache hit/miss rates (if available)
  - Cache bandwidth
- **Memory Metrics**:
  - Memory bandwidth
  - Memory latency
  - Memory access patterns
- **Branch Prediction**:
  - Branch misprediction rate
  - Branch prediction accuracy
- **Pipeline Metrics**:
  - Pipeline stalls
  - Instruction retirement rate
  - Front-end vs back-end bottlenecks
- **Microarchitecture Events**:
  - CPU_CLK_UNHALTED (CPU cycles)
  - INST_RETIRED (Instructions retired)
  - MEM_LOAD_RETIRED (Memory loads)
  - BR_MISP_RETIRED (Branch mispredictions)
  - And many more hardware-specific events

---

## Workloads Supported by VTune

### Currently Implemented Workloads: **30 workloads** (15 original + 15 additional)

1. **w1_matrix_mult** - Matrix Multiplication
   - Collection types: `hotspots`, `memory-access`
   
2. **w2_bubble_sort** - Bubble Sort
   - Collection types: `hotspots`
   
3. **w3_fft_calc** - FFT Computation
   - Collection types: `hotspots`, `memory-access`
   
4. **w4_memory_intensive** - Memory Intensive (Poor Locality)
   - Collection types: `memory-access`, `hotspots`
   
5. **w5_compute_intensive** - Compute Intensive
   - Collection types: `hotspots`, `microarchitecture-exploration`
   
6. **w6_branch_intensive** - Branch Intensive
   - Collection types: `hotspots`, `microarchitecture-exploration`
   
7. **w7_cache_friendly** - Cache Friendly
   - Collection types: `memory-access`, `hotspots`
   
8. **w8_mixed_workload** - Mixed Workload
   - Collection types: `hotspots`
   
9. **w9_vector_ops** - Vector Operations
   - Collection types: `hotspots`, `microarchitecture-exploration`
   
10. **w10_nested_loops** - Nested Loops
    - Collection types: `hotspots`
    
11. **w11_string_processing** - String Processing
    - Collection types: `hotspots`
    
12. **w12_recursive** - Recursive Algorithm
    - Collection types: `hotspots`
    
13. **w13_hash_table** - Hash Table Operations
    - Collection types: `memory-access`, `hotspots`
    
14. **w14_matrix_decomp** - Matrix Decomposition
    - Collection types: `hotspots`, `memory-access`
    
15. **w15_pattern_matching** - Pattern Matching
    - Collection types: `hotspots`

#### Additional 15 Standard Workloads:

16. **w16_quicksort** - Quick Sort Algorithm
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

17. **w17_linpack** - LINPACK-like Dense Linear Algebra (HPC)
    - Collection types: `hotspots`, `microarchitecture-exploration`, `hpc-performance`, `bandwidth`

18. **w18_fft_2d** - 2D Fast Fourier Transform
    - Collection types: `hotspots`, `memory-access`, `microarchitecture-exploration`, `bandwidth`

19. **w19_monte_carlo** - Monte Carlo Simulation
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

20. **w20_sparse_matrix** - Sparse Matrix Operations
    - Collection types: `memory-access`, `hotspots`, `bandwidth`

21. **w21_tree_traversal** - Binary Tree Operations
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

22. **w22_graph_bfs** - Graph Breadth-First Search
    - Collection types: `memory-access`, `hotspots`, `microarchitecture-exploration`

23. **w23_image_processing** - Image Convolution and Filtering
    - Collection types: `hotspots`, `microarchitecture-exploration`, `memory-access`, `bandwidth`

24. **w24_cryptographic** - Cryptographic Hash Operations
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

25. **w25_database_query** - Database Query Simulation
    - Collection types: `memory-access`, `hotspots`, `microarchitecture-exploration`

26. **w26_nbody_simulation** - N-Body Physics Simulation (HPC)
    - Collection types: `hotspots`, `hpc-performance`, `microarchitecture-exploration`, `bandwidth`

27. **w27_compression** - Data Compression (LZ-like)
    - Collection types: `memory-access`, `hotspots`, `microarchitecture-exploration`

28. **w28_neural_network** - Neural Network Forward Pass
    - Collection types: `hotspots`, `microarchitecture-exploration`, `memory-access`, `bandwidth`

29. **w29_particle_filter** - Monte Carlo Particle Filter
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

30. **w30_ray_tracing** - Simple Ray Tracing
    - Collection types: `hotspots`, `microarchitecture-exploration`, `uarch-exploration`

### VTune Can Profile Any Application:
VTune is not limited to these workloads. It can profile:
- **Any executable** (C/C++, Python, Java, .NET, etc.)
- **Any script** (Python, shell scripts, etc.)
- **Containerized applications** (Docker containers)
- **Cloud applications**
- **HPC applications**
- **Multi-threaded applications**
- **GPU-accelerated applications**

---

## Parameters Currently Tuned by Our Framework

### Currently Tuned: **16 parameters** (6 original + 10 additional)

#### Original 6 Parameters:

1. **`rob_size`** (ReOrder Buffer Size)
   - Options: [64, 96, 128, 160, 192, 224, 256]
   - Total options: **7**

2. **`l1_cache_size`** (L1 Cache Size in KB)
   - Options: [32, 48, 64, 80, 96, 112, 128]
   - Total options: **7**

3. **`l2_cache_size`** (L2 Cache Size in KB)
   - Options: [128, 192, 256, 320, 384, 448, 512]
   - Total options: **7**

4. **`issue_width`** (Instruction Issue Width)
   - Options: [2, 3, 4, 5, 6, 7, 8]
   - Total options: **7**

5. **`l1_latency`** (L1 Cache Latency in cycles)
   - Options: [2, 3, 4]
   - Total options: **3**

6. **`l2_latency`** (L2 Cache Latency in cycles)
   - Options: [8, 10, 11, 12, 13, 14, 16]
   - Total options: **7**

#### Additional 10 Parameters (Now Implemented):

7. **`l3_cache_size`** (L3 Cache Size in KB)
   - Options: [1024, 1536, 2048, 3072, 4096, 6144, 8192]
   - Total options: **7**

8. **`l3_latency`** (L3 Cache Latency in cycles)
   - Options: [30, 35, 40, 45, 50, 55, 60]
   - Total options: **7**

9. **`memory_latency`** (Memory Latency in cycles)
   - Options: [100, 150, 200, 250, 300, 350, 400]
   - Total options: **7**

10. **`memory_bandwidth`** (Memory Bandwidth in GB/s)
    - Options: [10, 15, 20, 25, 30, 35, 40]
    - Total options: **7**

11. **`branch_predictor_size`** (Branch Predictor Entries)
    - Options: [512, 1024, 2048, 4096, 8192, 16384, 32768]
    - Total options: **7**

12. **`tlb_size`** (TLB Entries)
    - Options: [64, 128, 256, 512, 1024, 2048, 4096]
    - Total options: **7**

13. **`execution_units`** (Number of Execution Units)
    - Options: [2, 3, 4, 5, 6, 7, 8]
    - Total options: **7**

14. **`simd_width`** (SIMD Width in bits)
    - Options: [128, 256, 512]  # SSE, AVX2, AVX-512
    - Total options: **3**

15. **`prefetcher_lines`** (Prefetcher Lines per Request)
    - Options: [4, 8, 12, 16, 20, 24, 32]
    - Total options: **7**

16. **`smt_threads`** (SMT Threads per Core)
    - Options: [1, 2, 4, 8]
    - Total options: **4**

**Total Configuration Space**: 7 × 7 × 7 × 7 × 3 × 7 × 7 × 7 × 7 × 7 × 7 × 7 × 7 × 3 × 7 × 4 = **~1.1 × 10¹⁵ configurations** (extremely large search space)

---

## Summary Statistics

| Category | VTune Supports | Currently Used | Utilization |
|----------|---------------|----------------|-------------|
| **Collection Types** | ~10+ types | 4 types | ~40% |
| **Metrics** | 50+ metrics | 3 metrics | ~6% |
| **Workloads** | Unlimited | 30 workloads | N/A |
| **Tunable Parameters** | 10+ parameters | 16 parameters | ~100% |

---

## Recommendations for Improvement

1. **Extract More Metrics**: Use VTune's rich metric extraction capabilities
   - Cache hit/miss rates
   - CPI/IPC metrics
   - Branch misprediction rates
   - Memory bandwidth

2. **Use More Collection Types**: 
   - Add `threading` analysis for multi-threaded workloads
   - Use `bandwidth` for memory-intensive workloads
   - Use `uarch-exploration` for deeper microarchitecture analysis

3. **Add More Parameters**:
   - Include L3 cache parameters
   - Add memory latency parameters
   - Consider branch predictor parameters

4. **Expand Workload Diversity**:
   - Add multi-threaded workloads
   - Add GPU-accelerated workloads (if GPU available)
   - Add I/O-intensive workloads

---

## References

- Intel VTune Profiler Documentation: https://www.intel.com/content/www/us/en/docs/vtune-profiler/
- VTune Collection Types: https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2023-0/collection-types.html
- VTune Metrics Reference: https://www.intel.com/content/www/us/en/docs/vtune-profiler/user-guide/2023-0/metrics-reference.html
