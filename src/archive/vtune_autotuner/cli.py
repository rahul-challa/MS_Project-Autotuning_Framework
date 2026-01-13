"""
Command-line interface for VTune/EMON Autotuning Framework
"""

import sys
import argparse
from pathlib import Path
import json
import time
import os

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from .config import Config
from .discovery import VTuneMetricsDiscovery
from .benchmarks import BenchmarkWorkloads
from .autotuner import (
    run_autotuning,
    create_convergence_plot,
    predict_cpu_parameters,
    load_vtune_discovery
)


def setup_environment():
    """Set up the environment (discovery, benchmarks, ground truth)."""
    print("="*60)
    print("VTune/EMON Autotuning Framework - Setup")
    print("="*60)
    
    # 1. Discover VTune capabilities
    print("\n[1/3] Discovering VTune metrics and capabilities...")
    try:
        discovery = VTuneMetricsDiscovery()
        discovery_results = discovery.save_discovery(str(Config.VTUNE_DISCOVERY_FILE))
        print(f"  [OK] Discovery complete: {len(discovery_results.get('analysis_types', []))} analysis types found")
    except Exception as e:
        print(f"  [ERROR] Discovery failed: {e}")
        print("  Continuing with default parameters...")
        discovery_results = {}
    
    # 2. Create benchmark workloads
    print("\n[2/3] Creating benchmark workloads...")
    try:
        workloads = BenchmarkWorkloads()
        for workload_id in Config.DEFAULT_WORKLOADS:
            workloads.create_benchmark_executable(workload_id, Config.BENCHMARKS_DIR)
        print(f"  [OK] Created {len(Config.DEFAULT_WORKLOADS)} benchmark scripts")
    except Exception as e:
        print(f"  [ERROR] Failed to create benchmarks: {e}")
        return False
    
    # 3. Generate ground truth
    print("\n[3/3] Generating ground truth execution times...")
    try:
        if not Config.GROUND_TRUTH_FILE.exists():
            workloads = BenchmarkWorkloads()
            workloads.save_ground_truth(str(Config.GROUND_TRUTH_FILE), iterations=3)
            print(f"  [OK] Ground truth generated")
        else:
            print(f"  [OK] Ground truth already exists (skipping)")
    except Exception as e:
        print(f"  [ERROR] Failed to generate ground truth: {e}")
        return False
    
    print("\n" + "="*60)
    print("Setup complete! Ready to run autotuning.")
    print("="*60)
    return True


def verify_setup():
    """Verify that the framework is properly set up."""
    print("="*60)
    print("VTune/EMON Autotuning Framework - Setup Verification")
    print("="*60)
    
    checks = []
    
    # Check Python packages
    print("\nChecking Python packages...")
    try:
        import numpy
        import matplotlib
        print("  [OK] numpy")
        print("  [OK] matplotlib")
        checks.append(True)
    except ImportError as e:
        print(f"  [ERROR] Missing package: {e}")
        checks.append(False)
    
    # Check VTune
    print("\nChecking Intel VTune Profiler...")
    try:
        discovery = VTuneMetricsDiscovery()
        if discovery.check_vtune_available():
            print(f"  [OK] VTune found: {discovery.vtune_path}")
            checks.append(True)
        else:
            print(f"  [ERROR] VTune found but not accessible")
            checks.append(False)
    except FileNotFoundError as e:
        print(f"  [ERROR] VTune not found: {e}")
        checks.append(False)
    
    # Check EMON
    print("\nChecking Intel EMON...")
    try:
        from .emon_runner import EMONRunner
        runner = EMONRunner()
        print(f"  [OK] EMON found: {runner.emon_path}")
        checks.append(True)
    except FileNotFoundError as e:
        print(f"  [ERROR] EMON not found: {e}")
        checks.append(False)
    
    print("\n" + "="*60)
    if all(checks):
        print("[SUCCESS] All checks passed! Framework is ready to use.")
        return 0
    else:
        print("[WARNING] Some checks failed. Please fix the issues above.")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VTune/EMON Autotuning Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup environment (discovery, benchmarks, ground truth)
  vtune-autotune --setup
  
  # Run autotuning with default parameters
  vtune-autotune --run
  
  # Run autotuning with custom iterations
  vtune-autotune --run --iterations 100
  
  # Run autotuning without EMON
  vtune-autotune --run --no-emon
  
  # Setup and run in one command
  vtune-autotune --setup --run
        """
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Set up environment (discover VTune, create benchmarks, generate ground truth)'
    )
    
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run autotuning process'
    )
    
    parser.add_argument(
        '--iterations',
        type=int,
        default=Config.DEFAULT_MAX_ITERATIONS,
        help=f'Maximum number of autotuning iterations (default: {Config.DEFAULT_MAX_ITERATIONS})'
    )
    
    parser.add_argument(
        '--no-emon',
        action='store_true',
        help='Disable EMON (use only VTune)'
    )
    
    parser.add_argument(
        '--vtune-path',
        type=str,
        help='Custom path to VTune executable'
    )
    
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Run complete evaluation: autotuning + prediction + comparison with actual CPU parameters'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify setup (check VTune, EMON, Python packages)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not (args.setup or args.run or args.evaluate or args.verify):
        parser.print_help()
        return
    
    # Handle verify mode
    if args.verify:
        result = verify_setup()
        sys.exit(result)
    
    # Handle evaluation mode
    if args.evaluate:
        from .evaluate_predictions import evaluate_framework
        from .cpu_info_extractor import CPUInfoExtractor
        from .autotuner import predict_cpu_parameters, load_vtune_discovery
        
        print("\n" + "="*60)
        print("VTune/EMON Autotuning Framework - Complete Evaluation")
        print("="*60)
        
        # Extract actual CPU parameters
        print("\n[Step 1/4] Extracting actual CPU parameters...")
        extractor = CPUInfoExtractor()
        actual = extractor.get_actual_parameters()
        
        print("\nActual CPU Parameters:")
        for key, value in actual.items():
            if value is not None:
                print(f"  {key}: {value}")
        
        # Run autotuning if needed
        if not Config.GROUND_TRUTH_FILE.exists():
            print("\nGround truth not found. Running setup first...")
            if not setup_environment():
                print("\nSetup failed. Cannot proceed with evaluation.")
                sys.exit(1)
        
        print(f"\n[Step 2/4] Running autotuning ({args.iterations} iterations)...")
        best_config, best_error, error_history, collected_metrics = run_autotuning(
            max_iterations=args.iterations,
            use_emon=not args.no_emon
        )
        
        # Predict parameters
        print("\n[Step 3/4] Predicting CPU parameters...")
        discovery = load_vtune_discovery()
        predictions = predict_cpu_parameters(
            best_config,
            discovery,
            Config.BENCHMARKS_DIR,
            collected_metrics=collected_metrics
        )
        
        # Compare and evaluate
        print("\n[Step 4/4] Comparing predictions with actual...")
        comparison = evaluate_framework(
            predictions=predictions,
            output_dir=Config.RESULTS_DIR
        )
        
        print("\n" + "="*60)
        print("Evaluation Complete!")
        print("="*60)
        if "_summary" in comparison:
            summary = comparison["_summary"]
            print(f"\nFramework Accuracy: {summary['mean_accuracy']:.2f}%")
            print(f"Mean Relative Error: {summary['mean_relative_error']:.2f}%")
        
        return
    
    # Setup if requested
    if args.setup:
        if not setup_environment():
            print("\nSetup failed. Please fix errors and try again.")
            sys.exit(1)
    
    # Run autotuning if requested
    if args.run:
        print("\n" + "="*60)
        print("VTune/EMON Autotuning Framework - Running")
        print("="*60)
        
        # Check if setup was done
        if not Config.GROUND_TRUTH_FILE.exists():
            print("\nGround truth not found. Running setup first...")
            if not setup_environment():
                print("\nSetup failed. Cannot proceed with autotuning.")
                sys.exit(1)
        
        try:
            # Run autotuning
            best_config, best_error, error_history, collected_metrics = run_autotuning(
                max_iterations=args.iterations,
                use_emon=not args.no_emon
            )
            
            # Create visualization
            create_convergence_plot(error_history, best_error, best_config)
            
            # Predict CPU parameters
            discovery = load_vtune_discovery()
            predictions = predict_cpu_parameters(
                best_config, 
                discovery, 
                Config.BENCHMARKS_DIR,
                collected_metrics=collected_metrics
            )
            
            # Save results
            results = {
                "best_config": best_config,
                "best_error": best_error,
                "error_history": error_history,
                "predictions": predictions,
                "timestamp": time.time(),
                "iterations": args.iterations,
                "used_emon": not args.no_emon
            }
            
            results_file = Config.RESULTS_DIR / f"autotuning_results_{int(time.time())}.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print("\n" + "="*60)
            print("Autotuning Complete!")
            print("="*60)
            print(f"Best configuration: {best_config}")
            print(f"Minimum aggregate error: {best_error:.9f}")
            print(f"Total iterations: {len(error_history)}")
            print(f"Convergence plot: vtune_convergence.png")
            print(f"Results saved: {results_file}")
            print("\nCPU Parameter Predictions:")
            for param, value in predictions.items():
                print(f"  {param}: {value}")
            
        except KeyboardInterrupt:
            print("\n\nAutotuning interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n\nAutotuning failed with error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
