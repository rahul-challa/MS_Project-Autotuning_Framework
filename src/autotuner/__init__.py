"""
Autotuning Framework for CPU Model Validation using Intel VTune Profiler

This package provides a Multi-Armed Bandit (MAB) based autotuning framework
that uses Intel VTune Profiler to collect ground truth performance metrics
and tunes CPU microarchitecture parameters to minimize prediction error.
"""

from .mab_autotuner import (
    run_autotuning,
    run_maximized_autotuning,
    UCB1Bandit,
    MaximizedUCB1Bandit,
    TUNABLE_PARAMETERS,
    create_convergence_plot
)
from .vtune_profiler import VTuneProfiler
from .benchmark_runner import BenchmarkRunner
from .performance_model import PerformanceModel
from .system_profiler import SystemProfiler
from .workload_registry import (
    get_all_workloads,
    get_workload_code,
    get_workload_info,
    list_all_workloads,
    WORKLOADS
)

__version__ = '1.0.0'
__all__ = [
    'run_autotuning',
    'run_maximized_autotuning',  # Main function for parameter matching
    'UCB1Bandit',
    'MaximizedUCB1Bandit',
    'TUNABLE_PARAMETERS',
    'create_convergence_plot',
    'VTuneProfiler',
    'BenchmarkRunner',
    'PerformanceModel',
    'SystemProfiler',
    'get_all_workloads',
    'get_workload_code',
    'get_workload_info',
    'list_all_workloads',
    'WORKLOADS'
]
