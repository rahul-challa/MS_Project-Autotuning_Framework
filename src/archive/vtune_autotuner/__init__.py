"""
VTune/EMON Autotuning Framework

An end-to-end autotuning framework for CPU characterization using Intel VTune Profiler and EMON.
"""

__version__ = "1.0.0"
__author__ = "Viswanadh Rahul Challa"

from .config import Config
from .discovery import VTuneMetricsDiscovery
from .benchmarks import BenchmarkWorkloads
from .vtune_runner import VTuneRunner
from .emon_runner import EMONRunner
from .autotuner import run_autotuning, UCB1Bandit
from .cpu_info_extractor import CPUInfoExtractor
from .evaluate_predictions import evaluate_framework, compare_predictions_vs_actual

__all__ = [
    "Config",
    "VTuneMetricsDiscovery",
    "BenchmarkWorkloads",
    "VTuneRunner",
    "EMONRunner",
    "run_autotuning",
    "UCB1Bandit",
    "CPUInfoExtractor",
    "evaluate_framework",
    "compare_predictions_vs_actual",
]
