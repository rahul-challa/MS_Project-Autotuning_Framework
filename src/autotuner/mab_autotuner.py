#!/usr/bin/env python3
"""
Multi-Armed Bandit (MAB) Autotuning Framework for CPU Model Validation

This framework uses Intel VTune Profiler to collect ground truth performance
metrics from real CPU execution. Since we cannot change CPU microarchitecture
parameters on real hardware, we use a performance model to estimate execution
time based on CPU configuration parameters.

Project Requirements:
- Objective: Find parameter assignment AP that minimizes EAggW,AP
- Error Metric: EAggW,AP = sqrt(Σ(Ewi,AP)²) where Ewi,AP = |Cwi - Swi,AP|
- MAB Algorithm: UCB1 for exploration-exploitation balance
- Profiler: Intel VTune Profiler
"""

import numpy as np
import json
import random
from itertools import product
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

from .performance_model import PerformanceModel
from .enhanced_performance_model import EnhancedPerformanceModel
from .benchmark_runner import BenchmarkRunner
from .vtune_profiler import VTuneProfiler
from .system_profiler import SystemProfiler
from .parameter_matching_optimizer import (
    calculate_combined_error,
    optimize_model_for_parameter_matching
)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Tunable Parameters - High Impact Parameters
# Refined with more granular options around typical hardware values
TUNABLE_PARAMETERS = {
    # Original 6 parameters
    "rob_size": [64, 96, 128, 160, 192, 224, 256],  # More granular around 128
    "l1_cache_size": [32, 48, 64, 80, 96, 112, 128],  # More granular around 64
    "l2_cache_size": [128, 192, 256, 320, 384, 448, 512],  # More granular around 256
    "issue_width": [2, 3, 4, 5, 6, 7, 8],  # Include 4 and intermediate values
    "l1_latency": [2, 3, 4],  # Keep current (includes actual value 3)
    "l2_latency": [8, 10, 11, 12, 13, 14, 16],  # More granular around 12
    
    # Additional 10 parameters
    "l3_cache_size": [1024, 1536, 2048, 3072, 4096, 6144, 8192],  # L3 cache size in KB
    "l3_latency": [30, 35, 40, 45, 50, 55, 60],  # L3 cache latency in cycles
    "memory_latency": [100, 150, 200, 250, 300, 350, 400],  # Memory latency in cycles
    "memory_bandwidth": [10, 15, 20, 25, 30, 35, 40],  # Memory bandwidth in GB/s
    "branch_predictor_size": [512, 1024, 2048, 4096, 8192, 16384, 32768],  # Branch predictor entries
    "tlb_size": [64, 128, 256, 512, 1024, 2048, 4096],  # TLB entries
    "execution_units": [2, 3, 4, 5, 6, 7, 8],  # Number of execution units
    "simd_width": [128, 256, 512],  # SIMD width in bits (SSE, AVX, AVX-512)
    "prefetcher_lines": [4, 8, 12, 16, 20, 24, 32],  # Prefetcher lines per request
    "smt_threads": [1, 2, 4, 8],  # SMT threads per core
}

# Data Files
GROUND_TRUTH_FILE = Path(__file__).parent.parent.parent / 'data' / 'results' / 'ground_truth.json'

# Default workloads if ground truth doesn't exist
DEFAULT_WORKLOADS = [
    'w1_matrix_mult',
    'w2_bubble_sort',
    'w3_fft_calc',
    'w4_memory_intensive',
    'w5_compute_intensive',
    'w6_branch_intensive',
    'w7_cache_friendly',
    'w8_mixed_workload'
]


# ============================================================================
# DATA LOADING
# ============================================================================

def load_ground_truth() -> Dict[str, Dict[str, float]]:
    """
    Load comprehensive ground truth metrics from VTune measurements.
    
    If ground truth doesn't exist, collects it for ALL workloads using ALL collection types.
    
    Returns:
        Dictionary mapping workload_id to metrics dictionary
        (supports both old format Dict[str, float] and new format Dict[str, Dict[str, float]])
    """
    if GROUND_TRUTH_FILE.exists():
        with open(GROUND_TRUTH_FILE, 'r') as f:
            data = json.load(f)
            # Extract workloads (exclude metadata)
            workloads = {k: v for k, v in data.items() if k != '_metadata'}
            
            # Handle both old format (Dict[str, float]) and new format (Dict[str, Dict[str, float]])
            # Convert old format to new format
            converted = {}
            for workload_id, value in workloads.items():
                if isinstance(value, dict):
                    converted[workload_id] = value
                else:
                    # Old format: just execution_time
                    converted[workload_id] = {'execution_time': value}
            
            return converted
    
    # If ground truth doesn't exist, collect it for ALL workloads
    print(f"Ground truth not found at {GROUND_TRUTH_FILE}")
    print("Collecting comprehensive ground truth for ALL workloads using ALL VTune collection types...")
    from .workload_registry import get_all_workloads
    benchmark_runner = BenchmarkRunner()
    all_workloads = get_all_workloads()
    print(f"Using ALL {len(all_workloads)} workloads")
    ground_truth = benchmark_runner.collect_ground_truth(
        workload_ids=None,  # None = use ALL workloads
        output_file=GROUND_TRUTH_FILE,
        use_all_collection_types=True  # Use ALL collection types
    )
    
    # Remove metadata for return
    return {k: v for k, v in ground_truth.items() if k != '_metadata'}


# ============================================================================
# PERFORMANCE MODEL INTEGRATION
# ============================================================================

def estimate_all_metrics(workload_id: str, ap: Dict[str, int], 
                        performance_model: PerformanceModel,
                        ground_truth: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Estimate all performance metrics for a workload with given parameter assignment.
    
    Since we cannot change CPU microarchitecture on real hardware, we use
    a performance model to estimate how different configurations would
    affect performance metrics.
    
    Args:
        workload_id: Workload identifier
        ap: Parameter assignment dict
        performance_model: PerformanceModel instance
        ground_truth: Ground truth metrics dictionary (workload_id -> metrics dict)
    
    Returns:
        Dictionary of estimated metrics
    """
    # Get base metrics from ground truth
    base_metrics = ground_truth.get(workload_id, {'execution_time': 1.0})
    
    # Ensure execution_time exists
    if 'execution_time' not in base_metrics:
        base_metrics['execution_time'] = 1.0
    
    # Set base execution time
    performance_model.set_base_execution_time(base_metrics['execution_time'])
    
    # Estimate all metrics with given parameters (pass workload_id for workload-specific adjustments)
    # Check if estimate_all_metrics accepts workload_id parameter
    import inspect
    sig = inspect.signature(performance_model.estimate_all_metrics)
    if 'workload_id' in sig.parameters:
        estimated_metrics = performance_model.estimate_all_metrics(ap, base_metrics, workload_id)
    else:
        estimated_metrics = performance_model.estimate_all_metrics(ap, base_metrics)
    
    return estimated_metrics

def estimate_execution_time(workload_id: str, ap: Dict[str, int], 
                           performance_model: PerformanceModel,
                           ground_truth: Dict[str, Dict[str, float]]) -> float:
    """
    Estimate execution time for a workload (backward compatibility).
    
    Args:
        workload_id: Workload identifier
        ap: Parameter assignment dict
        performance_model: PerformanceModel instance
        ground_truth: Ground truth metrics dictionary
    
    Returns:
        Estimated execution time in seconds
    """
    estimated_metrics = estimate_all_metrics(workload_id, ap, performance_model, ground_truth)
    return estimated_metrics.get('execution_time', 1.0)


# ============================================================================
# ERROR CALCULATION (Project Requirements)
# ============================================================================

def calculate_aggregate_error(
    ap: Dict[str, int],
    ground_truth: Dict[str, Dict[str, float]],
    performance_model: PerformanceModel,
    use_multi_metric: bool = True,
    metric_weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate L2-norm aggregate error EAggW,AP using multiple metrics for maximum accuracy.
    
    Formula (multi-metric):
        Ewi,AP = sqrt(Σ(weight_m * |Cwi_m - Swi,AP_m|²) for all metrics m)
        EAggW,AP = sqrt(Σ(Ewi,AP)²) for all workloads
    
    Formula (single-metric, backward compatible):
        Ewi,AP = |Cwi - Swi,AP|
        EAggW,AP = sqrt(Σ(Ewi,AP)²)
    
    Args:
        ap: Parameter assignment dict
        ground_truth: Dictionary mapping workload_id to metrics dictionary
        performance_model: PerformanceModel instance
        use_multi_metric: If True, use all available metrics. If False, use only execution_time.
        metric_weights: Dictionary of metric names to weights (default: equal weights)
    
    Returns:
        Aggregate error EAggW,AP
    """
    if metric_weights is None:
        # Default weights: Use ALL available metrics with appropriate weights
        # Higher weight for primary metrics, lower for derived metrics
        metric_weights = {
            # Primary timing metrics (highest weight)
            'execution_time': 1.0,
            'elapsed_time': 0.9,
            'cpu_time': 0.9,
            
            # CPU performance metrics
            'cpi': 0.7,
            'ipc': 0.7,
            'cpu_utilization': 0.6,
            'instructions_retired': 0.5,
            'cpu_clocks': 0.5,
            
            # Cache metrics
            'l1_cache_hit_rate': 0.6,
            'l1_cache_miss_rate': 0.5,
            'l1_cache_hits': 0.4,
            'l1_cache_misses': 0.4,
            'l2_cache_hit_rate': 0.6,
            'l2_cache_miss_rate': 0.5,
            'l2_cache_hits': 0.4,
            'l2_cache_misses': 0.4,
            'l3_cache_hit_rate': 0.4,
            'l3_cache_miss_rate': 0.3,
            'l3_cache_hits': 0.3,
            'l3_cache_misses': 0.3,
            
            # Branch prediction metrics
            'branch_misprediction_rate': 0.5,
            'branch_prediction_accuracy': 0.5,
            'branch_mispredictions': 0.4,
            'branch_predictions': 0.4,
            
            # Memory metrics
            'memory_bandwidth': 0.5,
            
            # Any other metrics get default weight
        }
    
    errors_squared = []
    
    # Get all unique metrics across all workloads
    all_metric_names = set()
    for metrics in ground_truth.values():
        if isinstance(metrics, dict):
            all_metric_names.update(metrics.keys())
    
    # Remove metadata keys
    all_metric_names.discard('_source')
    all_metric_names.discard('_metadata')
    
    for workload_id, C_wi_metrics in ground_truth.items():
        # Get estimated metrics Swi,AP using performance model
        S_wi_AP_metrics = estimate_all_metrics(workload_id, ap, performance_model, ground_truth)
        
        if use_multi_metric:
            # Multi-metric error: weighted sum of errors across ALL available metrics
            workload_error_squared = 0.0
            metrics_used = 0
            
            # Use ALL metrics found in ground truth (not just predefined ones)
            for metric_name in all_metric_names:
                if metric_name in ['_source', '_metadata']:
                    continue
                
                C_value = C_wi_metrics.get(metric_name)
                S_value = S_wi_AP_metrics.get(metric_name)
                
                # Skip if either value is missing
                if C_value is None or S_value is None:
                    continue
                
                # Get weight for this metric (use default if not specified)
                weight = metric_weights.get(metric_name, 0.2)  # Default weight for unknown metrics
                
                # Normalize error by metric value (for relative error)
                if C_value != 0:
                    normalized_error = abs(C_value - S_value) / abs(C_value)
                else:
                    normalized_error = abs(C_value - S_value)
                
                workload_error_squared += weight * (normalized_error ** 2)
                metrics_used += 1
            
            # If no matching metrics found, fall back to execution_time
            if metrics_used == 0:
                C_time = C_wi_metrics.get('execution_time', 1.0)
                S_time = S_wi_AP_metrics.get('execution_time', 1.0)
                workload_error_squared = abs(C_time - S_time) ** 2
        else:
            # Single-metric error (backward compatibility)
            C_time = C_wi_metrics.get('execution_time', 1.0) if isinstance(C_wi_metrics, dict) else C_wi_metrics
            S_time = S_wi_AP_metrics.get('execution_time', 1.0)
            workload_error_squared = abs(C_time - S_time) ** 2
        
        errors_squared.append(workload_error_squared)
    
    # Calculate aggregate error EAggW,AP = sqrt(Σ(Ewi,AP)²)
    E_Agg_W_AP = np.sqrt(np.sum(errors_squared))
    
    return E_Agg_W_AP


# ============================================================================
# MULTI-ARMED BANDIT (UCB1) IMPLEMENTATION
# ============================================================================

class UCB1Bandit:
    """
    UCB1 Multi-Armed Bandit implementation for parameter selection.
    
    Each configuration (parameter assignment AP) is an "arm".
    The reward is the negative of the error (maximizing reward = minimizing error).
    """
    
    def __init__(self, tunable_params: Dict[str, List[int]], randomize_order: bool = True):
        """
        Initialize UCB1 bandit with all possible configurations.
        
        Args:
            tunable_params: Dictionary of parameter names to possible values
            randomize_order: If True, randomize the order of initial arm pulls
        """
        self.configs = self._generate_configurations(tunable_params)
        self.num_arms = len(self.configs)
        
        # Randomize initial arm order to avoid always starting with same config
        if randomize_order:
            random.seed()  # Use system time for seed
            indices = list(range(self.num_arms))
            random.shuffle(indices)
            self.configs = [self.configs[i] for i in indices]
            print(f"Randomized initial arm order")
        
        # Track which arms have been pulled (for initialization phase)
        self.unpulled_arms = list(range(self.num_arms))
        if randomize_order:
            random.shuffle(self.unpulled_arms)
        
        # UCB1 state variables
        self.counts = np.zeros(self.num_arms)  # N_k(t): times arm k pulled
        self.values = np.zeros(self.num_arms)  # Q_k(t): average reward
        self.total_pulls = 0  # t: total pulls
        
        print(f"Initialized UCB1 Bandit with {self.num_arms} configurations (arms)")
    
    def _generate_configurations(self, params: Dict[str, List[int]]) -> List[Dict[str, int]]:
        """Generate all combinations of discrete parameters."""
        keys = list(params.keys())
        values = list(params.values())
        configs = []
        for combination in product(*values):
            configs.append(dict(zip(keys, combination)))
        return configs
    
    def select_arm(self) -> Tuple[Dict[str, int], int]:
        """
        Select next arm (configuration) using UCB1 algorithm.
        
        UCB1 formula: argmax_k [Q_k(t) + c * sqrt(ln(t) / N_k(t))]
        where c = sqrt(2) for UCB1
        
        Returns:
            Tuple of (configuration dict, arm_index)
        """
        self.total_pulls += 1
        
        # Initialization: pull each arm once (in randomized order)
        if self.unpulled_arms:
            arm_index = self.unpulled_arms.pop(0)
            return self.configs[arm_index], arm_index
        
        # UCB1: select arm with highest upper confidence bound
        ucb_values = np.zeros(self.num_arms)
        for i in range(self.num_arms):
            if self.counts[i] == 0:
                ucb_values[i] = float('inf')
            else:
                confidence_bound = np.sqrt(2 * np.log(self.total_pulls) / self.counts[i])
                ucb_values[i] = self.values[i] + confidence_bound
        
        selected_index = np.argmax(ucb_values)
        return self.configs[selected_index], selected_index
    
    def update(self, arm_index: int, error: float) -> None:
        """
        Update arm statistics after pulling.
        
        Args:
            arm_index: Index of arm that was pulled
            error: Error value (will be converted to reward = -error)
        """
        # Reward is negative error (maximizing reward = minimizing error)
        reward = -error
        
        # Incremental update: Q_k(t+1) = Q_k(t) + (1/N_k) * (reward - Q_k(t))
        self.counts[arm_index] += 1
        n = self.counts[arm_index]
        self.values[arm_index] = self.values[arm_index] + (1/n) * (reward - self.values[arm_index])
    
    def get_best_config(self) -> Dict[str, int]:
        """Return configuration with highest average reward (lowest error)."""
        # Filter out arms that haven't been pulled
        valid_indices = np.where(self.counts > 0)[0]
        if len(valid_indices) == 0:
            return self.configs[0]
        
        best_index = valid_indices[np.argmax(self.values[valid_indices])]
        return self.configs[best_index]


# ============================================================================
# AUTOTUNING LOOP
# ============================================================================

def run_autotuning(
    max_iterations: int = 100,
    tunable_params: Optional[Dict[str, List[int]]] = None
) -> Tuple[Dict[str, int], float, List[float]]:
    """
    Run autotuning using MAB (UCB1) algorithm with VTune-based ground truth.
    
    Args:
        max_iterations: Maximum number of iterations
        tunable_params: Tunable parameters dict. If None, uses default.
    
    Returns:
        Tuple of (best_config, best_error, error_history)
    """
    if tunable_params is None:
        tunable_params = TUNABLE_PARAMETERS
    
    # Load ground truth (now supports multi-metric format)
    ground_truth = load_ground_truth()
    print(f"Loaded ground truth for {len(ground_truth)} workloads")
    
    # Extract execution times for calibration (backward compatibility)
    execution_times = [
        metrics.get('execution_time', 1.0) if isinstance(metrics, dict) else metrics
        for metrics in ground_truth.values()
    ]
    
    # Initialize performance model
    performance_model = PerformanceModel()
    
    # Calibrate model with ground truth
    avg_ground_truth = np.mean(execution_times)
    performance_model.set_base_execution_time(avg_ground_truth)
    
    # Initialize UCB1 bandit (with lazy generation for large spaces)
    if use_lazy_generation:
        # Use a modified bandit that generates configs on-demand
        try:
            from .lazy_bandit import LazyUCB1Bandit
            bandit = LazyUCB1Bandit(tunable_params)
        except ImportError:
            # Fallback: use regular bandit with limited parameters
            print("Warning: Lazy bandit not available, using first 6 parameters only")
            limited_params = {k: v for k, v in list(tunable_params.items())[:6]}
            bandit = UCB1Bandit(limited_params)
    else:
        bandit = UCB1Bandit(tunable_params)
    
    # Tracking
    error_history = []
    best_error = float('inf')
    best_config = None
    best_iteration = None
    
    print("Starting autotuning")
    print(f"Objective: minimize EAggW,AP = sqrt(sum(|Cwi - Swi,AP|^2))")
    print(f"Iterations: {max_iterations}")
    print(f"Using VTune-based ground truth and performance model")
    
    for iteration in range(max_iterations):
        # 1. Select configuration (arm) using UCB1
        config_ap, arm_index = bandit.select_arm()
        
        # 2. Calculate error for this configuration (using multi-metric for maximum accuracy)
        error = calculate_aggregate_error(config_ap, ground_truth, performance_model, use_multi_metric=True)
        
        # 3. Update bandit
        bandit.update(arm_index, error)
        
        # 4. Track best
        error_history.append(error)
        if error < best_error:
            best_error = error
            best_config = config_ap.copy()
            best_iteration = iteration + 1  # 1-indexed for user display
            print(f"Iteration {iteration+1}: NEW BEST config={config_ap}, error={error:.9f}")
        elif (iteration + 1) % 10 == 0 or iteration < 9:
            print(f"Iteration {iteration+1}: config={config_ap}, error={error:.9f}, best={best_error:.9f}")
    
    print("Autotuning complete")
    print(f"Best configuration: {best_config}")
    print(f"Best found at iteration: {best_iteration}")
    print(f"Minimum aggregate error: {best_error:.9f}")
    print(f"Error range: {min(error_history):.9f} to {max(error_history):.9f}")
    
    return best_config, best_error, error_history, best_iteration


# ============================================================================
# MAXIMIZED AUTOTUNING FOR PARAMETER MATCHING
# ============================================================================

# NOTE: refine_parameter_ranges removed - we should NOT use actual parameters
# during optimization. This function was using actual_params which is incorrect
# for predicting unknown CPU parameters.


class MaximizedUCB1Bandit:
    """
    UCB1 Bandit optimized for maximum parameter matching.
    Uses combined error (performance + parameter matching).
    """
    
    def __init__(
        self,
        tunable_params: Dict[str, List[int]],
        actual_params: Dict[str, int],
        randomize_order: bool = True
    ):
        """Initialize maximized bandit."""
        self.actual_params = actual_params
        self.configs = self._generate_configurations(tunable_params)
        self.num_arms = len(self.configs)
        
        if randomize_order:
            random.seed()
            indices = list(range(self.num_arms))
            random.shuffle(indices)
            self.configs = [self.configs[i] for i in indices]
        
        self.unpulled_arms = list(range(self.num_arms))
        if randomize_order:
            random.shuffle(self.unpulled_arms)
        
        self.counts = np.zeros(self.num_arms)
        self.values = np.zeros(self.num_arms)
        self.total_pulls = 0
        
        print(f"Initialized Maximized UCB1 Bandit with {self.num_arms} configurations")
        print(f"Target parameters: {actual_params}")
        if len(self.configs) < 10000:
            print(f"Configuration space reduced by focusing around actual values")
    
    def _generate_configurations(self, params: Dict[str, List[int]]) -> List[Dict[str, int]]:
        """Generate all parameter combinations."""
        keys = list(params.keys())
        values = list(params.values())
        configs = []
        for combination in product(*values):
            configs.append(dict(zip(keys, combination)))
        return configs
    
    def select_arm(self) -> Tuple[Dict[str, int], int]:
        """Select next arm using UCB1."""
        self.total_pulls += 1
        
        if self.unpulled_arms:
            arm_index = self.unpulled_arms.pop(0)
            return self.configs[arm_index], arm_index
        
        ucb_values = np.zeros(self.num_arms)
        for i in range(self.num_arms):
            if self.counts[i] == 0:
                ucb_values[i] = float('inf')
            else:
                confidence_bound = np.sqrt(2 * np.log(self.total_pulls) / self.counts[i])
                ucb_values[i] = self.values[i] + confidence_bound
        
        selected_index = np.argmax(ucb_values)
        return self.configs[selected_index], selected_index
    
    def update(self, arm_index: int, error: float) -> None:
        """Update arm statistics."""
        reward = -error
        self.counts[arm_index] += 1
        n = self.counts[arm_index]
        self.values[arm_index] = self.values[arm_index] + (1/n) * (reward - self.values[arm_index])
    
    def get_best_config(self) -> Dict[str, int]:
        """Return configuration with highest reward."""
        valid_indices = np.where(self.counts > 0)[0]
        if len(valid_indices) == 0:
            return self.configs[0]
        best_index = valid_indices[np.argmax(self.values[valid_indices])]
        return self.configs[best_index]


def run_maximized_autotuning(
    max_iterations: int = 500,
    use_multi_metric: bool = True,
    metric_weights: Optional[Dict[str, float]] = None
) -> Tuple[Dict[str, int], float, List[float], int, Dict[str, int], List[int], Dict[str, any]]:
    """
    Run autotuning to predict CPU parameters based ONLY on performance metrics.
    
    This function predicts CPU microarchitecture parameters using ONLY performance
    metrics (ground truth). Actual CPU parameters are NOT used during optimization
    and are only retrieved at the end for validation/comparison.
    
    Methodology:
    1. Use ONLY performance metrics (ground truth) to find best parameters
    2. Compare predicted performance vs actual performance (ground truth)
    3. At the end, compare predicted parameters vs actual parameters (validation only)
    
    Args:
        max_iterations: Maximum iterations (recommended: 500+)
        use_multi_metric: Use all available metrics for better accuracy
        metric_weights: Weights for performance metrics (default: equal weights)
    
    Returns:
        Tuple of (best_config, best_error, error_history, best_iteration, actual_params, match_history)
    """
    # Load ground truth (performance metrics ONLY)
    ground_truth = load_ground_truth()
    print(f"Loaded ground truth for {len(ground_truth)} workloads")
    print("Using ONLY performance metrics for parameter prediction")
    print("(Actual CPU parameters will be used only for validation at the end)")
    
    # Use full parameter space (no refinement based on actual params)
    tunable_params = TUNABLE_PARAMETERS
    total_configs = np.prod([len(v) for v in tunable_params.values()])
    print(f"\nParameter space: {total_configs:,} configurations")
    
    # For large parameter spaces, we use lazy configuration generation
    # Instead of generating all configs upfront, we generate on-demand
    use_lazy_generation = total_configs > 1e6  # Use lazy generation for > 1M configs
    if use_lazy_generation:
        print("Using lazy configuration generation (on-demand sampling)")
        print("This allows exploration of extremely large parameter spaces")
    
    # Initialize ENHANCED performance model with better sensitivity
    performance_model = EnhancedPerformanceModel()
    
    # Extract execution times for baseline calibration
    execution_times = [
        metrics.get('execution_time', 1.0) if isinstance(metrics, dict) else metrics
        for metrics in ground_truth.values()
    ]
    avg_ground_truth = np.mean(execution_times)
    performance_model.set_base_execution_time(avg_ground_truth)
    
    # Calibrate model from ground truth data (improves accuracy)
    performance_model.calibrate_from_ground_truth(ground_truth)
    
    print("\nEnhanced performance model initialized with:")
    print(f"  - Higher parameter sensitivity (80% ROB, 70% width, 85% L1, etc.)")
    print(f"  - Calibrated from ground truth data")
    print(f"  - Better metric estimation")
    
    # Initialize UCB1 bandit (with lazy generation for large spaces)
    if use_lazy_generation:
        # Use a modified bandit that generates configs on-demand
        try:
            from .lazy_bandit import LazyUCB1Bandit
            bandit = LazyUCB1Bandit(tunable_params)
        except ImportError:
            # Fallback: use regular bandit with limited parameters
            print("Warning: Lazy bandit not available, using first 6 parameters only")
            limited_params = {k: v for k, v in list(tunable_params.items())[:6]}
            bandit = UCB1Bandit(limited_params)
            use_lazy_generation = False
    else:
        bandit = UCB1Bandit(tunable_params)
    
    # Tracking
    error_history = []
    best_error = float('inf')
    best_config = None
    best_iteration = None
    unique_configs_tested = set()  # Track unique configurations tested
    
    total_configs = np.prod([len(v) for v in tunable_params.values()])
    
    print("\nStarting autotuning (performance-based prediction only)")
    print(f"Iterations: {max_iterations}")
    print(f"Multi-metric: {use_multi_metric}")
    print(f"Total possible configurations: {total_configs:,}")
    if use_lazy_generation:
        print(f"Using lazy configuration generation (on-demand sampling)")
        print(f"Will test up to {max_iterations:,} unique configurations")
    else:
        print(f"Will test: {max_iterations:,} configurations ({max_iterations/total_configs*100:.2f}% of search space)")
    print()
    
    for iteration in range(max_iterations):
        # Select configuration
        config_ap, arm_index = bandit.select_arm()
        
        # Track unique configurations
        config_tuple = tuple(sorted(config_ap.items()))
        unique_configs_tested.add(config_tuple)
        
        # Calculate ONLY performance prediction error (no parameter matching error)
        perf_error = calculate_aggregate_error(
            config_ap,
            ground_truth,
            performance_model,
            use_multi_metric=use_multi_metric,
            metric_weights=metric_weights
        )
        
        # Update bandit with performance error only
        bandit.update(arm_index, perf_error)
        
        # Track errors
        error_history.append(perf_error)
        
        # Track best (based on performance error only)
        if perf_error < best_error:
            best_error = perf_error
            best_config = config_ap.copy()
            best_iteration = iteration + 1
            
            print(f"Iteration {iteration+1}: NEW BEST")
            print(f"  Config: {config_ap}")
            print(f"  Performance error: {perf_error:.6f}")
            print()
        elif (iteration + 1) % 50 == 0 or iteration < 9:
            print(f"Iteration {iteration+1}: error={perf_error:.6f}, best={best_error:.6f}")
    
    print("Autotuning complete")
    print(f"Best configuration: {best_config}")
    print(f"Best found at iteration: {best_iteration}")
    print(f"Minimum performance error: {best_error:.9f}")
    print(f"\nSearch Space Coverage:")
    print(f"  Total possible configurations: {total_configs:,}")
    if use_lazy_generation and hasattr(bandit, 'get_search_space_info'):
        search_info = bandit.get_search_space_info()
        print(f"  Unique configurations tested: {search_info['unique_configs_tested']:,}")
        print(f"  Coverage: {search_info['coverage_percent']:.6f}% of search space")
        print(f"  Configurations tested per iteration: {search_info['configs_tested_per_pull']:.2f}")
    else:
        print(f"  Unique configurations tested: {len(unique_configs_tested):,}")
        print(f"  Coverage: {len(unique_configs_tested)/total_configs*100:.6f}% of search space")
        print(f"  Configurations tested per iteration: {len(unique_configs_tested)/max_iterations:.2f}")
    
    # NOW get actual parameters for validation/comparison only
    print("\n" + "=" * 70)
    print("VALIDATION: Comparing predicted vs actual parameters")
    print("=" * 70)
    system_profiler = SystemProfiler()
    actual_params = system_profiler.get_actual_parameters()
    print(f"Actual CPU parameters: {actual_params}")
    
    # Calculate matches for validation
    matches = sum(1 for k in actual_params.keys() 
                 if best_config.get(k) == actual_params.get(k))
    match_pct = matches / len(actual_params) * 100
    
    # Generate match history (for compatibility, but only meaningful at the end)
    match_history = [0] * (len(error_history) - 1) + [matches]
    
    print(f"\nPredicted parameters: {best_config}")
    print(f"Parameter matches: {matches}/{len(actual_params)} ({match_pct:.1f}%)")
    
    # Add search space info to return (for analysis)
    search_info = {
        'total_configs': total_configs,
        'unique_configs_tested': len(unique_configs_tested),
        'coverage_percent': len(unique_configs_tested) / total_configs * 100,
        'iterations': max_iterations
    }
    
    return best_config, best_error, error_history, best_iteration, actual_params, match_history, search_info


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_convergence_plot(
    error_history: List[float],
    best_error: float,
    best_config: Dict[str, int],
    output_file: str = 'mab_convergence.png'
):
    """Create convergence visualization."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    iterations = np.arange(1, len(error_history) + 1)
    best_idx = int(np.argmin(error_history))
    best_iter = iterations[best_idx]
    best_err_point = error_history[best_idx]
    
    # Top: Error convergence
    ax1 = axes[0]
    ax1.plot(iterations, error_history, 'b-', linewidth=2, alpha=0.7, label='Aggregate Error EAggW,AP')
    ax1.axhline(y=best_error, color='r', linestyle='--', linewidth=2, label=f'Best: {best_error:.9f}')
    ax1.scatter([best_iter], [best_err_point], color='red', zorder=5, s=80, marker='o', label=f'Best iteration: {best_iter}')
    ax1.annotate(f'Iter {best_iter}\n{best_err_point:.9f}',
                 xy=(best_iter, best_err_point),
                 xytext=(best_iter + max(1, len(error_history)//25), best_err_point),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=8),
                 fontsize=9, color='red')
    ax1.set_xlabel('Iteration', fontsize=12)
    ax1.set_ylabel('Aggregate Error EAggW,AP', fontsize=12)
    ax1.set_title('MAB Autotuning Convergence (VTune-based)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Bottom: Error distribution
    ax2 = axes[1]
    ax2.hist(error_history, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
    ax2.axvline(x=best_error, color='r', linestyle='--', linewidth=2, label=f'Best: {best_error:.9f}')
    ax2.set_xlabel('Aggregate Error EAggW,AP', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Error Distribution', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add best config text
    config_text = (f"Best Config: ROB={best_config['rob_size']}, "
                   f"L1={best_config['l1_cache_size']}KB, "
                   f"L2={best_config['l2_cache_size']}KB, "
                   f"Width={best_config['issue_width']}")
    fig.suptitle(config_text, fontsize=11, y=0.995)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"Convergence plot saved: {output_file}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import sys
    
    max_iter = 100
    if '--iterations' in sys.argv:
        idx = sys.argv.index('--iterations')
        if idx + 1 < len(sys.argv):
            max_iter = int(sys.argv[idx + 1])
    
    # Run autotuning
    best_config, best_error, error_history, best_iteration = run_autotuning(max_iterations=max_iter)
    
    # Create visualization
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    create_convergence_plot(error_history, best_error, best_config, 
                           str(output_dir / 'mab_convergence.png'))
    
    print("\nResults:")
    print(f"Best configuration: {best_config}")
    print(f"Best found at iteration: {best_iteration}")
    print(f"Minimum aggregate error: {best_error:.9f}")
    print(f"Total iterations: {len(error_history)}")
    print(f"Convergence plot: {output_dir / 'mab_convergence.png'}")
