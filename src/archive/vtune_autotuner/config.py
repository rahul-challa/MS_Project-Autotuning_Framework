#!/usr/bin/env python3
"""
Configuration Module

Centralized configuration for the VTune/EMON Autotuning Framework.
"""

from pathlib import Path
from typing import Dict, List, Optional
import os


class Config:
    """Configuration class for the autotuning framework."""
    
    # Base directories - use user's home directory for data
    BASE_DIR = Path.home() / ".vtune_autotuner"
    BENCHMARKS_DIR = BASE_DIR / "benchmarks"
    RESULTS_DIR = BASE_DIR / "autotuning_results"
    VTUNE_RESULTS_DIR = BASE_DIR / "vtune_results"
    EMON_RESULTS_DIR = BASE_DIR / "emon_results"
    DATASETS_DIR = BASE_DIR / "datasets"
    
    # Data files
    GROUND_TRUTH_FILE = DATASETS_DIR / "ground_truth.json"
    VTUNE_DISCOVERY_FILE = DATASETS_DIR / "vtune_discovery.json"
    
    # VTune/EMON paths (will be auto-detected)
    VTUNE_PATH: Optional[str] = None
    EMON_PATH: Optional[str] = None
    
    # Default tunable parameters
    # Note: analysis_type will be filtered based on CPU architecture
    DEFAULT_TUNABLE_PARAMETERS = {
        "analysis_type": ["hotspots"],  # Start with most universal type
        "sampling_interval": [10],  # Single value to reduce iterations
        "enable_callstack": [False],  # Disabled to avoid knob errors
    }
    
    # Benchmark workload IDs
    DEFAULT_WORKLOADS = [
        "w1_matrix_mult",
        "w2_bubble_sort",
        "w3_fft_calc",
        "w4_memory_bandwidth",
        "w5_random_access",
        "w6_branch_intensive",
        "w7_prime_calc",
    ]
    
    # Autotuning parameters
    DEFAULT_MAX_ITERATIONS = 50
    DEFAULT_TIMEOUT = 600  # seconds
    DEFAULT_USE_EMON = True
    
    @classmethod
    def initialize_directories(cls):
        """Create all necessary directories."""
        dirs = [
            cls.BENCHMARKS_DIR,
            cls.RESULTS_DIR,
            cls.VTUNE_RESULTS_DIR,
            cls.EMON_RESULTS_DIR,
            cls.DATASETS_DIR,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_vtune_path(cls) -> Optional[str]:
        """Get VTune executable path."""
        if cls.VTUNE_PATH:
            return cls.VTUNE_PATH
        
        # Check environment variable
        if "VTUNE_PROFILER_DIR" in os.environ:
            vtune_dir = Path(os.environ["VTUNE_PROFILER_DIR"])
            candidate = vtune_dir / "bin64" / "vtune.exe"
            if candidate.exists():
                return str(candidate)
        
        # Common paths
        common_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI\vtune\latest\bin64\vtune.exe",
            r"C:\Program Files\Intel\oneAPI\vtune\latest\bin64\vtune.exe",
            r"C:\Program Files (x86)\IntelSWTools\vtune_profiler\bin64\vtune.exe",
            r"C:\Program Files\IntelSWTools\vtune_profiler\bin64\vtune.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        return None
    
    @classmethod
    def get_emon_path(cls) -> Optional[str]:
        """Get EMON executable path."""
        if cls.EMON_PATH:
            return cls.EMON_PATH
        
        # Check environment variable
        if "VTUNE_PROFILER_DIR" in os.environ:
            vtune_dir = Path(os.environ["VTUNE_PROFILER_DIR"])
            candidate = vtune_dir / "bin64" / "emon.exe"
            if candidate.exists():
                return str(candidate)
        
        # Common paths
        common_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI\vtune\latest\bin64\emon.exe",
            r"C:\Program Files\Intel\oneAPI\vtune\latest\bin64\emon.exe",
            r"C:\Program Files (x86)\IntelSWTools\vtune_profiler\bin64\emon.exe",
            r"C:\Program Files\IntelSWTools\vtune_profiler\bin64\emon.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        return None


# Initialize directories on import
Config.initialize_directories()
