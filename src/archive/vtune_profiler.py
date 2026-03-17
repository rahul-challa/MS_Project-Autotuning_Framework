#!/usr/bin/env python3
"""
Intel VTune Profiler Integration Module

This module provides functions to run benchmarks with VTune Profiler
and extract performance metrics. VTune profiles actual CPU execution,
providing ground truth performance data for the autotuner.
"""

import subprocess
import json
import re
import os
import platform
from pathlib import Path
from typing import Dict, Optional, List
import xml.etree.ElementTree as ET


class VTuneProfiler:
    """
    Wrapper class for Intel VTune Profiler command-line interface.
    """
    
    def __init__(self, vtune_path: Optional[str] = None):
        """
        Initialize VTune Profiler interface.
        
        Args:
            vtune_path: Path to VTune Profiler executable. If None, tries to find it.
        """
        self.vtune_path = self._find_vtune(vtune_path)
        self.results_dir = Path.cwd() / 'vtune_results'
        self.results_dir.mkdir(exist_ok=True)
    
    def _find_vtune(self, vtune_path: Optional[str]) -> str:
        """Find VTune Profiler executable."""
        if vtune_path and Path(vtune_path).exists():
            return vtune_path
        
        # Common VTune installation paths (Linux)
        linux_paths = [
            '/opt/intel/oneapi/vtune/latest/bin64/vtune',
            '/opt/intel/vtune_profiler/bin64/vtune',
        ]
        
        # Common VTune installation paths (Windows)
        import platform
        windows_paths = []
        if platform.system() == 'Windows':
            # Check common Windows installation locations
            program_files = [
                os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                os.environ.get('ProgramFiles', r'C:\Program Files'),
            ]
            for pf in program_files:
                # Check for oneAPI VTune installations
                oneapi_base = Path(pf) / 'Intel' / 'oneAPI' / 'vtune'
                if oneapi_base.exists():
                    # Find latest version
                    versions = sorted([d for d in oneapi_base.iterdir() if d.is_dir()], reverse=True)
                    for version_dir in versions:
                        vtune_exe = version_dir / 'bin64' / 'vtune.exe'
                        if vtune_exe.exists():
                            windows_paths.append(str(vtune_exe))
                            break
        
        # Try all paths
        all_paths = linux_paths + windows_paths + ['vtune']  # Add 'vtune' for PATH
        
        for path in all_paths:
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # Fallback: try to find via which/where (Linux/Windows)
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    ['where.exe', 'vtune'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ['which', 'vtune'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return 'vtune'  # Default, will fail if not found
    
    def profile_workload(
        self,
        workload_command: List[str],
        workload_id: str,
        collection_type: str = 'hotspots',
        timeout: int = 300,
        collect_all_types: bool = False
    ) -> Dict[str, float]:
        """
        Profile a workload using VTune Profiler.
        
        Args:
            workload_command: Command to run the workload (list of strings)
            workload_id: Unique identifier for this workload
            collection_type: VTune collection type ('hotspots', 'microarchitecture', etc.)
            timeout: Maximum execution time in seconds
            collect_all_types: If True, collect metrics from all collection types
        
        Returns:
            Dictionary of performance metrics (aggregated from all collection types if collect_all_types=True)
        """
        all_metrics = {}
        
        # Determine which collection types to use
        if collect_all_types:
            # Try all available collection types, but prioritize ones that work
            collection_types = [
                'hotspots',  # Most basic, should work on all systems
                'uarch-exploration',  # Microarchitecture exploration
                'memory-access',  # Memory analysis
                'threading',  # Threading analysis
                'memory-consumption',  # Memory consumption
                # Skip these as they may not be available:
                # 'microarchitecture-exploration',  # May require admin
                # 'bandwidth',  # May not be available
            ]
        else:
            collection_types = [collection_type]
        
        for ct in collection_types:
            result_name = f"{workload_id}_{ct}"
            result_path = self.results_dir / result_name
            
            # Clean up any existing results
            if result_path.exists():
                import shutil
                shutil.rmtree(result_path)
            
            # Build VTune command
            cmd = [
                self.vtune_path,
                '-collect', ct,
                '-result-dir', str(result_path),
                '-quiet',
                '--'
            ] + workload_command
            
            try:
                # Run VTune profiling
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.getcwd()
                )
                
                if result.returncode != 0:
                    # Skip failed collection types (some may require admin or specific hardware)
                    print(f"Warning: VTune profiling failed for {workload_id} with {ct} (returncode: {result.returncode})")
                    if result.stderr:
                        print(f"  stderr: {result.stderr[:500]}")
                    if result.stdout:
                        print(f"  stdout: {result.stdout[:500]}")
                    continue
                
                # Extract metrics from VTune results
                print(f"  Extracting metrics from {result_path}...")
                metrics = self._extract_metrics(result_path, workload_id)
                print(f"  Extracted {len(metrics)} metrics from {ct}")
                
                # Merge metrics (prefer non-default values, average if both exist)
                for key, value in metrics.items():
                    if key not in all_metrics:
                        all_metrics[key] = value
                    elif all_metrics[key] == 1.0 and value != 1.0:  # Replace default
                        all_metrics[key] = value
                    elif key not in ['execution_time', 'elapsed_time', 'cpu_time']:
                        # Average non-timing metrics from different collection types
                        all_metrics[key] = (all_metrics[key] + value) / 2
                    else:
                        # For timing metrics, use minimum (most accurate)
                        all_metrics[key] = min(all_metrics[key], value)
                
            except subprocess.TimeoutExpired:
                print(f"Warning: VTune profiling timed out for {workload_id} with {ct}")
                continue
            except Exception as e:
                print(f"Error profiling {workload_id} with {ct}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # If no metrics collected, raise an error
        if not all_metrics:
            raise RuntimeError(
                f"Failed to collect any metrics from VTune for {workload_id}. "
                f"VTune profiling may have failed or returned no data."
            )
        
        return all_metrics
    
    def _extract_metrics(self, result_path: Path, workload_id: str) -> Dict[str, float]:
        """
        Extract comprehensive performance metrics from VTune result directory.
        
        Uses VTune's -report command to extract metrics from the result bundle.
        Extracts all available metrics including:
        - Timing metrics (elapsed_time, cpu_time)
        - CPU metrics (CPI, IPC, CPU utilization)
        - Cache metrics (L1/L2/L3 hit/miss rates)
        - Memory metrics (bandwidth, latency)
        - Branch prediction metrics
        - Pipeline metrics
        
        Args:
            result_path: Path to VTune result directory
            workload_id: Workload identifier
        
        Returns:
            Dictionary of performance metrics
        
        Raises:
            RuntimeError: If metrics cannot be extracted from VTune results
        """
        metrics = {}
        
        # First, try to extract using VTune's -report command (most reliable)
        try:
            # Generate summary report in text format
            cmd = [
                self.vtune_path,
                '-report', 'summary',
                '-result-dir', str(result_path),
                '-format', 'text'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse the summary report
                report_content = result.stdout
                
                # Extract timing metrics from report
                patterns = {
                    'elapsed_time': r'Elapsed Time[:\s]+([\d.]+)\s*(?:sec|seconds?)?',
                    'cpu_time': r'CPU Time[:\s]+([\d.]+)\s*(?:sec|seconds?)?',
                    'cpu_utilization': r'CPU Utilization[:\s]+([\d.]+)%?',
                    'cpi': r'CPI Rate[:\s]+([\d.]+)',
                    'ipc': r'IPC Rate[:\s]+([\d.]+)',
                    'instructions_retired': r'Instructions Retired[:\s]+([\d.e+\-]+)',
                    'cpu_clocks': r'CPU Clocks[:\s]+([\d.e+\-]+)',
                    'l1_cache_hits': r'L1.*?hit[^s]*[:\s]+([\d.e+\-]+)',
                    'l1_cache_misses': r'L1.*?miss[^s]*[:\s]+([\d.e+\-]+)',
                    'l2_cache_hits': r'L2.*?hit[^s]*[:\s]+([\d.e+\-]+)',
                    'l2_cache_misses': r'L2.*?miss[^s]*[:\s]+([\d.e+\-]+)',
                    'l3_cache_hits': r'L3.*?hit[^s]*[:\s]+([\d.e+\-]+)',
                    'l3_cache_misses': r'L3.*?miss[^s]*[:\s]+([\d.e+\-]+)',
                    'memory_bandwidth': r'Memory Bandwidth[:\s]+([\d.]+)\s*([GMK]?B/s)?',
                    'branch_mispredictions': r'Branch Mispredictions?[:\s]+([\d.e+\-]+)',
                    'branch_predictions': r'Branch Predictions?[:\s]+([\d.e+\-]+)',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, report_content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        try:
                            value = float(match.group(1))
                            metrics[key] = value
                        except (ValueError, IndexError):
                            pass
        except subprocess.TimeoutExpired:
            pass  # Try other methods
        except Exception as e:
            pass  # Try other methods
        
        # Also try to extract from XML bundle file if it exists
        vtune_bundle = list(result_path.glob('*.vtune'))
        if vtune_bundle:
            try:
                tree = ET.parse(vtune_bundle[0])
                root = tree.getroot()
                
                # Extract metrics from XML (VTune XML structure)
                for elem in root.iter():
                    tag = elem.tag.lower()
                    text = elem.text
                    
                    # Look for common metric tags
                    if text and any(keyword in tag for keyword in ['metric', 'value', 'count', 'rate', 'time']):
                        try:
                            value = float(text)
                            metric_name = tag.replace('{', '').replace('}', '').split('}')[-1].lower()
                            if metric_name not in metrics:
                                metrics[metric_name] = value
                        except (ValueError, AttributeError):
                            pass
                    
                    # Extract attributes that might contain metrics
                    for attr_name, attr_value in elem.attrib.items():
                        if any(keyword in attr_name.lower() for keyword in ['value', 'count', 'rate', 'time']):
                            try:
                                value = float(attr_value)
                                metric_name = attr_name.lower().replace('-', '_')
                                if metric_name not in metrics:
                                    metrics[metric_name] = value
                            except ValueError:
                                pass
            except Exception:
                pass
        
        # Try to extract from summary.txt if it exists (legacy format)
        summary_file = result_path / 'summary.txt'
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Extract timing metrics
                    patterns = {
                        'elapsed_time': r'Elapsed Time:\s+([\d.]+)\s+sec',
                        'cpu_time': r'CPU Time:\s+([\d.]+)\s+sec',
                        'cpu_utilization': r'CPU Utilization:\s+([\d.]+)%',
                        'cpi': r'CPI Rate:\s+([\d.]+)',
                        'ipc': r'IPC Rate:\s+([\d.]+)',
                        'instructions_retired': r'Instructions Retired:\s+([\d.e+\-]+)',
                        'cpu_clocks': r'CPU Clocks:\s+([\d.e+\-]+)',
                    }
                    
                    for key, pattern in patterns.items():
                        if key not in metrics:  # Don't overwrite existing metrics
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                try:
                                    metrics[key] = float(match.group(1))
                                except ValueError:
                                    pass
            except Exception:
                pass
        
        # Calculate derived metrics
        if 'cpu_clocks' in metrics and 'instructions_retired' in metrics:
            if metrics['instructions_retired'] > 0:
                metrics['cpi'] = metrics['cpu_clocks'] / metrics['instructions_retired']
                metrics['ipc'] = metrics['instructions_retired'] / metrics['cpu_clocks']
        
        if 'l1_cache_hits' in metrics and 'l1_cache_misses' in metrics:
            total_l1 = metrics['l1_cache_hits'] + metrics['l1_cache_misses']
            if total_l1 > 0:
                metrics['l1_cache_hit_rate'] = metrics['l1_cache_hits'] / total_l1
                metrics['l1_cache_miss_rate'] = metrics['l1_cache_misses'] / total_l1
        
        if 'l2_cache_hits' in metrics and 'l2_cache_misses' in metrics:
            total_l2 = metrics['l2_cache_hits'] + metrics['l2_cache_misses']
            if total_l2 > 0:
                metrics['l2_cache_hit_rate'] = metrics['l2_cache_hits'] / total_l2
                metrics['l2_cache_miss_rate'] = metrics['l2_cache_misses'] / total_l2
        
        if 'branch_predictions' in metrics and 'branch_mispredictions' in metrics:
            total_branches = metrics['branch_predictions'] + metrics['branch_mispredictions']
            if total_branches > 0:
                metrics['branch_misprediction_rate'] = metrics['branch_mispredictions'] / total_branches
                metrics['branch_prediction_accuracy'] = metrics['branch_predictions'] / total_branches
        
        # Ensure we have execution_time (primary metric)
        if 'elapsed_time' in metrics:
            metrics['execution_time'] = metrics['elapsed_time']
        elif 'cpu_time' in metrics:
            metrics['execution_time'] = metrics['cpu_time']
        
        # If no metrics found, raise an error instead of returning defaults
        if not metrics or 'execution_time' not in metrics:
            raise RuntimeError(
                f"Failed to extract metrics from VTune results for {workload_id}. "
                f"Result directory: {result_path}. "
                f"VTune may not have completed profiling successfully."
            )
        
        # Mark source as VTune
        metrics['_source'] = 'vtune'
        
        return metrics
    
    def cleanup_results(self, keep_latest: int = 10):
        """Clean up old VTune result directories."""
        if not self.results_dir.exists():
            return
        
        result_dirs = sorted(
            [d for d in self.results_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_dir in result_dirs[keep_latest:]:
            import shutil
            shutil.rmtree(old_dir)
