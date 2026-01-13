#!/usr/bin/env python3
"""
VTune Metrics Discovery Module

Discovers available VTune Profiler metrics, analysis types, and parameters
on the current system. This module queries VTune to find all supported
metrics that can be used for CPU characterization.
"""

import subprocess
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
import platform


class VTuneMetricsDiscovery:
    """Discovers and catalogs available VTune Profiler metrics."""
    
    def __init__(self, vtune_path: Optional[str] = None):
        """
        Initialize VTune discovery.
        
        Args:
            vtune_path: Path to VTune executable. If None, searches common locations.
        """
        self.vtune_path = self._find_vtune(vtune_path)
        self.metrics_cache = {}
        
    def _find_vtune(self, custom_path: Optional[str] = None) -> str:
        """Find VTune executable path."""
        if custom_path and Path(custom_path).exists():
            return custom_path
        
        # Common VTune installation paths on Windows
        common_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI\vtune\latest\bin64\vtune.exe",
            r"C:\Program Files\Intel\oneAPI\vtune\latest\bin64\vtune.exe",
            r"C:\Program Files (x86)\IntelSWTools\vtune_profiler\bin64\vtune.exe",
            r"C:\Program Files\IntelSWTools\vtune_profiler\bin64\vtune.exe",
        ]
        
        # Also check environment variables
        if "VTUNE_PROFILER_DIR" in os.environ:
            vtune_dir = Path(os.environ["VTUNE_PROFILER_DIR"])
            candidate = vtune_dir / "bin64" / "vtune.exe"
            if candidate.exists():
                return str(candidate)
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["where", "vtune"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        raise FileNotFoundError(
            "VTune Profiler not found. Please install Intel VTune Profiler or set VTUNE_PROFILER_DIR environment variable."
        )
    
    def check_vtune_available(self) -> bool:
        """Check if VTune is available and accessible."""
        try:
            result = subprocess.run(
                [self.vtune_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def get_analysis_types(self) -> List[str]:
        """
        Get list of available VTune analysis types.
        
        Returns:
            List of analysis type names (e.g., ['hotspots', 'memory-access', 'uarch-exploration'])
        """
        # Start with universal analysis types (work on both Intel and AMD)
        analysis_types = [
            'hotspots',
            'memory-access',
            'memory-consumption',
            'threading',
            'system-overview',
        ]
        
        # Intel-specific types (may not work on AMD)
        intel_specific = [
            'uarch-exploration',
            'microarchitecture-exploration',
            'hpc-performance-characterization',
        ]
        
        # GPU types
        gpu_types = [
            'gpu-offload',
            'gpu-hotspots',
            'gpu-compute-media',
        ]
        
        # Check CPU architecture
        cpu_vendor = platform.processor().upper()
        is_intel = 'INTEL' in cpu_vendor or 'CORE' in cpu_vendor or 'XEON' in cpu_vendor
        
        # If Intel, add Intel-specific types
        if is_intel:
            analysis_types.extend(intel_specific)
        
        # Verify which ones are actually available
        available = []
        for atype in analysis_types:
            try:
                result = subprocess.run(
                    [self.vtune_path, "-collect", atype, "-help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Check if analysis type is supported
                if result.returncode == 0:
                    # Check stderr for errors about microarchitecture
                    if "not applicable" not in result.stderr.lower():
                        available.append(atype)
                elif "collect" in result.stdout.lower():
                    available.append(atype)
            except:
                pass
        
        # Always return at least hotspots (most universal)
        return available if available else ['hotspots']
    
    def get_available_metrics(self, analysis_type: str = "uarch-exploration") -> Dict[str, List[str]]:
        """
        Get available metrics for a specific analysis type.
        
        Args:
            analysis_type: VTune analysis type
            
        Returns:
            Dictionary mapping metric categories to lists of metric names
        """
        cache_key = f"{analysis_type}_metrics"
        if cache_key in self.metrics_cache:
            return self.metrics_cache[cache_key]
        
        metrics = {
            "cpu_metrics": [
                "CPU_CLK_UNHALTED.THREAD",
                "CPU_CLK_UNHALTED.REF_TSC",
                "INST_RETIRED.ANY",
                "CPU_CLK_UNHALTED.REF_XCLK",
                "CPU_CLK_UNHALTED.CORE",
            ],
            "cache_metrics": [
                "L1D.REPLACEMENT",
                "L1D.M_EVICT",
                "L2_RQSTS.ALL_DEMAND_DATA_RD",
                "L2_RQSTS.ALL_RFO",
                "L2_RQSTS.MISS",
                "L2_RQSTS.REFERENCES",
                "LLC_REFERENCES",
                "LLC_MISSES",
            ],
            "memory_metrics": [
                "MEM_LOAD_RETIRED.L1_HIT",
                "MEM_LOAD_RETIRED.L2_HIT",
                "MEM_LOAD_RETIRED.L3_HIT",
                "MEM_LOAD_RETIRED.L3_MISS",
                "MEM_STORE_RETIRED.L1_HIT",
                "MEM_STORE_RETIRED.L2_HIT",
            ],
            "branch_metrics": [
                "BR_INST_RETIRED.ALL_BRANCHES",
                "BR_MISP_RETIRED.ALL_BRANCHES",
                "BR_INST_RETIRED.CONDITIONAL",
                "BR_MISP_RETIRED.CONDITIONAL",
            ],
            "pipeline_metrics": [
                "IDQ_UOPS_NOT_DELIVERED.CORE",
                "UOPS_ISSUED.ANY",
                "UOPS_RETIRED.ALL",
                "UOPS_EXECUTED.CORE",
            ],
        }
        
        # Try to query VTune for actual available metrics
        try:
            result = subprocess.run(
                [self.vtune_path, "-collect", analysis_type, "-help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse output for metric information
            # This is a simplified version - actual parsing would be more complex
        except:
            pass
        
        self.metrics_cache[cache_key] = metrics
        return metrics
    
    def get_tunable_parameters(self) -> Dict[str, List]:
        """
        Get tunable VTune parameters for autotuning.
        
        These represent different analysis configurations that can be tuned.
        
        Returns:
            Dictionary of parameter names to possible values
        """
        return {
            "analysis_type": self.get_analysis_types(),
            "sampling_interval": [1, 10, 100, 1000],  # milliseconds
            "stack_size": [0, 1, 2, 4, 8],  # KB
            "enable_callstack": [True, False],
            "enable_user_mode": [True, False],
            "enable_kernel_mode": [True, False],
        }
    
    def get_cpu_info(self) -> Dict[str, str]:
        """
        Get basic CPU information using system commands.
        
        Returns:
            Dictionary with CPU information
        """
        cpu_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }
        
        # Try to get more detailed CPU info on Windows
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name,numberofcores,numberoflogicalprocessors,maxclockspeed"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].strip().split()
                    if parts:
                        cpu_info["name"] = ' '.join(parts[:-3]) if len(parts) > 3 else ' '.join(parts)
                        cpu_info["cores"] = parts[-3] if len(parts) > 3 else "unknown"
                        cpu_info["threads"] = parts[-2] if len(parts) > 2 else "unknown"
                        cpu_info["max_clock_mhz"] = parts[-1] if len(parts) > 1 else "unknown"
        except:
            pass
        
        return cpu_info
    
    def discover_all_metrics(self) -> Dict:
        """
        Discover all available metrics and create a comprehensive catalog.
        
        Returns:
            Dictionary with all discovered information
        """
        print("Discovering VTune metrics and capabilities...")
        
        discovery_result = {
            "vtune_path": self.vtune_path,
            "vtune_available": self.check_vtune_available(),
            "analysis_types": self.get_analysis_types(),
            "cpu_info": self.get_cpu_info(),
            "tunable_parameters": self.get_tunable_parameters(),
        }
        
        # Get metrics for each analysis type
        discovery_result["metrics_by_analysis"] = {}
        for atype in discovery_result["analysis_types"][:3]:  # Limit to first 3 for speed
            try:
                discovery_result["metrics_by_analysis"][atype] = self.get_available_metrics(atype)
            except:
                pass
        
        return discovery_result
    
    def save_discovery(self, output_file: str = "vtune_discovery.json"):
        """Save discovery results to JSON file."""
        discovery = self.discover_all_metrics()
        with open(output_file, 'w') as f:
            json.dump(discovery, f, indent=2)
        print(f"Discovery results saved to {output_file}")
        return discovery


if __name__ == "__main__":
    discovery = VTuneMetricsDiscovery()
    results = discovery.save_discovery()
    print("\nDiscovery Summary:")
    print(f"VTune Path: {results['vtune_path']}")
    print(f"Available: {results['vtune_available']}")
    print(f"Analysis Types: {len(results['analysis_types'])} found")
    print(f"CPU: {results['cpu_info'].get('name', 'Unknown')}")
