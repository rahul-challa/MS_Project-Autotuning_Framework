"""
VTune/EMON Autotuning Framework - Main Autotuner Module

Multi-Armed Bandit (MAB) Autotuning Framework using Intel VTune Profiler and EMON
for CPU characterization and parameter prediction.
"""

import numpy as np
import json
import subprocess
import random
from itertools import product
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import time

from .config import Config
from .discovery import VTuneMetricsDiscovery
from .benchmarks import BenchmarkWorkloads
from .vtune_runner import VTuneRunner
from .emon_runner import EMONRunner


# ============================================================================
# DATA LOADING
# ============================================================================

def load_ground_truth() -> Dict[str, float]:
    """
    Load ground truth execution times.
    
    Returns:
        Dictionary mapping workload_id to execution time in seconds
    """
    if Config.GROUND_TRUTH_FILE.exists():
        with open(Config.GROUND_TRUTH_FILE, 'r') as f:
            data = json.load(f)
            # Extract workloads (exclude metadata)
            return {k: v for k, v in data.items() if isinstance(v, (int, float))}
    
    # Generate ground truth if not available
    print("Ground truth not found. Generating...")
    workloads = BenchmarkWorkloads()
    gt = workloads.save_ground_truth(str(Config.GROUND_TRUTH_FILE))
    return {k: v for k, v in gt.items() if isinstance(v, (int, float))}


def load_vtune_discovery() -> Dict:
    """Load VTune discovery results."""
    if Config.VTUNE_DISCOVERY_FILE.exists():
        with open(Config.VTUNE_DISCOVERY_FILE, 'r') as f:
            return json.load(f)
    
    # Run discovery if not available
    print("VTune discovery not found. Running discovery...")
    discovery = VTuneMetricsDiscovery()
    return discovery.save_discovery(str(Config.VTUNE_DISCOVERY_FILE))


# ============================================================================
# VTUNE/EMON INTEGRATION
# ============================================================================

def run_benchmark_with_vtune(
    workload_id: str,
    ap: Dict,
    benchmark_dir: Path,
    use_emon: bool = True
) -> float:
    """
    Run benchmark with VTune/EMON and return execution time.
    
    Args:
        workload_id: Workload identifier
        ap: Parameter assignment dict (VTune configuration)
        benchmark_dir: Directory containing benchmark scripts
        use_emon: Whether to also run EMON
        
    Returns:
        Execution time in seconds
    """
    workload_path = benchmark_dir / f"{workload_id}.py"
    
    if not workload_path.exists():
        print(f"Warning: Workload not found: {workload_path}")
        return float('inf')
    
    # Run VTune
    vtune_runner = VTuneRunner()
    
    analysis_type = ap.get("analysis_type", "hotspots")
    
    additional_options = []
    # Note: Stack collection knob names vary by analysis type
    # For now, we'll skip this to avoid errors
    # if ap.get("enable_callstack", False):
    #     additional_options.append("-knob")
    #     additional_options.append("enable-stack-collection=true")
    
    result = vtune_runner.run_vtune(
        str(workload_path),
        analysis_type=analysis_type,
        additional_options=additional_options if additional_options else None,
        timeout=Config.DEFAULT_TIMEOUT
    )
    
    # Extract execution time
    execution_time = 0.0
    if result.get("success"):
        execution_time = vtune_runner.extract_execution_time(result)
    else:
        # VTune failed - use fallback timing
        print(f"VTune failed for {workload_id}, using direct timing fallback...")
        error_msg = result.get('error', 'Unknown error')
        if 'not applicable' in error_msg.lower() or 'microarchitecture' in error_msg.lower():
            print(f"  Note: Analysis type may not be supported on this CPU")
    
    # Optionally run EMON for additional metrics (even if VTune failed)
    # Note: EMON is Intel-specific and will fail on AMD CPUs
    if use_emon:
        try:
            emon_runner = EMONRunner()
            emon_result = emon_runner.run_emon(
                str(workload_path),
                timeout=Config.DEFAULT_TIMEOUT
            )
            if emon_result.get("success"):
                # Store EMON metrics for later analysis
                emon_metrics = emon_runner.extract_performance_metrics(emon_result)
                result["emon_metrics"] = emon_metrics
            elif "AMD" in emon_result.get("error", "") or "Intel-specific" in emon_result.get("error", ""):
                # Silently skip EMON on AMD CPUs (expected behavior)
                pass
        except Exception as e:
            # EMON failures are non-critical - framework continues with direct timing
            pass
    
    # If we couldn't extract time from VTune, use a fallback
    if execution_time <= 0:
        # Fallback: run workload directly to measure time
        try:
            import sys
            from pathlib import Path
            
            # Get real Python executable (avoid Windows Store launcher)
            python_exe = sys.executable
            if "WindowsApps" in python_exe and "python.exe" in python_exe:
                # Try to find real Python using py launcher
                try:
                    result = subprocess.run(
                        ["py", "-c", "import sys; print(sys.executable)"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        real_python = result.stdout.strip()
                        if Path(real_python).exists():
                            python_exe = real_python
                except:
                    # Fallback to common paths
                    common_paths = [
                        Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "python.exe",
                        Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python312" / "python.exe",
                        Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python311" / "python.exe",
                    ]
                    for path in common_paths:
                        if path.exists():
                            python_exe = str(path)
                            break
            
            start = time.perf_counter()
            subprocess.run(
                [python_exe, str(workload_path)],
                capture_output=True,
                timeout=300
            )
            execution_time = time.perf_counter() - start
            if execution_time > 0:
                print(f"  Fallback timing: {execution_time:.6f}s")
        except Exception as e:
            print(f"  Fallback timing also failed: {e}")
            execution_time = float('inf')
    
    return execution_time


# ============================================================================
# ERROR CALCULATION
# ============================================================================

def calculate_aggregate_error(
    ap: Dict,
    ground_truth: Dict[str, float],
    benchmark_dir: Path
) -> float:
    """
    Calculate L2-norm aggregate error EAggW,AP.
    
    Formula:
        Ewi,AP = |Cwi - Swi,AP|
        EAggW,AP = sqrt(Σ(Ewi,AP)²)
    
    Args:
        ap: Parameter assignment dict (VTune configuration)
        ground_truth: Dictionary mapping workload_id to real execution time Cwi
        benchmark_dir: Directory containing benchmark scripts
    
    Returns:
        Aggregate error EAggW,AP
    """
    errors_squared = []
    
    for workload_id, C_wi in ground_truth.items():
        # Get simulated/measured time Swi,AP using VTune
        S_wi_AP = run_benchmark_with_vtune(workload_id, ap, benchmark_dir)
        
        # Calculate absolute error Ewi,AP = |Cwi - Swi,AP|
        E_wi_AP = abs(C_wi - S_wi_AP)
        errors_squared.append(E_wi_AP ** 2)
        
        print(f"  {workload_id}: C={C_wi:.6f}s, S={S_wi_AP:.6f}s, E={E_wi_AP:.6f}s")
    
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
    
    def __init__(self, tunable_params: Dict, randomize_order: bool = True):
        """
        Initialize UCB1 bandit with all possible configurations.
        
        Args:
            tunable_params: Dictionary of parameter names to possible values
            randomize_order: If True, randomize the order of initial arm pulls
        """
        self.configs = self._generate_configurations(tunable_params)
        self.num_arms = len(self.configs)
        
        # Randomize initial arm order
        if randomize_order:
            random.seed()
            indices = list(range(self.num_arms))
            random.shuffle(indices)
            self.configs = [self.configs[i] for i in indices]
        
        # Track which arms have been pulled
        self.unpulled_arms = list(range(self.num_arms))
        if randomize_order:
            random.shuffle(self.unpulled_arms)
        
        # UCB1 state variables
        self.counts = np.zeros(self.num_arms)
        self.values = np.zeros(self.num_arms)
        self.total_pulls = 0
        
        print(f"Initialized UCB1 Bandit with {self.num_arms} configurations (arms)")
    
    def _generate_configurations(self, params: Dict) -> List[Dict]:
        """Generate all combinations of discrete parameters."""
        keys = list(params.keys())
        values = list(params.values())
        configs = []
        for combination in product(*values):
            configs.append(dict(zip(keys, combination)))
        return configs
    
    def select_arm(self) -> Tuple[Dict, int]:
        """
        Select next arm (configuration) using UCB1 algorithm.
        
        Returns:
            Tuple of (configuration dict, arm_index)
        """
        self.total_pulls += 1
        
        # Initialization: pull each arm once
        if self.unpulled_arms:
            arm_index = self.unpulled_arms.pop(0)
            return self.configs[arm_index], arm_index
        
        # UCB1: select arm with highest upper confidence bound
        ucb_values = np.zeros(self.num_arms)
        for i in range(self.num_arms):
            if self.counts[i] > 0:
                confidence_bound = np.sqrt(2 * np.log(self.total_pulls) / self.counts[i])
                ucb_values[i] = self.values[i] + confidence_bound
            else:
                ucb_values[i] = float('inf')
        
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
        
        # Incremental update
        self.counts[arm_index] += 1
        n = self.counts[arm_index]
        self.values[arm_index] = self.values[arm_index] + (1/n) * (reward - self.values[arm_index])
    
    def get_best_config(self) -> Dict:
        """Return configuration with highest average reward (lowest error)."""
        if self.total_pulls == 0:
            return {}
        best_index = np.argmax(self.values)
        return self.configs[best_index]


# ============================================================================
# AUTOTUNING LOOP
# ============================================================================

def run_autotuning(
    max_iterations: int = 50,
    tunable_params: Optional[Dict] = None,
    use_emon: bool = True
) -> Tuple[Dict, float, List[float], Dict]:
    """
    Run autotuning using MAB (UCB1) algorithm with VTune/EMON.
    
    Args:
        max_iterations: Maximum number of iterations
        tunable_params: Tunable parameters dict (uses defaults if None)
        use_emon: Whether to use EMON in addition to VTune
    
    Returns:
        Tuple of (best_config, best_error, error_history, collected_metrics)
    """
    # Load ground truth
    ground_truth = load_ground_truth()
    print(f"Loaded ground truth for {len(ground_truth)} workloads")
    
    # Load VTune discovery
    discovery = load_vtune_discovery()
    
    # Determine tunable parameters
    if tunable_params is None:
        tunable_params = Config.DEFAULT_TUNABLE_PARAMETERS.copy()
        # Update with discovered analysis types if available
        if "analysis_types" in discovery:
            available_types = discovery["analysis_types"]
            if available_types:
                tunable_params["analysis_type"] = available_types[:3]  # Limit to 3
    
    # Create benchmark scripts
    benchmark_dir = Config.BENCHMARKS_DIR
    workloads = BenchmarkWorkloads()
    print("Creating benchmark scripts...")
    for workload_id in ground_truth.keys():
        workloads.create_benchmark_executable(workload_id, benchmark_dir)
    
    # Initialize UCB1 bandit
    bandit = UCB1Bandit(tunable_params)
    
    # Tracking
    error_history = []
    best_error = float('inf')
    best_config = None
    collected_metrics = {}  # Store metrics from best configuration
    
    print("\nStarting autotuning with VTune/EMON")
    print(f"Objective: minimize EAggW,AP = sqrt(sum(|Cwi - Swi,AP|^2))")
    print(f"Iterations: {max_iterations}")
    print(f"Tunable parameters: {list(tunable_params.keys())}")
    
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration+1}/{max_iterations} ---")
        
        # 1. Select configuration (arm) using UCB1
        config_ap, arm_index = bandit.select_arm()
        print(f"Selected config: {config_ap}")
        
        # 2. Calculate error for this configuration
        error = calculate_aggregate_error(config_ap, ground_truth, benchmark_dir)
        
        # 3. Update bandit
        bandit.update(arm_index, error)
        
        # 4. Track best and collect metrics
        error_history.append(error)
        if error < best_error:
            best_error = error
            best_config = config_ap.copy()
            # Collect metrics from best configuration
            collected_metrics = _collect_metrics_for_config(config_ap, benchmark_dir)
            print(f"*** NEW BEST: error={error:.9f}, config={best_config}")
        else:
            print(f"Error: {error:.9f}, Best: {best_error:.9f}")
    
    print("\n" + "="*60)
    print("Autotuning complete")
    print(f"Best configuration: {best_config}")
    print(f"Minimum aggregate error: {best_error:.9f}")
    print(f"Error range: {min(error_history):.9f} to {max(error_history):.9f}")
    
    return best_config, best_error, error_history, collected_metrics


def _collect_metrics_for_config(config_ap: Dict, benchmark_dir: Path) -> Dict:
    """
    Collect metrics from a single representative workload with given configuration.
    
    Args:
        config_ap: Configuration to use
        benchmark_dir: Directory containing benchmarks
        
    Returns:
        Dictionary of collected metrics
    """
    from .vtune_runner import VTuneRunner
    from .emon_runner import EMONRunner
    
    metrics = {}
    
    # Use a representative workload (matrix multiplication)
    workload_path = benchmark_dir / "w1_matrix_mult.py"
    
    if not workload_path.exists():
        return metrics
    
    # Run VTune
    try:
        vtune_runner = VTuneRunner()
        vtune_result = vtune_runner.run_vtune(
            str(workload_path),
            analysis_type=config_ap.get("analysis_type", "hotspots"),
            timeout=Config.DEFAULT_TIMEOUT
        )
        
        if vtune_result.get("success"):
            metrics.update(vtune_runner.extract_performance_metrics(vtune_result))
    except:
        pass
    
    # Run EMON
    try:
        emon_runner = EMONRunner()
        emon_result = emon_runner.run_emon(
            str(workload_path),
            timeout=Config.DEFAULT_TIMEOUT
        )
        
        if emon_result.get("success"):
            metrics.update(emon_runner.extract_performance_metrics(emon_result))
    except:
        pass
    
    return metrics


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_convergence_plot(
    error_history: List[float],
    best_error: float,
    best_config: Dict,
    output_file: str = 'vtune_convergence.png'
):
    """Create convergence visualization showing MAB model convergence."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    iterations = np.arange(1, len(error_history) + 1)
    best_idx = int(np.argmin(error_history))
    best_iter = iterations[best_idx]
    best_err_point = error_history[best_idx]
    
    # Top: Error convergence (MAB learning curve)
    ax1 = axes[0]
    ax1.plot(iterations, error_history, 'b-', linewidth=2, alpha=0.7, label='Aggregate Error EAggW,AP')
    ax1.axhline(y=best_error, color='r', linestyle='--', linewidth=2, label=f'Best: {best_error:.9f}')
    ax1.scatter([best_iter], [best_err_point], color='red', zorder=5, s=100, marker='o', 
                label=f'Best iteration: {best_iter}', edgecolors='darkred', linewidths=2)
    
    # Add moving average to show convergence trend
    if len(error_history) > 10:
        window = min(10, len(error_history) // 10)
        moving_avg = []
        for i in range(len(error_history)):
            start = max(0, i - window)
            moving_avg.append(np.mean(error_history[start:i+1]))
        ax1.plot(iterations, moving_avg, 'g--', linewidth=1.5, alpha=0.8, label=f'Moving Average (window={window})')
    
    ax1.set_xlabel('Iteration (MAB Exploration)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Aggregate Error EAggW,AP', fontsize=12, fontweight='bold')
    ax1.set_title('MAB (UCB1) Convergence - VTune/EMON Autotuning', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Add convergence annotation
    if len(error_history) > 1:
        initial_error = error_history[0]
        final_error = error_history[-1]
        improvement = ((initial_error - best_error) / initial_error) * 100 if initial_error > 0 else 0
        ax1.text(0.02, 0.98, f'Improvement: {improvement:.2f}%\nConverged: {best_iter}/{len(iterations)} iterations',
                transform=ax1.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
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
    config_text = f"Best Config: {best_config}"
    fig.suptitle(config_text, fontsize=11, y=0.995)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"Convergence plot saved: {output_file}")
    plt.close()


# ============================================================================
# CPU PARAMETER PREDICTION
# ============================================================================

def predict_cpu_parameters(
    best_config: Dict,
    discovery: Dict,
    benchmark_dir: Path,
    collected_metrics: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Predict CPU parameters based on VTune/EMON metrics.
    
    Args:
        best_config: Best VTune configuration found
        discovery: VTune discovery results
        benchmark_dir: Directory containing benchmarks
        collected_metrics: Optional pre-collected metrics dictionary
        
    Returns:
        Dictionary of predicted CPU parameters
    """
    from .vtune_runner import VTuneRunner
    from .emon_runner import EMONRunner
    
    predictions = {}
    
    # Run a comprehensive analysis with the best configuration
    print("\nRunning comprehensive analysis for CPU parameter prediction...")
    
    # Collect metrics from all workloads
    all_metrics = {}
    if collected_metrics:
        all_metrics = collected_metrics
    else:
        # Run one representative workload to collect metrics
        workloads = BenchmarkWorkloads()
        workload_id = "w1_matrix_mult"  # Use matrix multiplication as representative
        workload_path = benchmark_dir / f"{workload_id}.py"
        
        if workload_path.exists():
            # Run VTune
            vtune_runner = VTuneRunner()
            vtune_result = vtune_runner.run_vtune(
                str(workload_path),
                analysis_type=best_config.get("analysis_type", "hotspots"),
                timeout=Config.DEFAULT_TIMEOUT
            )
            
            if vtune_result.get("success"):
                all_metrics.update(vtune_runner.extract_performance_metrics(vtune_result))
            
            # Run EMON
            try:
                emon_runner = EMONRunner()
                emon_result = emon_runner.run_emon(
                    str(workload_path),
                    timeout=Config.DEFAULT_TIMEOUT
                )
                
                if emon_result.get("success"):
                    all_metrics.update(emon_runner.extract_performance_metrics(emon_result))
            except:
                pass
    
    # Predict parameters based on collected metrics
    predictions = _predict_from_metrics(all_metrics, discovery)
    
    print("CPU Parameter Predictions:")
    for param, value in predictions.items():
        print(f"  {param}: {value}")
    
    return predictions


def _predict_from_metrics(metrics: Dict, discovery: Dict) -> Dict[str, float]:
    """
    Predict CPU parameters from collected metrics using heuristics.
    
    Args:
        metrics: Dictionary of collected performance metrics
        discovery: VTune discovery results
        
    Returns:
        Dictionary of predicted parameters
    """
    predictions = {}
    
    # Predict cache sizes based on cache hit rates and access patterns
    if "LLC_MISS_RATE" in metrics:
        miss_rate = metrics["LLC_MISS_RATE"]
        # Lower miss rate suggests larger cache
        if miss_rate < 0.1:
            predictions["predicted_l3_cache_size_kb"] = 16384.0  # Large cache
        elif miss_rate < 0.2:
            predictions["predicted_l3_cache_size_kb"] = 8192.0
        elif miss_rate < 0.3:
            predictions["predicted_l3_cache_size_kb"] = 4096.0
        else:
            predictions["predicted_l3_cache_size_kb"] = 2048.0
    else:
        predictions["predicted_l3_cache_size_kb"] = 8192.0  # Default
    
    # Predict L2 cache based on L2 metrics
    if "L2_RQSTS.MISS" in metrics or "L2_RQSTS.REFERENCES" in metrics:
        # Estimate based on typical ratios
        predictions["predicted_l2_cache_size_kb"] = predictions["predicted_l3_cache_size_kb"] / 32
    else:
        predictions["predicted_l2_cache_size_kb"] = 256.0  # Default
    
    # L1 cache is typically 32KB per core
    cpu_info = discovery.get("cpu_info", {})
    cores = cpu_info.get("cores")
    if cores:
        predictions["predicted_l1_cache_size_kb"] = 32.0 * cores
    else:
        predictions["predicted_l1_cache_size_kb"] = 32.0  # Default per core
    
    # Predict ROB size based on CPI and instruction throughput
    if "CPI" in metrics:
        cpi = metrics["CPI"]
        # Lower CPI suggests better out-of-order execution (larger ROB)
        if cpi < 0.5:
            predictions["predicted_rob_size"] = 224  # Very efficient
        elif cpi < 0.8:
            predictions["predicted_rob_size"] = 192  # Good
        elif cpi < 1.2:
            predictions["predicted_rob_size"] = 160  # Moderate
        else:
            predictions["predicted_rob_size"] = 128  # Smaller ROB
    else:
        predictions["predicted_rob_size"] = 192  # Default
    
    # Predict issue width based on IPC
    if "IPC" in metrics:
        ipc = metrics["IPC"]
        # Higher IPC suggests wider issue width
        if ipc > 3.0:
            predictions["predicted_issue_width"] = 6  # Very wide
        elif ipc > 2.0:
            predictions["predicted_issue_width"] = 4  # Standard
        else:
            predictions["predicted_issue_width"] = 2  # Narrow
    else:
        predictions["predicted_issue_width"] = 4  # Default
    
    # Predict branch predictor accuracy
    if "BRANCH_PREDICT_RATE" in metrics:
        predictions["predicted_branch_predictor_accuracy"] = metrics["BRANCH_PREDICT_RATE"]
    elif "BRANCH_MISPREDICT_RATE" in metrics:
        predictions["predicted_branch_predictor_accuracy"] = 1.0 - metrics["BRANCH_MISPREDICT_RATE"]
    else:
        predictions["predicted_branch_predictor_accuracy"] = 0.95  # Default
    
    return predictions
