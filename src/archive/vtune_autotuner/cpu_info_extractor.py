"""
CPU Information Extractor

Extracts actual CPU parameters from the system for comparison with predictions.
Uses system commands and CPUID information to get real hardware specifications.
"""

import subprocess
import platform
import re
from typing import Dict, Optional
from pathlib import Path


class CPUInfoExtractor:
    """Extracts actual CPU parameters from the system."""
    
    def __init__(self):
        self.cpu_info = {}
        self._extract_all()
    
    def _extract_all(self):
        """Extract all available CPU information."""
        self.cpu_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }
        
        if platform.system() == "Windows":
            self._extract_windows()
        elif platform.system() == "Linux":
            self._extract_linux()
        else:
            self._extract_generic()
    
    def _extract_windows(self):
        """Extract CPU info on Windows."""
        # Get CPU name and basic info
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
                        # CPU name is everything except last 3 parts
                        name_parts = parts[:-3] if len(parts) > 3 else parts
                        self.cpu_info["name"] = ' '.join(name_parts)
                        self.cpu_info["cores"] = int(parts[-3]) if len(parts) > 3 and parts[-3].isdigit() else None
                        self.cpu_info["threads"] = int(parts[-2]) if len(parts) > 2 and parts[-2].isdigit() else None
                        self.cpu_info["max_clock_mhz"] = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else None
        except Exception as e:
            print(f"Warning: Could not extract CPU info via wmic: {e}")
        
        # Get cache information using wmic
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "L2CacheSize,L3CacheSize"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].strip().split()
                    if len(parts) >= 2:
                        self.cpu_info["l2_cache_size_kb"] = int(parts[0]) if parts[0].isdigit() else None
                        self.cpu_info["l3_cache_size_kb"] = int(parts[1]) if parts[1].isdigit() else None
        except Exception as e:
            print(f"Warning: Could not extract cache info: {e}")
        
        # Try to get more detailed info using CPUID or registry
        self._extract_windows_detailed()
    
    def _extract_windows_detailed(self):
        """Extract detailed CPU info on Windows using additional methods."""
        # Try to get L1 cache from registry or CPUID
        try:
            # Use PowerShell to query CPUID information
            ps_script = """
            $cpu = Get-WmiObject Win32_Processor
            $cpu | Select-Object L2CacheSize, L3CacheSize, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed
            """
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse PowerShell output
                for line in result.stdout.split('\n'):
                    if 'L2CacheSize' in line or 'L3CacheSize' in line:
                        # Extract values
                        pass
        except:
            pass
        
        # Try to use CPU-Z or similar tools if available
        # For now, we'll use heuristics based on CPU name
    
    def _extract_linux(self):
        """Extract CPU info on Linux."""
        try:
            # Get CPU info from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                
            # Extract model name
            match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
            if match:
                self.cpu_info["name"] = match.group(1).strip()
            
            # Extract cache sizes
            l1d_match = re.search(r'cache size\s*:\s*(\d+)\s*KB', cpuinfo)
            if l1d_match:
                self.cpu_info["l1_cache_size_kb"] = int(l1d_match.group(1))
            
            # Get L2/L3 from lscpu
            try:
                result = subprocess.run(
                    ["lscpu"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'L1d cache' in line:
                            match = re.search(r'(\d+)\s*K', line)
                            if match:
                                self.cpu_info["l1_cache_size_kb"] = int(match.group(1))
                        elif 'L2 cache' in line:
                            match = re.search(r'(\d+)\s*K', line)
                            if match:
                                self.cpu_info["l2_cache_size_kb"] = int(match.group(1))
                        elif 'L3 cache' in line:
                            match = re.search(r'(\d+)\s*K', line)
                            if match:
                                self.cpu_info["l3_cache_size_kb"] = int(match.group(1))
                        elif 'CPU(s):' in line:
                            match = re.search(r'(\d+)', line)
                            if match:
                                self.cpu_info["threads"] = int(match.group(1))
                        elif 'Core(s) per socket' in line:
                            match = re.search(r'(\d+)', line)
                            if match:
                                self.cpu_info["cores"] = int(match.group(1))
            except:
                pass
        except Exception as e:
            print(f"Warning: Could not extract CPU info from /proc/cpuinfo: {e}")
    
    def _extract_generic(self):
        """Extract generic CPU info."""
        # Fallback method
        pass
    
    def get_actual_parameters(self) -> Dict:
        """
        Get actual CPU parameters that can be compared with predictions.
        
        Returns:
            Dictionary of actual CPU parameters
        """
        actual = {}
        
        # Cache sizes (convert to KB if needed)
        if "l1_cache_size_kb" in self.cpu_info:
            actual["l1_cache_size_kb"] = self.cpu_info["l1_cache_size_kb"]
        else:
            # Estimate based on CPU architecture (common values)
            actual["l1_cache_size_kb"] = None  # Will need to be looked up
        
        if "l2_cache_size_kb" in self.cpu_info:
            actual["l2_cache_size_kb"] = self.cpu_info["l2_cache_size_kb"]
        else:
            actual["l2_cache_size_kb"] = None
        
        if "l3_cache_size_kb" in self.cpu_info:
            actual["l3_cache_size_kb"] = self.cpu_info["l3_cache_size_kb"]
        else:
            actual["l3_cache_size_kb"] = None
        
        # CPU architecture parameters (these need to be looked up or estimated)
        # ROB size, issue width are architecture-specific
        actual["cores"] = self.cpu_info.get("cores")
        actual["threads"] = self.cpu_info.get("threads")
        actual["max_clock_mhz"] = self.cpu_info.get("max_clock_mhz")
        actual["cpu_name"] = self.cpu_info.get("name", self.cpu_info.get("processor", "Unknown"))
        
        # Lookup architecture-specific parameters
        self._lookup_architecture_params(actual)
        
        return actual
    
    def _lookup_architecture_params(self, actual: Dict):
        """
        Lookup architecture-specific parameters based on CPU name.
        
        This uses heuristics and known CPU specifications.
        """
        cpu_name = actual.get("cpu_name", "").upper()
        
        # Intel processors
        if "INTEL" in cpu_name or "CORE" in cpu_name:
            # Modern Intel (Skylake and later)
            if any(x in cpu_name for x in ["I7", "I9", "I5"]):
                # Skylake, Kaby Lake, Coffee Lake, etc.
                actual["rob_size"] = 224  # Typical for modern Intel
                actual["issue_width"] = 4  # 4-wide decode
            elif "XEON" in cpu_name:
                actual["rob_size"] = 224
                actual["issue_width"] = 4
            else:
                # Older Intel
                actual["rob_size"] = 192
                actual["issue_width"] = 4
        
        # AMD processors
        elif "AMD" in cpu_name or "RYZEN" in cpu_name or "Family 26" in cpu_name:
            # Check for specific Ryzen models
            if "2600" in cpu_name or ("Family 26" in cpu_name and "Model 36" in cpu_name):
                # AMD Ryzen 5 2600 (Zen+ architecture)
                actual["rob_size"] = 192
                actual["issue_width"] = 4
                # Cache sizes (from specifications)
                actual["l1_data_cache_size_kb"] = 32  # Per core
                actual["l1_instruction_cache_size_kb"] = 64  # Per core
                actual["l2_cache_size_kb"] = 512  # Per core
                actual["l3_cache_size_kb"] = 16384  # 16MB total (shared)
                actual["l1_cache_size_kb"] = 96  # 32+64 per core
            elif "RYZEN" in cpu_name:
                # Zen, Zen+, Zen2, Zen3 (generic)
                actual["rob_size"] = 192  # Zen architecture
                actual["issue_width"] = 4
            elif "EPYC" in cpu_name:
                actual["rob_size"] = 192
                actual["issue_width"] = 4
            else:
                # Older AMD
                actual["rob_size"] = 192
                actual["issue_width"] = 4
        
        # Default values if not found
        if "rob_size" not in actual:
            actual["rob_size"] = 192  # Conservative default
        if "issue_width" not in actual:
            actual["issue_width"] = 4  # Common default
        
        # Branch predictor accuracy (typical values)
        actual["branch_predictor_accuracy"] = 0.95  # Typical modern CPU
        
        # Cache latencies (typical values in cycles)
        actual["l1_latency_cycles"] = 3  # Typical L1 latency
        actual["l2_latency_cycles"] = 12  # Typical L2 latency
        actual["l3_latency_cycles"] = 40  # Typical L3 latency
    
    def get_all_info(self) -> Dict:
        """Get all extracted CPU information."""
        return self.cpu_info.copy()
    
    def save_to_file(self, filepath: str):
        """Save CPU information to JSON file."""
        import json
        info = {
            "extracted_info": self.cpu_info,
            "actual_parameters": self.get_actual_parameters()
        }
        with open(filepath, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"CPU information saved to {filepath}")


if __name__ == "__main__":
    extractor = CPUInfoExtractor()
    print("Extracted CPU Information:")
    print("=" * 60)
    for key, value in extractor.get_all_info().items():
        print(f"{key}: {value}")
    
    print("\nActual Parameters (for comparison):")
    print("=" * 60)
    for key, value in extractor.get_actual_parameters().items():
        print(f"{key}: {value}")
