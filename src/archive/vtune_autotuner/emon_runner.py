#!/usr/bin/env python3
"""
EMON (Event Monitor) Runner Module

Executes Intel EMON to collect hardware performance monitoring events.
EMON provides low-level access to CPU performance counters.
"""

import subprocess
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import time


def get_real_python_executable() -> str:
    """
    Get the real Python executable path, avoiding Windows Store launcher.
    
    Returns:
        Path to actual Python executable
    """
    python_exe = sys.executable
    
    # Check if this is the Windows Store launcher
    if "WindowsApps" in python_exe and "python.exe" in python_exe:
        # Try to find real Python using py launcher
        try:
            result = subprocess.run(
                ["py", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                real_python = result.stdout.strip()
                if Path(real_python).exists():
                    return real_python
        except:
            pass
        
        # Fallback: try common Python installation paths
        common_paths = [
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "python.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python312" / "python.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python311" / "python.exe",
            Path("C:/Python313/python.exe"),
            Path("C:/Python312/python.exe"),
            Path("C:/Python311/python.exe"),
        ]
        
        for path in common_paths:
            if path.exists():
                return str(path)
    
    return python_exe


class EMONRunner:
    """Handles Intel EMON execution and result parsing."""
    
    def __init__(self, emon_path: Optional[str] = None):
        """
        Initialize EMON runner.
        
        Args:
            emon_path: Path to EMON executable. If None, will be auto-detected.
        """
        self.emon_path = self._find_emon(emon_path)
        self.results_dir = Path("emon_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _find_emon(self, custom_path: Optional[str] = None) -> str:
        """Find EMON executable path."""
        if custom_path and Path(custom_path).exists():
            return custom_path
        
        # Common EMON installation paths on Windows
        common_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI\vtune\latest\bin64\emon.exe",
            r"C:\Program Files\Intel\oneAPI\vtune\latest\bin64\emon.exe",
            r"C:\Program Files (x86)\IntelSWTools\vtune_profiler\bin64\emon.exe",
            r"C:\Program Files\IntelSWTools\vtune_profiler\bin64\emon.exe",
        ]
        
        # Check environment variables
        if "VTUNE_PROFILER_DIR" in os.environ:
            vtune_dir = Path(os.environ["VTUNE_PROFILER_DIR"])
            candidate = vtune_dir / "bin64" / "emon.exe"
            if candidate.exists():
                return str(candidate)
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["where", "emon"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        raise FileNotFoundError(
            "EMON not found. EMON is typically included with Intel VTune Profiler."
        )
    
    def _is_amd_cpu(self) -> bool:
        """Check if the current CPU is AMD (EMON is Intel-specific)."""
        try:
            import platform
            processor = platform.processor()
            cpu_name = processor.upper() if processor else ""
            
            # Check for AMD indicators
            if "AMD" in cpu_name or "RYZEN" in cpu_name:
                return True
            
            # Check Windows system info
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "name"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        output = result.stdout.upper()
                        if "AMD" in output or "RYZEN" in output or "FAMILY 26" in output:
                            return True
                except:
                    pass
            
            return False
        except:
            # If we can't determine, assume Intel (safer to try)
            return False
    
    def get_available_events(self) -> List[str]:
        """
        Get list of available hardware events on the current CPU.
        
        Returns:
            List of event names
        """
        try:
            result = subprocess.run(
                [self.emon_path, "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                events = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract event name (format may vary)
                        parts = line.split()
                        if parts:
                            events.append(parts[0])
                return events
        except Exception as e:
            print(f"Error getting available events: {e}")
        
        # Fallback to common events
        return [
            "CPU_CLK_UNHALTED.THREAD",
            "INST_RETIRED.ANY",
            "L1D.REPLACEMENT",
            "L2_RQSTS.ALL_DEMAND_DATA_RD",
            "LLC_REFERENCES",
            "LLC_MISSES",
            "BR_INST_RETIRED.ALL_BRANCHES",
            "BR_MISP_RETIRED.ALL_BRANCHES",
        ]
    
    def run_emon(
        self,
        workload_path: str,
        events: Optional[List[str]] = None,
        duration: Optional[int] = None,
        output_file: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run EMON on a workload.
        
        Args:
            workload_path: Path to the workload executable/script
            events: List of events to monitor (None = use defaults)
            duration: Collection duration in seconds (None = full execution)
            output_file: Output file for EMON data
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with execution results and event counts
        """
        if output_file is None:
            timestamp = int(time.time())
            output_file = self.results_dir / f"emon_{timestamp}.dat"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if CPU is AMD (EMON is Intel-specific and doesn't work on AMD)
        if self._is_amd_cpu():
            return {
                "success": False,
                "error": "EMON is Intel-specific and not supported on AMD CPUs",
                "return_code": -1,
                "output_file": str(output_file)
            }
        
        if events is None:
            events = self.get_available_events()[:8]  # Limit to 8 events
        
        # Build EMON command
        # EMON syntax: emon -i <event_list_file> -o <output_file> -- <command>
        # Note: -v is for verbose mode and should not be used with event collection
        cmd = [self.emon_path]
        
        # Create event list file
        event_list_file = output_file.parent / f"{output_file.stem}_events.txt"
        with open(event_list_file, 'w') as f:
            for event in events:
                f.write(f"{event}\n")
        
        cmd.extend(["-i", str(event_list_file)])
        cmd.extend(["-o", str(output_file)])
        
        if duration:
            cmd.extend(["-d", str(duration)])
        
        # Add workload
        cmd.append("--")
        
        if workload_path.endswith('.py'):
            # Use real Python executable (avoid Windows Store launcher)
            python_exe = get_real_python_executable()
            cmd.extend([python_exe, workload_path])
        else:
            cmd.append(workload_path)
        
        print(f"Running EMON: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"EMON execution failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "return_code": result.returncode,
                    "output_file": str(output_file)
                }
            
            # Parse results
            event_counts = self.parse_emon_results(output_file, event_list_file)
            
            return {
                "success": True,
                "output_file": str(output_file),
                "elapsed_time": elapsed_time,
                "events": events,
                "event_counts": event_counts,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"EMON execution timed out after {timeout} seconds",
                "output_file": str(output_file)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output_file": str(output_file)
            }
        finally:
            # Clean up event list file
            if event_list_file.exists():
                try:
                    event_list_file.unlink()
                except:
                    pass
    
    def parse_emon_results(self, output_file: Path, event_list_file: Path) -> Dict[str, float]:
        """
        Parse EMON output file to extract event counts.
        
        Args:
            output_file: Path to EMON output file
            event_list_file: Path to event list file used
            
        Returns:
            Dictionary mapping event names to counts
        """
        event_counts = {}
        
        # Read event list
        events = []
        if event_list_file.exists():
            with open(event_list_file, 'r') as f:
                events = [line.strip() for line in f if line.strip()]
        
        # Parse EMON output file
        # EMON output format varies, this is a simplified parser
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Try to parse as CSV
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        # Try different parsing strategies
                        parts = line.split()
                        if len(parts) >= 2:
                            # Assume format: event_name count
                            event_name = parts[0]
                            try:
                                count = float(parts[1].replace(',', ''))
                                event_counts[event_name] = count
                            except:
                                pass
                        
                        # Also try CSV format
                        if ',' in line:
                            csv_parts = line.split(',')
                            if len(csv_parts) >= 2:
                                event_name = csv_parts[0].strip()
                                try:
                                    count = float(csv_parts[1].strip().replace(',', ''))
                                    event_counts[event_name] = count
                                except:
                                    pass
            except Exception as e:
                print(f"Error parsing EMON output file {output_file}: {e}")
        
        # If parsing failed, try to extract from stdout/stderr
        # This is a fallback method
        if not event_counts and events:
            # Create placeholder values
            for event in events:
                event_counts[event] = 0.0
        
        return event_counts
    
    def extract_performance_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key performance metrics from EMON results.
        
        Args:
            result: Result dictionary from run_emon
            
        Returns:
            Dictionary of performance metrics
        """
        if not result.get("success"):
            return {}
        
        event_counts = result.get("event_counts", {})
        metrics = {}
        
        # Calculate derived metrics
        if "CPU_CLK_UNHALTED.THREAD" in event_counts and "INST_RETIRED.ANY" in event_counts:
            cycles = event_counts["CPU_CLK_UNHALTED.THREAD"]
            instructions = event_counts["INST_RETIRED.ANY"]
            if instructions > 0:
                metrics["CPI"] = cycles / instructions  # Cycles per instruction
                metrics["IPC"] = instructions / cycles  # Instructions per cycle
        
        # Cache metrics
        if "LLC_REFERENCES" in event_counts and "LLC_MISSES" in event_counts:
            references = event_counts["LLC_REFERENCES"]
            misses = event_counts["LLC_MISSES"]
            if references > 0:
                metrics["LLC_MISS_RATE"] = misses / references
                metrics["LLC_HIT_RATE"] = 1 - (misses / references)
        
        # Branch prediction
        if "BR_INST_RETIRED.ALL_BRANCHES" in event_counts and "BR_MISP_RETIRED.ALL_BRANCHES" in event_counts:
            branches = event_counts["BR_INST_RETIRED.ALL_BRANCHES"]
            mispredicts = event_counts["BR_MISP_RETIRED.ALL_BRANCHES"]
            if branches > 0:
                metrics["BRANCH_MISPREDICT_RATE"] = mispredicts / branches
                metrics["BRANCH_PREDICT_RATE"] = 1 - (mispredicts / branches)
        
        # Add raw event counts
        for event, count in event_counts.items():
            metrics[f"EMON_{event}"] = count
        
        return metrics


if __name__ == "__main__":
    # Test EMON runner
    try:
        runner = EMONRunner()
        
        # Test with a simple Python script
        test_script = """
import time
import numpy as np
arr = np.random.rand(1000, 1000)
result = np.dot(arr, arr)
print("Done")
"""
        
        test_file = Path("test_workload.py")
        test_file.write_text(test_script)
        
        try:
            result = runner.run_emon(
                str(test_file),
                duration=10
            )
            
            print("\nEMON Execution Result:")
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Event Counts: {json.dumps(result['event_counts'], indent=2)}")
                metrics = runner.extract_performance_metrics(result)
                print(f"Derived Metrics: {json.dumps(metrics, indent=2)}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        finally:
            if test_file.exists():
                test_file.unlink()
    except FileNotFoundError as e:
        print(f"EMON not available: {e}")
