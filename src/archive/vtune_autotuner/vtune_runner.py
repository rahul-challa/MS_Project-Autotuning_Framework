#!/usr/bin/env python3
"""
VTune Runner Module

Executes Intel VTune Profiler and parses results to extract performance metrics.
Handles VTune command-line execution, result parsing, and metric extraction.
"""

import subprocess
import json
import re
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import shutil


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


class VTuneRunner:
    """Handles VTune Profiler execution and result parsing."""
    
    def __init__(self, vtune_path: Optional[str] = None):
        """
        Initialize VTune runner.
        
        Args:
            vtune_path: Path to VTune executable. If None, will be auto-detected.
        """
        if vtune_path:
            self.vtune_path = vtune_path
        else:
            from .discovery import VTuneMetricsDiscovery
            discovery = VTuneMetricsDiscovery(vtune_path)
            self.vtune_path = discovery.vtune_path
        self.results_dir = Path("vtune_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def run_vtune(
        self,
        workload_path: str,
        analysis_type: str = "hotspots",
        result_dir: Optional[str] = None,
        duration: Optional[int] = None,
        additional_options: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run VTune Profiler on a workload.
        
        Args:
            workload_path: Path to the workload executable/script
            analysis_type: VTune analysis type (e.g., 'hotspots', 'uarch-exploration')
            result_dir: Directory to store results (auto-generated if None)
            duration: Collection duration in seconds (None = full execution)
            additional_options: Additional VTune command-line options
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with execution results and metrics
        """
        if result_dir is None:
            timestamp = int(time.time())
            result_dir = self.results_dir / f"vtune_{analysis_type}_{timestamp}"
        else:
            result_dir = Path(result_dir)
        
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # Build VTune command
        cmd = [
            self.vtune_path,
            "-collect", analysis_type,
            "-result-dir", str(result_dir),
        ]
        
        if duration:
            cmd.extend(["-duration", str(duration)])
        
        if additional_options:
            cmd.extend(additional_options)
        
        # Add workload
        cmd.append("--")
        
        # Determine how to run the workload
        if workload_path.endswith('.py'):
            # Find Python executable (avoid Windows Store launcher)
            python_exe = get_real_python_executable()
            cmd.extend([python_exe, workload_path])
        else:
            cmd.append(workload_path)
        
        print(f"Running VTune: {' '.join(cmd)}")
        
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
                print(f"VTune execution failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "return_code": result.returncode,
                    "result_dir": str(result_dir)
                }
            
            # Parse results
            metrics = self.parse_vtune_results(result_dir, analysis_type)
            
            return {
                "success": True,
                "result_dir": str(result_dir),
                "elapsed_time": elapsed_time,
                "analysis_type": analysis_type,
                "metrics": metrics,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"VTune execution timed out after {timeout} seconds",
                "result_dir": str(result_dir)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result_dir": str(result_dir)
            }
    
    def parse_vtune_results(self, result_dir: Path, analysis_type: str) -> Dict[str, Any]:
        """
        Parse VTune results from result directory.
        
        Args:
            result_dir: Path to VTune results directory
            analysis_type: Analysis type that was run
            
        Returns:
            Dictionary of parsed metrics
        """
        metrics = {}
        result_dir = Path(result_dir)
        
        # Look for summary files
        summary_files = [
            result_dir / "summary.txt",
            result_dir / "summary.csv",
            result_dir / "r000hs" / "summary.txt",  # Common VTune structure
            result_dir / "r000hs" / "summary.csv",
        ]
        
        for summary_file in summary_files:
            if summary_file.exists():
                metrics.update(self._parse_summary_file(summary_file))
                break
        
        # Try to parse XML results if available
        xml_files = list(result_dir.glob("*.xml"))
        for xml_file in xml_files:
            try:
                metrics.update(self._parse_xml_file(xml_file))
            except:
                pass
        
        # Try to parse CSV files
        csv_files = list(result_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                metrics.update(self._parse_csv_file(csv_file))
            except:
                pass
        
        return metrics
    
    def _parse_summary_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse VTune summary text file."""
        metrics = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Extract common metrics using regex
                patterns = {
                    "elapsed_time": r"Elapsed Time:\s*([\d.]+)\s*sec",
                    "cpu_time": r"CPU Time:\s*([\d.]+)\s*sec",
                    "instructions": r"Instructions Retired:\s*([\d,]+)",
                    "clockticks": r"Clockticks:\s*([\d,]+)",
                    "cpu_utilization": r"CPU Utilization:\s*([\d.]+)%",
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        value = match.group(1).replace(',', '')
                        try:
                            metrics[key] = float(value)
                        except:
                            metrics[key] = value
        except Exception as e:
            print(f"Error parsing summary file {file_path}: {e}")
        
        return metrics
    
    def _parse_xml_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse VTune XML result file."""
        metrics = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract metrics from XML structure
            # This is a simplified parser - actual VTune XML structure may vary
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    tag = elem.tag.lower().replace('{', '').replace('}', '')
                    if any(keyword in tag for keyword in ['metric', 'counter', 'value', 'time']):
                        try:
                            value = float(elem.text.strip())
                            metrics[tag] = value
                        except:
                            pass
        except Exception as e:
            print(f"Error parsing XML file {file_path}: {e}")
        
        return metrics
    
    def _parse_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse VTune CSV result file."""
        metrics = {}
        
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for key, value in row.items():
                        if value and value.strip():
                            try:
                                # Try to convert to number
                                num_value = float(value.replace(',', ''))
                                metrics[key.strip()] = num_value
                            except:
                                metrics[key.strip()] = value.strip()
        except Exception as e:
            print(f"Error parsing CSV file {file_path}: {e}")
        
        return metrics
    
    def extract_execution_time(self, result: Dict[str, Any]) -> float:
        """
        Extract execution time from VTune results.
        
        Args:
            result: Result dictionary from run_vtune
            
        Returns:
            Execution time in seconds, or 0.0 if not available
        """
        if not result.get("success"):
            return 0.0
        
        metrics = result.get("metrics", {})
        
        # Try different metric names for execution time
        time_metrics = [
            "elapsed_time",
            "cpu_time",
            "execution_time",
            "wall_clock_time",
            "Elapsed Time",
            "CPU Time",
        ]
        
        for metric in time_metrics:
            if metric in metrics:
                return float(metrics[metric])
        
        # Fallback to elapsed_time from result
        return result.get("elapsed_time", 0.0)
    
    def extract_performance_metrics(self, result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key performance metrics from VTune results.
        
        Args:
            result: Result dictionary from run_vtune
            
        Returns:
            Dictionary of performance metrics
        """
        if not result.get("success"):
            return {}
        
        metrics = result.get("metrics", {})
        
        # Extract key metrics
        performance_metrics = {}
        
        # CPU metrics
        cpu_keys = ["instructions", "clockticks", "cpu_utilization", "cpu_time"]
        for key in cpu_keys:
            if key in metrics:
                performance_metrics[key] = metrics[key]
        
        # Cache metrics
        cache_keys = [k for k in metrics.keys() if any(x in k.lower() for x in ['cache', 'l1', 'l2', 'l3', 'llc'])]
        for key in cache_keys:
            performance_metrics[key] = metrics[key]
        
        # Memory metrics
        memory_keys = [k for k in metrics.keys() if 'memory' in k.lower() or 'mem' in k.lower()]
        for key in memory_keys:
            performance_metrics[key] = metrics[key]
        
        return performance_metrics
    
    def cleanup_results(self, result_dir: Optional[str] = None, keep_recent: int = 5):
        """
        Clean up old VTune result directories.
        
        Args:
            result_dir: Base results directory (default: self.results_dir)
            keep_recent: Number of recent results to keep
        """
        if result_dir is None:
            result_dir = self.results_dir
        else:
            result_dir = Path(result_dir)
        
        if not result_dir.exists():
            return
        
        # Get all result directories sorted by modification time
        dirs = [d for d in result_dir.iterdir() if d.is_dir()]
        dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old directories
        for old_dir in dirs[keep_recent:]:
            try:
                shutil.rmtree(old_dir)
                print(f"Removed old result directory: {old_dir}")
            except Exception as e:
                print(f"Error removing {old_dir}: {e}")


if __name__ == "__main__":
    # Test VTune runner
    runner = VTuneRunner()
    
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
        result = runner.run_vtune(
            str(test_file),
            analysis_type="hotspots",
            duration=10
        )
        
        print("\nVTune Execution Result:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Execution Time: {runner.extract_execution_time(result):.3f}s")
            print(f"Metrics: {json.dumps(result['metrics'], indent=2)}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    finally:
        if test_file.exists():
            test_file.unlink()
