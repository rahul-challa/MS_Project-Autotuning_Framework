#!/usr/bin/env python3
"""
Enhanced Performance Model

A more accurate performance model with:
1. Higher sensitivity to parameter changes
2. Better calibration from ground truth
3. More accurate metric estimation
4. Workload-specific parameter impacts
"""

import numpy as np
from typing import Dict, Optional
from .performance_model import PerformanceModel


class EnhancedPerformanceModel(PerformanceModel):
    """
    Enhanced performance model with better parameter sensitivity and calibration.
    """
    
    def __init__(self, base_execution_time: float = 1.0):
        """Initialize enhanced performance model."""
        super().__init__(base_execution_time)
        
        # INCREASED impact factors for better parameter distinction
        self.rob_impact = 0.80  # Increased from 0.50 - ROB has strong impact
        self.width_impact = 0.70  # Increased from 0.40 - Issue width is critical
        self.l1_size_impact = 0.85  # Increased from 0.60 - L1 cache is very important
        self.l1_latency_impact = 0.40  # Increased from 0.20 - Latency matters more
        self.l2_size_impact = 0.75  # Increased from 0.50 - L2 cache is important
        self.l2_latency_impact = 0.50  # Increased from 0.25 - L2 latency has significant impact
        
        # Workload-specific characteristics
        self.workload_characteristics = {}
    
    def estimate_execution_time(self, ap: Dict[str, int], workload_id: Optional[str] = None) -> float:
        """
        Enhanced execution time estimation with higher sensitivity.
        
        Args:
            ap: Parameter assignment
            workload_id: Optional workload ID for workload-specific adjustments
        """
        scaled_time = self.base_execution_time
        
        # Workload-specific adjustments
        workload_multipliers = {
            'rob_impact': 1.0,
            'width_impact': 1.0,
            'l1_size_impact': 1.0,
            'l2_size_impact': 1.0,
        }
        
        if workload_id:
            # Matrix/memory workloads: cache matters more
            if 'matrix' in workload_id or 'memory' in workload_id or 'cache' in workload_id:
                workload_multipliers['l1_size_impact'] = 1.3
                workload_multipliers['l2_size_impact'] = 1.3
            # Branch workloads: ROB matters more
            elif 'branch' in workload_id:
                workload_multipliers['rob_impact'] = 1.3
            # Compute workloads: issue width matters more
            elif 'compute' in workload_id or 'vector' in workload_id:
                workload_multipliers['width_impact'] = 1.3
        
        # ROB size effect - STRONGER impact (with workload adjustment)
        # Larger ROB = better instruction-level parallelism = better performance
        rob_impact_adj = self.rob_impact * workload_multipliers['rob_impact']
        rob_ratio = ap['rob_size'] / self.rob_baseline
        if rob_ratio < 1.0:
            # Smaller ROB = worse performance (more stalls)
            scaled_time = scaled_time * (1 + rob_impact_adj * (1 - rob_ratio))
        else:
            # Larger ROB = better performance (diminishing returns)
            scaled_time = scaled_time * (1 - 0.6 * rob_impact_adj * (rob_ratio - 1) / rob_ratio)
        
        # Issue width effect - STRONGER impact (with workload adjustment)
        # Wider issue = more instructions per cycle = better performance
        width_impact_adj = self.width_impact * workload_multipliers['width_impact']
        width_ratio = ap['issue_width'] / self.width_baseline
        if width_ratio < 1.0:
            # Narrower issue = worse performance
            scaled_time = scaled_time * (1 + width_impact_adj * (1 - width_ratio))
        else:
            # Wider issue = better performance (diminishing returns)
            scaled_time = scaled_time * (1 - 0.7 * width_impact_adj * (width_ratio - 1) / width_ratio)
        
        # L1 cache size effect - STRONGER impact (with workload adjustment)
        l1_impact_adj = self.l1_size_impact * workload_multipliers['l1_size_impact']
        l1_ratio = ap['l1_cache_size'] / self.l1_size_baseline
        if l1_ratio < 1.0:
            # Smaller L1 = more misses = worse performance
            miss_penalty = (1 - l1_ratio) ** 1.5  # Non-linear penalty
            scaled_time = scaled_time * (1 + l1_impact_adj * miss_penalty)
        else:
            # Larger L1 = fewer misses = better performance
            hit_benefit = (l1_ratio - 1) / (1 + 0.5 * (l1_ratio - 1))
            scaled_time = scaled_time * (1 - 0.5 * l1_impact_adj * hit_benefit)
        
        # L1 latency effect - STRONGER impact
        l1_lat_ratio = ap['l1_latency'] / self.l1_latency_baseline
        scaled_time = scaled_time * (1 + self.l1_latency_impact * (l1_lat_ratio - 1))
        
        # L2 cache size effect - STRONGER impact (with workload adjustment)
        l2_impact_adj = self.l2_size_impact * workload_multipliers['l2_size_impact']
        l2_ratio = ap['l2_cache_size'] / self.l2_size_baseline
        if l2_ratio < 1.0:
            # Smaller L2 = more L2 misses = worse performance
            miss_penalty = (1 - l2_ratio) ** 1.3  # Non-linear penalty
            scaled_time = scaled_time * (1 + l2_impact_adj * miss_penalty)
        else:
            # Larger L2 = fewer misses = better performance
            hit_benefit = (l2_ratio - 1) / (1 + 0.4 * (l2_ratio - 1))
            scaled_time = scaled_time * (1 - 0.4 * l2_impact_adj * hit_benefit)
        
        # L2 latency effect - STRONGER impact
        l2_lat_ratio = ap['l2_latency'] / self.l2_latency_baseline
        scaled_time = scaled_time * (1 + self.l2_latency_impact * (l2_lat_ratio - 1))
        
        # L3 cache size effect (if available)
        if 'l3_cache_size' in ap:
            l3_baseline = 2048  # KB
            l3_impact = 0.60
            l3_ratio = ap['l3_cache_size'] / l3_baseline
            if l3_ratio < 1.0:
                miss_penalty = (1 - l3_ratio) ** 1.2
                scaled_time = scaled_time * (1 + l3_impact * miss_penalty)
            else:
                hit_benefit = (l3_ratio - 1) / (1 + 0.3 * (l3_ratio - 1))
                scaled_time = scaled_time * (1 - 0.3 * l3_impact * hit_benefit)
        
        # L3 latency effect (if available)
        if 'l3_latency' in ap:
            l3_lat_baseline = 40
            l3_lat_impact = 0.35
            l3_lat_ratio = ap['l3_latency'] / l3_lat_baseline
            scaled_time = scaled_time * (1 + l3_lat_impact * (l3_lat_ratio - 1))
        
        # Memory latency effect (if available)
        if 'memory_latency' in ap:
            mem_lat_baseline = 200
            mem_lat_impact = 0.45
            mem_lat_ratio = ap['memory_latency'] / mem_lat_baseline
            scaled_time = scaled_time * (1 + mem_lat_impact * (mem_lat_ratio - 1))
        
        # Memory bandwidth effect (if available)
        if 'memory_bandwidth' in ap:
            mem_bw_baseline = 25  # GB/s
            mem_bw_impact = 0.50
            mem_bw_ratio = mem_bw_baseline / ap['memory_bandwidth']  # Inverse: higher BW = better
            if mem_bw_ratio > 1.0:
                scaled_time = scaled_time * (1 + mem_bw_impact * (mem_bw_ratio - 1))
            else:
                scaled_time = scaled_time * (1 - 0.4 * mem_bw_impact * (1 - mem_bw_ratio))
        
        # Branch predictor size effect (if available)
        if 'branch_predictor_size' in ap:
            bp_baseline = 4096
            bp_impact = 0.30
            bp_ratio = ap['branch_predictor_size'] / bp_baseline
            if bp_ratio < 1.0:
                scaled_time = scaled_time * (1 + bp_impact * (1 - bp_ratio))
            else:
                scaled_time = scaled_time * (1 - 0.2 * bp_impact * (bp_ratio - 1) / bp_ratio)
        
        # TLB size effect (if available)
        if 'tlb_size' in ap:
            tlb_baseline = 512
            tlb_impact = 0.25
            tlb_ratio = ap['tlb_size'] / tlb_baseline
            if tlb_ratio < 1.0:
                scaled_time = scaled_time * (1 + tlb_impact * (1 - tlb_ratio))
            else:
                scaled_time = scaled_time * (1 - 0.15 * tlb_impact * (tlb_ratio - 1) / tlb_ratio)
        
        # Execution units effect (if available)
        if 'execution_units' in ap:
            eu_baseline = 4
            eu_impact = 0.40
            eu_ratio = ap['execution_units'] / eu_baseline
            if eu_ratio < 1.0:
                scaled_time = scaled_time * (1 + eu_impact * (1 - eu_ratio))
            else:
                scaled_time = scaled_time * (1 - 0.5 * eu_impact * (eu_ratio - 1) / eu_ratio)
        
        # SIMD width effect (if available)
        if 'simd_width' in ap:
            simd_baseline = 256  # bits
            simd_impact = 0.35
            simd_ratio = ap['simd_width'] / simd_baseline
            if simd_ratio < 1.0:
                scaled_time = scaled_time * (1 + simd_impact * (1 - simd_ratio))
            else:
                scaled_time = scaled_time * (1 - 0.4 * simd_impact * (simd_ratio - 1) / simd_ratio)
        
        # Prefetcher effect (if available)
        if 'prefetcher_lines' in ap:
            pref_baseline = 16
            pref_impact = 0.20
            pref_ratio = ap['prefetcher_lines'] / pref_baseline
            if pref_ratio < 1.0:
                scaled_time = scaled_time * (1 + pref_impact * (1 - pref_ratio))
            else:
                scaled_time = scaled_time * (1 - 0.15 * pref_impact * (pref_ratio - 1) / pref_ratio)
        
        # SMT threads effect (if available) - more threads can help or hurt depending on workload
        if 'smt_threads' in ap:
            smt_baseline = 2
            smt_impact = 0.15  # Lower impact, can be positive or negative
            smt_ratio = ap['smt_threads'] / smt_baseline
            # SMT can help with memory-bound workloads but hurt compute-bound
            if workload_id and ('memory' in workload_id or 'cache' in workload_id):
                # Memory-bound: SMT helps
                if smt_ratio > 1.0:
                    scaled_time = scaled_time * (1 - 0.2 * smt_impact * (smt_ratio - 1))
            else:
                # Compute-bound: SMT can hurt
                if smt_ratio > 1.0:
                    scaled_time = scaled_time * (1 + 0.1 * smt_impact * (smt_ratio - 1))
        
        return max(scaled_time, 0.001)  # Ensure positive time
    
    def estimate_all_metrics(self, ap: Dict[str, int], base_metrics: Dict[str, float] = None, workload_id: Optional[str] = None) -> Dict[str, float]:
        """
        Enhanced metric estimation with better parameter sensitivity.
        
        Args:
            ap: Parameter assignment
            base_metrics: Base metrics dictionary
            workload_id: Optional workload ID for workload-specific adjustments
        """
        if base_metrics is None:
            base_metrics = {'execution_time': self.base_execution_time}
        
        estimated = {}
        
        # Estimate execution time (with workload-specific adjustments if available)
        estimated['execution_time'] = self.estimate_execution_time(ap, workload_id)
        
        # Enhanced CPI estimation - more sensitive to ROB and issue width
        base_cpi = base_metrics.get('cpi', 1.5)
        rob_ratio = ap['rob_size'] / self.rob_baseline
        width_ratio = ap['issue_width'] / self.width_baseline
        
        # CPI improves with larger ROB and wider issue width
        cpi_factor = 1.0
        if rob_ratio < 1.0:
            cpi_factor += 0.5 * (1 - rob_ratio)  # Smaller ROB = higher CPI
        else:
            cpi_factor -= 0.3 * (rob_ratio - 1) / rob_ratio  # Larger ROB = lower CPI
        
        if width_ratio < 1.0:
            cpi_factor += 0.4 * (1 - width_ratio)  # Narrower issue = higher CPI
        else:
            cpi_factor -= 0.3 * (width_ratio - 1) / width_ratio  # Wider issue = lower CPI
        
        estimated['cpi'] = base_cpi * cpi_factor
        estimated['ipc'] = 1.0 / estimated['cpi'] if estimated['cpi'] > 0 else 1.0
        
        # Enhanced cache hit rate estimation - more sensitive to cache sizes
        base_l1_hit_rate = base_metrics.get('l1_cache_hit_rate', 0.95)
        l1_ratio = ap['l1_cache_size'] / self.l1_size_baseline
        
        # Hit rate improves with cache size (non-linear)
        if l1_ratio < 1.0:
            hit_rate_factor = l1_ratio ** 0.8  # Stronger penalty for smaller cache
        else:
            hit_rate_factor = 1.0 + 0.15 * (l1_ratio - 1) / (1 + 0.3 * (l1_ratio - 1))
        
        estimated['l1_cache_hit_rate'] = min(0.99, base_l1_hit_rate * hit_rate_factor)
        estimated['l1_cache_miss_rate'] = 1.0 - estimated['l1_cache_hit_rate']
        
        base_l2_hit_rate = base_metrics.get('l2_cache_hit_rate', 0.85)
        l2_ratio = ap['l2_cache_size'] / self.l2_size_baseline
        
        if l2_ratio < 1.0:
            hit_rate_factor = l2_ratio ** 0.7  # Stronger penalty for smaller cache
        else:
            hit_rate_factor = 1.0 + 0.20 * (l2_ratio - 1) / (1 + 0.25 * (l2_ratio - 1))
        
        estimated['l2_cache_hit_rate'] = min(0.95, base_l2_hit_rate * hit_rate_factor)
        estimated['l2_cache_miss_rate'] = 1.0 - estimated['l2_cache_hit_rate']
        
        # Enhanced branch prediction - more sensitive to ROB size
        base_branch_mispred_rate = base_metrics.get('branch_misprediction_rate', 0.05)
        rob_ratio = ap['rob_size'] / self.rob_baseline
        
        # Larger ROB = better branch prediction (more history)
        if rob_ratio < 1.0:
            mispred_factor = 1.0 + 0.4 * (1 - rob_ratio)  # Smaller ROB = more mispredictions
        else:
            mispred_factor = 1.0 - 0.2 * (rob_ratio - 1) / rob_ratio  # Larger ROB = fewer mispredictions
        
        estimated['branch_misprediction_rate'] = base_branch_mispred_rate * mispred_factor
        estimated['branch_prediction_accuracy'] = 1.0 - estimated['branch_misprediction_rate']
        
        # L3 cache metrics (if available)
        if 'l3_cache_size' in ap:
            l3_baseline = 2048
            base_l3_hit_rate = base_metrics.get('l3_cache_hit_rate', 0.70)
            l3_ratio = ap['l3_cache_size'] / l3_baseline
            if l3_ratio < 1.0:
                hit_rate_factor = l3_ratio ** 0.6
            else:
                hit_rate_factor = 1.0 + 0.25 * (l3_ratio - 1) / (1 + 0.2 * (l3_ratio - 1))
            estimated['l3_cache_hit_rate'] = min(0.90, base_l3_hit_rate * hit_rate_factor)
            estimated['l3_cache_miss_rate'] = 1.0 - estimated['l3_cache_hit_rate']
        
        # Memory bandwidth estimation (if parameter available)
        if 'memory_bandwidth' in ap:
            base_mem_bw = base_metrics.get('memory_bandwidth', 25.0)
            mem_bw_ratio = ap['memory_bandwidth'] / 25.0
            estimated['memory_bandwidth'] = base_mem_bw * mem_bw_ratio
        
        # Branch prediction accuracy (enhanced with branch predictor size)
        if 'branch_predictor_size' in ap:
            bp_baseline = 4096
            bp_ratio = ap['branch_predictor_size'] / bp_baseline
            if bp_ratio < 1.0:
                accuracy_factor = bp_ratio ** 0.5
            else:
                accuracy_factor = 1.0 + 0.1 * (bp_ratio - 1) / (1 + 0.2 * (bp_ratio - 1))
            estimated['branch_prediction_accuracy'] = min(0.99, estimated.get('branch_prediction_accuracy', 0.95) * accuracy_factor)
            estimated['branch_misprediction_rate'] = 1.0 - estimated['branch_prediction_accuracy']
        
        # TLB hit rate (if available)
        if 'tlb_size' in ap:
            tlb_baseline = 512
            base_tlb_hit_rate = base_metrics.get('tlb_hit_rate', 0.98)
            tlb_ratio = ap['tlb_size'] / tlb_baseline
            if tlb_ratio < 1.0:
                hit_rate_factor = tlb_ratio ** 0.3
            else:
                hit_rate_factor = 1.0 + 0.05 * (tlb_ratio - 1) / (1 + 0.1 * (tlb_ratio - 1))
            estimated['tlb_hit_rate'] = min(0.995, base_tlb_hit_rate * hit_rate_factor)
            estimated['tlb_miss_rate'] = 1.0 - estimated['tlb_hit_rate']
        
        # Copy other metrics from base if available
        for key in ['cpu_utilization', 'instructions_retired', 'cpu_clocks']:
            if key in base_metrics:
                estimated[key] = base_metrics[key]
        
        return estimated
    
    def calibrate_from_ground_truth(self, ground_truth: Dict[str, Dict[str, float]]):
        """
        Calibrate model parameters based on ground truth data.
        
        This adjusts the model to better match observed performance patterns.
        """
        if not ground_truth:
            return
        
        # Calculate average execution times
        exec_times = []
        for metrics in ground_truth.values():
            if isinstance(metrics, dict) and 'execution_time' in metrics:
                exec_times.append(metrics['execution_time'])
        
        if exec_times:
            avg_time = np.mean(exec_times)
            self.base_execution_time = avg_time
            
            # Adjust impact factors based on variance in execution times
            # Higher variance = parameters have stronger impact
            if len(exec_times) > 1:
                variance = np.var(exec_times)
                std_dev = np.std(exec_times)
                cv = std_dev / avg_time if avg_time > 0 else 0  # Coefficient of variation
                
                # If workloads have high variance, parameters matter more
                if cv > 0.5:  # High coefficient of variation
                    # Increase impact factors significantly
                    self.rob_impact = min(1.0, self.rob_impact * 1.2)
                    self.width_impact = min(1.0, self.width_impact * 1.2)
                    self.l1_size_impact = min(1.0, self.l1_size_impact * 1.2)
                    self.l2_size_impact = min(1.0, self.l2_size_impact * 1.15)
                    self.l1_latency_impact = min(1.0, self.l1_latency_impact * 1.3)
                    self.l2_latency_impact = min(1.0, self.l2_latency_impact * 1.3)
                
                # Analyze cache metrics if available
                cache_metrics_found = False
                for metrics in ground_truth.values():
                    if isinstance(metrics, dict):
                        if 'l1_cache_hit_rate' in metrics or 'l2_cache_hit_rate' in metrics:
                            cache_metrics_found = True
                            break
                
                if cache_metrics_found:
                    # Cache metrics available - increase cache impact
                    self.l1_size_impact = min(1.0, self.l1_size_impact * 1.15)
                    self.l2_size_impact = min(1.0, self.l2_size_impact * 1.15)
