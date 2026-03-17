#!/usr/bin/env python3
"""
System Profiler Module

Extracts actual CPU microarchitecture parameters from the system using
system information tools.
"""

import subprocess
import platform
import re
import json
from pathlib import Path
from typing import Dict, Optional


class SystemProfiler:
    """
    Extracts actual CPU microarchitecture parameters from the system.
    """
    
    def __init__(self):
        """Initialize system profiler."""
        self.system_info = self._get_system_info()
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        return {
            'platform': platform.system(),
            'processor': platform.processor(),
            'machine': platform.machine(),
        }
    
    def extract_cpu_parameters(self) -> Dict[str, int]:
        """
        Extract actual CPU microarchitecture parameters from the system.
        
        Returns:
            Dictionary of actual CPU parameters
        """
        params = {}
        
        # Try to get CPU info from various sources
        if platform.system() == 'Windows':
            params.update(self._extract_windows_cpu_params())
        else:
            params.update(self._extract_linux_cpu_params())
        
        # Map to our parameter space (round to nearest valid value)
        return self._map_to_parameter_space(params)
    
    def _extract_windows_cpu_params(self) -> Dict[str, int]:
        """Extract CPU parameters on Windows."""
        params = {}
        
        try:
            # Try to get CPU info from wmic
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name,numberofcores,numberoflogicalprocessors'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Intel' in line or 'AMD' in line:
                        # Try to extract cache info
                        if 'Cache' in line or 'cache' in line:
                            cache_match = re.search(r'(\d+)\s*[KMGT]?B', line, re.IGNORECASE)
                            if cache_match:
                                cache_size = int(cache_match.group(1))
                                if 'L1' in line or 'l1' in line:
                                    params['l1_cache_size'] = cache_size // 1024  # Convert to KB
                                elif 'L2' in line or 'l2' in line:
                                    params['l2_cache_size'] = cache_size // 1024  # Convert to KB
        except Exception as e:
            print(f"Warning: Could not extract Windows CPU params: {e}")
        
        return params
    
    def _extract_linux_cpu_params(self) -> Dict[str, int]:
        """Extract CPU parameters on Linux."""
        params = {}
        
        try:
            # Prefer sysfs cache info (most reliable on Linux)
            # Example path: /sys/devices/system/cpu/cpu0/cache/index*/{level,type,size}
            cache_root = Path("/sys/devices/system/cpu/cpu0/cache")
            if cache_root.exists():
                for idx_dir in sorted(cache_root.glob("index*")):
                    try:
                        level = (idx_dir / "level").read_text().strip()
                        ctype = (idx_dir / "type").read_text().strip().lower()
                        size_s = (idx_dir / "size").read_text().strip().upper()  # e.g. "32K", "1M"
                        m = re.match(r"^\s*(\d+)\s*([KM])\s*$", size_s)
                        if not m:
                            continue
                        val = int(m.group(1))
                        unit = m.group(2)
                        size_kb = val * (1024 if unit == "M" else 1)

                        if level == "1" and ctype in {"data", "unified"}:
                            # L1 data cache in KB
                            params["l1_cache_size"] = size_kb
                        elif level == "2" and ctype in {"unified", "data"}:
                            params["l2_cache_size"] = size_kb
                        elif level == "3" and ctype in {"unified", "data"}:
                            params["l3_cache_size"] = size_kb
                    except Exception:
                        continue

            # Fallback: /proc/cpuinfo for feature flags (used only for a weak heuristic)
            try:
                cpuinfo = Path("/proc/cpuinfo").read_text().lower()
                if "avx512" in cpuinfo:
                    params["simd_width"] = 512
                elif "avx2" in cpuinfo or "avx" in cpuinfo:
                    params["simd_width"] = 256
                elif "sse" in cpuinfo:
                    params["simd_width"] = 128

                # Issue width is not directly extractable; keep a conservative heuristic.
                if "avx" in cpuinfo or "sse" in cpuinfo:
                    params["issue_width"] = 4
            except Exception:
                pass
        except Exception as e:
            print(f"Warning: Could not extract Linux CPU params: {e}")
        
        return params
    
    
    def _map_to_parameter_space(self, params: Dict[str, int]) -> Dict[str, int]:
        """
        Map extracted parameters to our tunable parameter space.
        
        Rounds values to nearest valid option in our parameter space.
        """
        from .mab_autotuner import TUNABLE_PARAMETERS
        
        # If nothing was extracted, don't fabricate a full set of parameters.
        # Callers should treat {} as "unknown actual parameters".
        if not params:
            return {}

        mapped: Dict[str, int] = {}
        
        # Helper function to find nearest value
        def find_nearest(value: int, options: list) -> int:
            return min(options, key=lambda x: abs(x - value))
        
        # Map only what we can actually infer (avoid defaulting everything).
        if 'rob_size' in params:
            mapped['rob_size'] = find_nearest(params['rob_size'], TUNABLE_PARAMETERS['rob_size'])

        if 'l1_cache_size' in params:
            mapped['l1_cache_size'] = find_nearest(params['l1_cache_size'], TUNABLE_PARAMETERS['l1_cache_size'])

        if 'l2_cache_size' in params:
            mapped['l2_cache_size'] = find_nearest(params['l2_cache_size'], TUNABLE_PARAMETERS['l2_cache_size'])

        if 'issue_width' in params:
            mapped['issue_width'] = find_nearest(params['issue_width'], TUNABLE_PARAMETERS['issue_width'])

        # Latencies/bandwidth/etc. are not reliably extractable here; skip unless provided.
        if 'l1_latency' in params:
            mapped['l1_latency'] = find_nearest(params['l1_latency'], TUNABLE_PARAMETERS['l1_latency'])
        if 'l2_latency' in params:
            mapped['l2_latency'] = find_nearest(params['l2_latency'], TUNABLE_PARAMETERS['l2_latency'])

        if 'l3_cache_size' in params:
            mapped['l3_cache_size'] = find_nearest(params['l3_cache_size'], TUNABLE_PARAMETERS['l3_cache_size'])
        
        if 'l3_latency' in params:
            mapped['l3_latency'] = find_nearest(params['l3_latency'], TUNABLE_PARAMETERS['l3_latency'])
        
        if 'memory_latency' in params:
            mapped['memory_latency'] = find_nearest(params['memory_latency'], TUNABLE_PARAMETERS['memory_latency'])
        
        if 'memory_bandwidth' in params:
            mapped['memory_bandwidth'] = find_nearest(params['memory_bandwidth'], TUNABLE_PARAMETERS['memory_bandwidth'])
        
        if 'branch_predictor_size' in params:
            mapped['branch_predictor_size'] = find_nearest(params['branch_predictor_size'], TUNABLE_PARAMETERS['branch_predictor_size'])
        
        if 'tlb_size' in params:
            mapped['tlb_size'] = find_nearest(params['tlb_size'], TUNABLE_PARAMETERS['tlb_size'])
        
        if 'execution_units' in params:
            mapped['execution_units'] = find_nearest(params['execution_units'], TUNABLE_PARAMETERS['execution_units'])
        
        if 'simd_width' in params:
            mapped['simd_width'] = find_nearest(params['simd_width'], TUNABLE_PARAMETERS['simd_width'])
        
        if 'prefetcher_lines' in params:
            mapped['prefetcher_lines'] = find_nearest(params['prefetcher_lines'], TUNABLE_PARAMETERS['prefetcher_lines'])
        
        if 'smt_threads' in params:
            mapped['smt_threads'] = find_nearest(params['smt_threads'], TUNABLE_PARAMETERS['smt_threads'])
        
        return mapped
    
    def get_actual_parameters(self) -> Dict[str, int]:
        """
        Get actual CPU parameters.
        
        IMPORTANT: This function will NOT fabricate or fall back to "typical"
        CPU parameters if extraction fails. If parameters cannot be extracted,
        it returns an empty dictionary so callers can explicitly detect the
        missing information and avoid reporting fake values.
        
        Returns:
            Dictionary of actual CPU parameters mapped to our parameter space.
            If extraction fails, returns {}.
        """
        try:
            params = self.extract_cpu_parameters()
            # extract_cpu_parameters() already maps into our discrete parameter
            # space and may use reasonable defaults for *missing fields* when
            # some information is available. However, if it ever returns an
            # empty dict, treat that as a complete extraction failure and
            # propagate an empty result instead of fabricating a full config.
            if not params:
                print("Warning: Could not extract any CPU parameters; returning empty actual_parameters.")
                return {}
            return params
        except Exception as e:
            print(f"Warning: Could not extract actual parameters: {e}")
            print("Returning empty actual_parameters; no fallback defaults will be used.")
            return {}
    
    def save_actual_parameters(self, output_file: Path):
        """Save actual parameters to JSON file."""
        params = self.get_actual_parameters()
        data = {
            'actual_parameters': params,
            'system_info': self.system_info,
            'extraction_method': 'system_profiler'
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Actual CPU parameters saved to: {output_file}")
        return params
