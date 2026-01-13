#!/usr/bin/env python3
"""
Benchmark Runner Module

This module provides functions to run benchmarks and collect performance
metrics. It integrates with VTune Profiler to get ground truth measurements.
"""

import subprocess
import json
import time
import sys
import platform
from pathlib import Path
from typing import Dict, List, Optional
from .vtune_profiler import VTuneProfiler
from .workload_registry import (
    WORKLOADS,
    get_all_workloads,
    get_workload_code,
    get_workload_info,
    get_recommended_collection_types
)


class BenchmarkRunner:
    """
    Runs benchmarks and collects performance metrics using VTune.
    """
    
    def __init__(self, vtune_profiler: Optional[VTuneProfiler] = None):
        """
        Initialize benchmark runner.
        
        Args:
            vtune_profiler: VTuneProfiler instance. If None, creates a new one.
        """
        self.vtune = vtune_profiler or VTuneProfiler()
        self.benchmark_dir = Path(__file__).parent.parent.parent / 'data' / 'benchmarks'
        self.benchmark_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_python_executable(self) -> str:
        """Get the Python executable path."""
        # Use sys.executable which is the Python interpreter running this script
        return sys.executable
    
    def _create_benchmark_script(self, workload_id: str, code: str) -> Path:
        """Create a temporary benchmark script file."""
        script_file = self.benchmark_dir / f"{workload_id}_temp.py"
        script_file.parent.mkdir(parents=True, exist_ok=True)
        with open(script_file, 'w') as f:
            f.write(code)
        return script_file
    
    def get_workload_command(self, workload_id: str) -> List[str]:
        """
        Get the command to run a specific workload.
        
        Args:
            workload_id: Workload identifier (e.g., 'w1_matrix_mult')
        
        Returns:
            List of command arguments to run the workload
        """
        python_exe = self._get_python_executable()
        
        # Try to get from workload registry first
        try:
            code = get_workload_code(workload_id)
            script_file = self._create_benchmark_script(workload_id, code)
            return [python_exe, str(script_file)]
        except ValueError:
            pass
        
        # Fallback to old hardcoded workloads (for backward compatibility)
        workload_code = {
            'w1_matrix_mult': '''
import numpy as np
import time
n = 500
A = np.random.rand(n, n)
B = np.random.rand(n, n)
start = time.time()
C = np.dot(A, B)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w2_bubble_sort': '''
import random
import time
n = 10000
arr = [random.randint(1, 1000) for _ in range(n)]
start = time.time()
for i in range(n):
    for j in range(0, n - i - 1):
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w3_fft_calc': '''
import numpy as np
import time
n = 1000000
data = np.random.rand(n) + 1j * np.random.rand(n)
start = time.time()
result = np.fft.fft(data)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w4_memory_intensive': '''
import numpy as np
import time
# Memory-intensive workload with poor cache locality
n = 2000
arr = np.random.rand(n, n)
start = time.time()
# Strided access pattern
result = 0
for i in range(0, n, 8):
    for j in range(0, n, 8):
        result += arr[i, j]
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w5_compute_intensive': '''
import numpy as np
import time
# CPU-intensive mathematical operations
n = 1000
A = np.random.rand(n, n)
start = time.time()
# Multiple matrix operations
B = np.sin(A) * np.cos(A)
C = np.sqrt(np.abs(B))
D = np.log1p(C)
result = np.sum(D)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w6_branch_intensive': '''
import random
import time
# Branch-heavy workload
n = 50000
arr = [random.randint(1, 100) for _ in range(n)]
start = time.time()
result = 0
for x in arr:
    if x < 25:
        result += x * 2
    elif x < 50:
        result += x * 3
    elif x < 75:
        result += x * 4
    else:
        result += x * 5
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w7_cache_friendly': '''
import numpy as np
import time
# Cache-friendly sequential access
n = 5000
arr = np.random.rand(n, n)
start = time.time()
# Sequential access pattern
result = np.sum(arr, axis=1)
result = np.sum(result)
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
            'w8_mixed_workload': '''
import numpy as np
import time
# Mixed workload combining multiple patterns
n = 300
A = np.random.rand(n, n)
B = np.random.rand(n, n)
start = time.time()
# Matrix operations + element-wise operations
C = np.dot(A, B)
D = np.sin(C) + np.cos(C)
E = np.sort(D.flatten())
result = np.sum(E[::10])  # Strided access
end = time.time()
print(f"Execution time: {end - start:.6f} seconds")
''',
        }
        
        if workload_id in workload_code:
            # Create temporary script file (VTune works better with script files on Windows)
            script_file = self._create_benchmark_script(workload_id, workload_code[workload_id])
            return [python_exe, str(script_file)]
        
        # Try to find a benchmark executable
        benchmark_exe = self.benchmark_dir / f"{workload_id}.exe"
        if benchmark_exe.exists():
            return [str(benchmark_exe)]
        
        # Fallback: return a simple command
        return ['echo', f'Workload {workload_id} not found']
    
    def run_benchmark(
        self,
        workload_id: str,
        use_vtune: bool = True,
        fallback_on_error: bool = True,
        use_all_collection_types: bool = True
    ) -> Dict[str, float]:
        """
        Run a benchmark and collect performance metrics using all available VTune collection types.
        
        Args:
            workload_id: Workload identifier
            use_vtune: If True, use VTune profiling. If False, use simple timing.
            fallback_on_error: If True and VTune fails, fall back to simple timing
            use_all_collection_types: If True, collect metrics from all compatible collection types
        
        Returns:
            Dictionary of performance metrics (comprehensive if use_all_collection_types=True)
        """
        command = self.get_workload_command(workload_id)
        
        if use_vtune:
            try:
                # Use VTune to profile with all collection types
                metrics = self.vtune.profile_workload(
                    command,
                    workload_id,
                    collection_type='hotspots',
                    collect_all_types=use_all_collection_types
                )
                # Check if we got valid metrics (not defaults)
                exec_time = metrics.get('execution_time', float('inf'))
                if exec_time != float('inf') and exec_time != 1.0:  # Not default fallback
                    return metrics
                elif fallback_on_error:
                    # VTune failed, will fall through to timing
                    pass
                else:
                    return metrics
            except Exception as e:
                if fallback_on_error:
                    # Will fall through to timing
                    pass
                else:
                    raise
        
        # Fallback: Simple timing without VTune (or when VTune fails)
        # This gives us actual execution times
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Try to parse execution time from output (more accurate)
            if result.stdout:
                import re
                time_match = re.search(
                    r'Execution time:\s+([\d.]+)',
                    result.stdout,
                    re.IGNORECASE
                )
                if time_match:
                    execution_time = float(time_match.group(1))
            
            # Return actual timing metrics
            return {
                'execution_time': execution_time,
                'elapsed_time': execution_time,
                'cpu_time': execution_time,
                '_source': 'direct_timing'  # Mark as direct timing, not VTune
            }
        except subprocess.TimeoutExpired:
            return {'execution_time': float('inf')}
        except Exception as e:
            print(f"Error running benchmark {workload_id}: {e}")
            return {'execution_time': float('inf')}
    
    def collect_ground_truth(
        self,
        workload_ids: Optional[List[str]] = None,
        output_file: Optional[Path] = None,
        use_all_collection_types: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Collect comprehensive ground truth performance metrics for ALL workloads.
        
        Collects metrics from ALL VTune collection types to maximize accuracy.
        Uses ALL available workloads if workload_ids is None.
        
        Args:
            workload_ids: List of workload identifiers (None = use ALL workloads)
            output_file: Path to save ground truth JSON file
            use_all_collection_types: If True, use ALL compatible collection types
        
        Returns:
            Dictionary mapping workload_id to comprehensive metrics dictionary
        """
        # Use ALL workloads if not specified
        if workload_ids is None:
            workload_ids = get_all_workloads()
            print(f"Using ALL {len(workload_ids)} workloads from registry")
        
        ground_truth = {}
        
        print("Collecting comprehensive ground truth performance metrics using VTune...")
        print(f"  Workloads: {len(workload_ids)}")
        print(f"  Using ALL collection types: {use_all_collection_types}")
        
        for workload_id in workload_ids:
            print(f"  Profiling {workload_id}...")
            metrics = self.run_benchmark(
                workload_id,
                use_vtune=True,
                use_all_collection_types=use_all_collection_types
            )
            # Store all metrics, not just execution_time
            ground_truth[workload_id] = metrics
            
            # Print summary
            exec_time = metrics.get('execution_time', 'N/A')
            if isinstance(exec_time, float):
                print(f"    Execution time: {exec_time:.6f} seconds")
            else:
                print(f"    Execution time: {exec_time}")
            
            # Print additional metrics if available
            if 'cpi' in metrics:
                print(f"    CPI: {metrics['cpi']:.4f}")
            if 'ipc' in metrics:
                print(f"    IPC: {metrics['ipc']:.4f}")
            if 'l1_cache_hit_rate' in metrics:
                print(f"    L1 Cache Hit Rate: {metrics['l1_cache_hit_rate']:.4f}")
            if 'l2_cache_hit_rate' in metrics:
                print(f"    L2 Cache Hit Rate: {metrics['l2_cache_hit_rate']:.4f}")
        
        # Add metadata
        ground_truth['_metadata'] = {
            'source': 'VTune Profiler',
            'collection_method': 'all_collection_types' if use_all_collection_types else 'hotspots',
            'workloads': workload_ids,
            'metrics_collected': list(set(
                key for wl_id, metrics_dict in ground_truth.items()
                if wl_id != '_metadata'
                for key in metrics_dict.keys()
            ))
        }
        
        # Save to file
        if output_file is None:
            output_file = Path(__file__).parent.parent.parent / 'data' / 'results' / 'vtune_ground_truth.json'
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(ground_truth, f, indent=2)
        
        print(f"Ground truth saved to {output_file}")
        print(f"  Collected {len(ground_truth['_metadata']['metrics_collected'])} different metrics")
        
        return ground_truth
