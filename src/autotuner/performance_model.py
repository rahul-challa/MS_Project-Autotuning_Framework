#!/usr/bin/env python3
"""
Performance Model Module

Since we cannot change CPU microarchitecture parameters on real hardware,
this module provides a performance model that estimates execution time
based on CPU configuration parameters. The model parameters are tuned
to match VTune-measured ground truth.
"""

import numpy as np
from typing import Dict


class PerformanceModel:
    """
    Performance model that estimates execution time based on CPU parameters.
    
    The model uses a simplified analytical approach to estimate how different
    CPU configurations would affect performance, based on:
    - Cache hit/miss rates (affected by cache size)
    - Instruction throughput (affected by issue width and ROB size)
    - Memory latency penalties (affected by cache latencies)
    """
    
    def __init__(self, base_execution_time: float = 1.0):
        """
        Initialize performance model.
        
        Args:
            base_execution_time: Base execution time in seconds
        """
        self.base_execution_time = base_execution_time
        
        # Model parameters (tuned to match real CPU behavior)
        self.rob_impact = 0.50  # Impact of ROB size on performance
        self.rob_baseline = 128
        
        self.width_impact = 0.40  # Impact of issue width
        self.width_baseline = 4
        
        self.l1_size_impact = 0.60  # Impact of L1 cache size
        self.l1_size_baseline = 64  # KB
        
        self.l1_latency_impact = 0.20  # Impact of L1 latency
        self.l1_latency_baseline = 3  # cycles
        
        self.l2_size_impact = 0.50  # Impact of L2 cache size
        self.l2_size_baseline = 256  # KB
        
        self.l2_latency_impact = 0.25  # Impact of L2 latency
        self.l2_latency_baseline = 12  # cycles
    
    def estimate_execution_time(self, ap: Dict[str, int]) -> float:
        """
        Estimate execution time for a given parameter assignment.
        
        Args:
            ap: Parameter assignment dictionary with:
                - rob_size: Reorder Buffer size
                - l1_cache_size: L1 cache size in KB
                - l2_cache_size: L2 cache size in KB
                - issue_width: Issue width
                - l1_latency: L1 cache access latency in cycles
                - l2_latency: L2 cache access latency in cycles
        
        Returns:
            Estimated execution time in seconds
        """
        scaled_time = self.base_execution_time
        
        # ROB size effect (larger ROB = better performance, fewer cycles)
        rob_factor = self.rob_baseline / ap['rob_size']
        scaled_time = scaled_time * (1 + self.rob_impact * (rob_factor - 1))
        
        # Issue width effect (wider issue = better performance)
        width_factor = self.width_baseline / ap['issue_width']
        scaled_time = scaled_time * (1 + self.width_impact * (width_factor - 1))
        
        # L1 cache size effect
        if ap['l1_cache_size'] < self.l1_size_baseline:
            l1_factor = (self.l1_size_baseline - ap['l1_cache_size']) / self.l1_size_baseline
            scaled_time = scaled_time * (1 + self.l1_size_impact * l1_factor)
        elif ap['l1_cache_size'] > self.l1_size_baseline:
            l1_factor = (ap['l1_cache_size'] - self.l1_size_baseline) / self.l1_size_baseline
            scaled_time = scaled_time * (1 - 0.45 * l1_factor)  # Diminishing returns
        
        # L1 latency effect (higher latency = more time)
        l1_latency_factor = ap['l1_latency'] / self.l1_latency_baseline
        scaled_time = scaled_time * (1 + self.l1_latency_impact * (l1_latency_factor - 1))
        
        # L2 cache size effect
        if ap['l2_cache_size'] < self.l2_size_baseline:
            l2_factor = (self.l2_size_baseline - ap['l2_cache_size']) / self.l2_size_baseline
            scaled_time = scaled_time * (1 + self.l2_size_impact * l2_factor)
        elif ap['l2_cache_size'] > self.l2_size_baseline:
            l2_factor = (ap['l2_cache_size'] - self.l2_size_baseline) / self.l2_size_baseline
            scaled_time = scaled_time * (1 - 0.35 * l2_factor)  # Diminishing returns
        
        # L2 latency effect (higher latency = more time)
        l2_latency_factor = ap['l2_latency'] / self.l2_latency_baseline
        scaled_time = scaled_time * (1 + self.l2_latency_impact * (l2_latency_factor - 1))
        
        return max(scaled_time, 0.001)  # Ensure positive time
    
    def estimate_all_metrics(self, ap: Dict[str, int], base_metrics: Dict[str, float] = None) -> Dict[str, float]:
        """
        Estimate all performance metrics for a given parameter assignment.
        
        Args:
            ap: Parameter assignment dictionary
            base_metrics: Base metrics dictionary (if None, uses execution_time only)
        
        Returns:
            Dictionary of estimated metrics
        """
        if base_metrics is None:
            base_metrics = {'execution_time': self.base_execution_time}
        
        estimated = {}
        
        # Estimate execution time
        estimated['execution_time'] = self.estimate_execution_time(ap)
        
        # Estimate CPI (Cycles Per Instruction)
        # Larger ROB and wider issue width reduce CPI
        base_cpi = base_metrics.get('cpi', 1.5)  # Default CPI
        rob_cpi_factor = self.rob_baseline / ap['rob_size']
        width_cpi_factor = self.width_baseline / ap['issue_width']
        estimated['cpi'] = base_cpi * (1 + 0.3 * (rob_cpi_factor - 1) + 0.2 * (width_cpi_factor - 1))
        
        # Estimate IPC (Instructions Per Cycle) = 1 / CPI
        estimated['ipc'] = 1.0 / estimated['cpi'] if estimated['cpi'] > 0 else 1.0
        
        # Estimate cache hit rates based on cache sizes
        base_l1_hit_rate = base_metrics.get('l1_cache_hit_rate', 0.95)
        l1_size_factor = ap['l1_cache_size'] / self.l1_size_baseline
        estimated['l1_cache_hit_rate'] = min(0.99, base_l1_hit_rate * (1 + 0.1 * (l1_size_factor - 1)))
        estimated['l1_cache_miss_rate'] = 1.0 - estimated['l1_cache_hit_rate']
        
        base_l2_hit_rate = base_metrics.get('l2_cache_hit_rate', 0.85)
        l2_size_factor = ap['l2_cache_size'] / self.l2_size_baseline
        estimated['l2_cache_hit_rate'] = min(0.95, base_l2_hit_rate * (1 + 0.15 * (l2_size_factor - 1)))
        estimated['l2_cache_miss_rate'] = 1.0 - estimated['l2_cache_hit_rate']
        
        # Estimate branch misprediction rate (affected by ROB size)
        base_branch_mispred_rate = base_metrics.get('branch_misprediction_rate', 0.05)
        rob_branch_factor = self.rob_baseline / ap['rob_size']
        estimated['branch_misprediction_rate'] = base_branch_mispred_rate * (1 + 0.2 * (rob_branch_factor - 1))
        estimated['branch_prediction_accuracy'] = 1.0 - estimated['branch_misprediction_rate']
        
        # Copy other metrics from base if available
        for key in ['cpu_utilization', 'memory_bandwidth', 'instructions_retired', 'cpu_clocks']:
            if key in base_metrics:
                estimated[key] = base_metrics[key]
        
        return estimated
    
    def set_base_execution_time(self, base_time: float):
        """Set the base execution time for the model."""
        self.base_execution_time = base_time
    
    def calibrate(self, ground_truth: Dict[str, float], workload_configs: Dict[str, Dict[str, int]]):
        """
        Calibrate model parameters to match ground truth measurements.
        
        This is a simplified calibration - in practice, you might use
        more sophisticated optimization techniques.
        
        Args:
            ground_truth: Dictionary mapping workload_id to execution time
            workload_configs: Dictionary mapping workload_id to parameter config
        """
        # Simple calibration: adjust base execution time to match average
        if ground_truth:
            avg_ground_truth = np.mean([v for k, v in ground_truth.items() if k != '_metadata'])
            self.base_execution_time = avg_ground_truth
