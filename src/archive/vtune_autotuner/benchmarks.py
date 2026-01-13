#!/usr/bin/env python3
"""
Benchmark Workloads Generator

Creates various CPU benchmark workloads for testing and characterization.
These workloads exercise different aspects of CPU performance:
- Computational intensity
- Memory access patterns
- Cache behavior
- Branch prediction
"""

import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Callable
import tempfile
import subprocess
import platform


class BenchmarkWorkload:
    """Represents a single benchmark workload."""
    
    def __init__(self, workload_id: str, function: Callable, description: str):
        self.workload_id = workload_id
        self.function = function
        self.description = description
    
    def run(self, *args, **kwargs):
        """Run the workload."""
        return self.function(*args, **kwargs)


class BenchmarkWorkloads:
    """Collection of benchmark workloads for CPU characterization."""
    
    def __init__(self):
        self.workloads = {}
        self._register_workloads()
    
    def _register_workloads(self):
        """Register all available benchmark workloads."""
        
        # Matrix multiplication - CPU intensive, cache-friendly
        self.workloads["w1_matrix_mult"] = BenchmarkWorkload(
            "w1_matrix_mult",
            self._matrix_multiply,
            "Matrix multiplication - CPU intensive, good cache locality"
        )
        
        # Bubble sort - CPU intensive, poor cache locality
        self.workloads["w2_bubble_sort"] = BenchmarkWorkload(
            "w2_bubble_sort",
            self._bubble_sort,
            "Bubble sort - CPU intensive, random memory access"
        )
        
        # FFT calculation - Mixed workload
        self.workloads["w3_fft_calc"] = BenchmarkWorkload(
            "w3_fft_calc",
            self._fft_calculation,
            "FFT calculation - Mixed computational and memory workload"
        )
        
        # Memory bandwidth test
        self.workloads["w4_memory_bandwidth"] = BenchmarkWorkload(
            "w4_memory_bandwidth",
            self._memory_bandwidth,
            "Memory bandwidth test - Sequential memory access"
        )
        
        # Random memory access
        self.workloads["w5_random_access"] = BenchmarkWorkload(
            "w5_random_access",
            self._random_memory_access,
            "Random memory access - Cache unfriendly"
        )
        
        # Branch prediction test
        self.workloads["w6_branch_intensive"] = BenchmarkWorkload(
            "w6_branch_intensive",
            self._branch_intensive,
            "Branch prediction test - Many conditional branches"
        )
        
        # Prime number calculation
        self.workloads["w7_prime_calc"] = BenchmarkWorkload(
            "w7_prime_calc",
            self._prime_calculation,
            "Prime number calculation - Integer arithmetic intensive"
        )
    
    def _matrix_multiply(self, size: int = 500):
        """Matrix multiplication workload."""
        np.random.seed(42)
        A = np.random.rand(size, size).astype(np.float64)
        B = np.random.rand(size, size).astype(np.float64)
        C = np.dot(A, B)
        return C.sum()
    
    def _bubble_sort(self, size: int = 10000):
        """Bubble sort workload."""
        np.random.seed(42)
        arr = np.random.randint(0, 1000000, size).tolist()
        
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        
        return sum(arr)
    
    def _fft_calculation(self, size: int = 100000):
        """FFT calculation workload."""
        np.random.seed(42)
        data = np.random.rand(size) + 1j * np.random.rand(size)
        result = np.fft.fft(data)
        return np.abs(result).sum()
    
    def _memory_bandwidth(self, size: int = 10000000):
        """Memory bandwidth test."""
        arr1 = np.ones(size, dtype=np.float64)
        arr2 = np.ones(size, dtype=np.float64)
        arr3 = arr1 + arr2
        return arr3.sum()
    
    def _random_memory_access(self, size: int = 1000000):
        """Random memory access pattern."""
        np.random.seed(42)
        indices = np.random.permutation(size)
        arr = np.arange(size, dtype=np.int64)
        result = 0
        for idx in indices[:100000]:  # Limit iterations
            result += arr[idx]
        return result
    
    def _branch_intensive(self, size: int = 10000000):
        """Branch prediction intensive workload."""
        np.random.seed(42)
        arr = np.random.randint(0, 100, size)
        result = 0
        for val in arr:
            if val < 50:
                result += val * 2
            else:
                result += val
        return result
    
    def _prime_calculation(self, limit: int = 100000):
        """Prime number calculation."""
        primes = []
        for num in range(2, limit):
            is_prime = True
            for i in range(2, int(num ** 0.5) + 1):
                if num % i == 0:
                    is_prime = False
                    break
            if is_prime:
                primes.append(num)
        return sum(primes)
    
    def create_benchmark_executable(self, workload_id: str, output_dir: Path) -> Path:
        """
        Create a standalone Python script for a benchmark workload.
        
        Args:
            workload_id: ID of the workload to create
            output_dir: Directory to save the script
            
        Returns:
            Path to the created script
        """
        if workload_id not in self.workloads:
            raise ValueError(f"Unknown workload: {workload_id}")
        
        workload = self.workloads[workload_id]
        
        # Create Python script
        script_content = f'''#!/usr/bin/env python3
"""
Benchmark workload: {workload.description}
Workload ID: {workload_id}
"""

import numpy as np
import sys

def matrix_multiply(size=500):
    np.random.seed(42)
    A = np.random.rand(size, size).astype(np.float64)
    B = np.random.rand(size, size).astype(np.float64)
    C = np.dot(A, B)
    return C.sum()

def bubble_sort(size=10000):
    np.random.seed(42)
    arr = np.random.randint(0, 1000000, size).tolist()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return sum(arr)

def fft_calculation(size=100000):
    np.random.seed(42)
    data = np.random.rand(size) + 1j * np.random.rand(size)
    result = np.fft.fft(data)
    return np.abs(result).sum()

def memory_bandwidth(size=10000000):
    arr1 = np.ones(size, dtype=np.float64)
    arr2 = np.ones(size, dtype=np.float64)
    arr3 = arr1 + arr2
    return arr3.sum()

def random_memory_access(size=1000000):
    np.random.seed(42)
    indices = np.random.permutation(size)
    arr = np.arange(size, dtype=np.int64)
    result = 0
    for idx in indices[:100000]:
        result += arr[idx]
    return result

def branch_intensive(size=10000000):
    np.random.seed(42)
    arr = np.random.randint(0, 100, size)
    result = 0
    for val in arr:
        if val < 50:
            result += val * 2
        else:
            result += val
    return result

def prime_calculation(limit=100000):
    primes = []
    for num in range(2, limit):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return sum(primes)

if __name__ == "__main__":
    workload_id = "{workload_id}"
    
    if workload_id == "w1_matrix_mult":
        result = matrix_multiply()
    elif workload_id == "w2_bubble_sort":
        result = bubble_sort()
    elif workload_id == "w3_fft_calc":
        result = fft_calculation()
    elif workload_id == "w4_memory_bandwidth":
        result = memory_bandwidth()
    elif workload_id == "w5_random_access":
        result = random_memory_access()
    elif workload_id == "w6_branch_intensive":
        result = branch_intensive()
    elif workload_id == "w7_prime_calc":
        result = prime_calculation()
    else:
        print(f"Unknown workload: {{workload_id}}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Result: {{result}}")
'''
        
        output_dir.mkdir(parents=True, exist_ok=True)
        script_path = output_dir / f"{workload_id}.py"
        script_path.write_text(script_content)
        
        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            import stat
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
        
        return script_path
    
    def get_workload_ids(self) -> List[str]:
        """Get list of all workload IDs."""
        return list(self.workloads.keys())
    
    def run_workload(self, workload_id: str, *args, **kwargs):
        """Run a specific workload."""
        if workload_id not in self.workloads:
            raise ValueError(f"Unknown workload: {workload_id}")
        return self.workloads[workload_id].run(*args, **kwargs)
    
    def get_ground_truth(self, iterations: int = 3) -> Dict[str, float]:
        """
        Run all workloads to get baseline execution times (ground truth).
        
        Args:
            iterations: Number of iterations to average
            
        Returns:
            Dictionary mapping workload_id to average execution time in seconds
        """
        ground_truth = {}
        
        print("Generating ground truth execution times...")
        for workload_id in self.get_workload_ids():
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                self.run_workload(workload_id)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            
            avg_time = sum(times) / len(times)
            ground_truth[workload_id] = avg_time
            print(f"  {workload_id}: {avg_time:.6f}s (avg of {iterations} runs)")
        
        return ground_truth
    
    def save_ground_truth(self, output_file: str = "ground_truth.json", iterations: int = 3):
        """Save ground truth to JSON file."""
        gt = self.get_ground_truth(iterations)
        with open(output_file, 'w') as f:
            json.dump(gt, f, indent=2)
        print(f"Ground truth saved to {output_file}")
        return gt


if __name__ == "__main__":
    workloads = BenchmarkWorkloads()
    
    # Create benchmark scripts
    output_dir = Path("benchmarks")
    print("Creating benchmark scripts...")
    for workload_id in workloads.get_workload_ids():
        script_path = workloads.create_benchmark_executable(workload_id, output_dir)
        print(f"  Created: {script_path}")
    
    # Generate ground truth
    workloads.save_ground_truth()
