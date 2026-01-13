#!/usr/bin/env python3
"""
Script to collect ground truth performance metrics using VTune Profiler.

This script can be run standalone to collect ground truth data before
running the autotuning process.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autotuner.benchmark_runner import BenchmarkRunner
from autotuner.workload_registry import get_all_workloads


def main():
    """Collect ground truth for all workloads."""
    print("=" * 70)
    print("Collecting Ground Truth using Intel VTune Profiler")
    print("=" * 70)
    print()
    
    # Use all workloads by default, or allow command-line arguments
    if len(sys.argv) > 1:
        workloads = sys.argv[1:]
    else:
        workloads = get_all_workloads()
        print(f"Using all {len(workloads)} workloads from registry")
    
    benchmark_runner = BenchmarkRunner()
    
    # Output file
    output_file = Path(__file__).parent.parent / 'data' / 'results' / 'ground_truth.json'
    
    ground_truth = benchmark_runner.collect_ground_truth(
        workloads,
        output_file,
        use_all_collection_types=True
    )
    
    print()
    print("=" * 70)
    print("Ground Truth Collection Complete")
    print("=" * 70)
    print(f"Profiled {len([k for k in ground_truth.keys() if k != '_metadata'])} workloads")
    
    if '_metadata' in ground_truth:
        metrics = ground_truth['_metadata'].get('metrics_collected', [])
        print(f"Metrics collected: {len(metrics)}")
    
    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
