#!/usr/bin/env python3
"""
Command-Line Interface for the Autotuning Framework
"""

import argparse
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autotuner.mab_autotuner import create_convergence_plot
from autotuner.sequential_tuner import run_sequential_autotuning
from autotuner.benchmark_runner import BenchmarkRunner
from autotuner.workload_registry import get_all_workloads


def main():
    parser = argparse.ArgumentParser(
        description='Autotuning Framework for CPU Model Validation using Intel VTune Profiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run sequential autotuning (default: 5 rounds × 5000 iterations per parameter)
  python main.py

  # Run with custom settings
  python main.py --rounds 3 --iterations-per-param 3000

  # Collect ground truth using VTune
  python main.py collect-ground-truth

  # Collect ground truth for specific workloads
  python main.py collect-ground-truth --workloads w1_matrix_mult w2_bubble_sort
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Sequential autotune command (now the main/default)
    sequential_parser = subparsers.add_parser('autotune', 
                                             help='Run sequential autotuning (one parameter at a time) - DEFAULT',
                                             aliases=['sequential-autotune'])
    sequential_parser.add_argument(
        '--iterations-per-param',
        type=int,
        default=5000,
        help='Number of iterations per parameter (default: 5000)'
    )
    sequential_parser.add_argument(
        '--rounds',
        type=int,
        default=5,
        help='Number of rounds (default: 5). Each round tunes all parameters sequentially.'
    )
    sequential_parser.add_argument(
        '--use-multi-metric',
        action='store_true',
        default=True,
        help='Use all available metrics for better accuracy (default: True)'
    )
    sequential_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for results (default: data/results)'
    )
    
    # Collect ground truth command
    collect_parser = subparsers.add_parser('collect-ground-truth', 
                                          help='Collect ground truth using VTune')
    collect_parser.add_argument(
        '--workloads',
        nargs='+',
        default=None,
        help='Workload IDs to profile (default: all workloads)'
    )
    collect_parser.add_argument(
        '--all-collection-types',
        action='store_true',
        default=True,
        help='Use all VTune collection types for comprehensive metrics'
    )
    collect_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for ground truth JSON (default: data/results/vtune_ground_truth.json)'
    )
    
    args = parser.parse_args()
    
    # Default to sequential autotuning if no command specified
    if args.command is None:
        args.command = 'autotune'
        # Set defaults
        if not hasattr(args, 'rounds'):
            args.rounds = 5
        if not hasattr(args, 'iterations_per_param'):
            args.iterations_per_param = 5000
        if not hasattr(args, 'use_multi_metric'):
            args.use_multi_metric = True
        if not hasattr(args, 'output'):
            args.output = None
    
    if args.command in ['autotune', 'sequential-autotune']:
        print("=" * 70)
        print("Sequential Autotuning Framework - CPU Parameter Prediction")
        print("=" * 70)
        print("Tuning one parameter at a time for maximum accuracy")
        print("Predicting CPU parameters using ONLY performance metrics")
        print("(Actual parameters used only for validation at the end)")
        print()
        print(f"Configuration: {args.rounds} rounds × {args.iterations_per_param} iterations per parameter")
        print(f"Total iterations: {args.rounds * 16 * args.iterations_per_param:,}")
        print()
        
        # Run sequential autotuning
        best_config, best_error, error_history, actual_params, tuning_info = run_sequential_autotuning(
            iterations_per_param=args.iterations_per_param,
            num_rounds=args.rounds,
            use_multi_metric=args.use_multi_metric
        )
        
        # Create visualization
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = Path(__file__).parent.parent.parent / 'data' / 'results'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plot_path = output_dir / 'sequential_autotuning_convergence.png'
        create_convergence_plot(error_history, best_error, best_config, str(plot_path))
        
        # Save results
        results_file = output_dir / 'sequential_autotuning_results.json'
        import json
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(v) for v in obj]
            elif hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, (int, float, str, bool)) or obj is None:
                return obj
            else:
                return str(obj)
        
        with open(results_file, 'w') as f:
            json.dump({
                'best_config': convert_to_native(best_config),
                'best_error': float(best_error),
                'actual_parameters': convert_to_native(actual_params),
                'matches': tuning_info['final_matches'],
                'match_percent': tuning_info['final_match_percent'],
                'tuning_info': convert_to_native(tuning_info),
                'error_history': [float(e) for e in error_history]
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        print(f"Convergence plot saved to: {plot_path}")
        
    elif args.command == 'autotune':
        print("=" * 70)
        print("Autotuning Framework - CPU Parameter Prediction")
        print("=" * 70)
        print("Predicting CPU parameters using ONLY performance metrics")
        print("(Actual parameters used only for validation at the end)")
        print()
        
        # Run maximized autotuning (uses ONLY performance metrics)
        # Note: Actual parameters are NOT used during optimization, only for validation
        best_config, best_error, error_history, best_iteration, actual_params, match_history, search_info = run_maximized_autotuning(
            max_iterations=args.iterations,
            use_multi_metric=True
        )
        
        # Create visualization
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = Path(__file__).parent.parent.parent / 'data' / 'results'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plot_path = output_dir / 'autotuning_convergence.png'
        create_convergence_plot(error_history, best_error, best_config, str(plot_path))
        
        # Save results
        results_file = output_dir / 'autotuning_results.json'
        import json
        with open(results_file, 'w') as f:
            json.dump({
                'best_config': best_config,
                'actual_parameters': actual_params,
                'best_error': best_error,
                'best_iteration': best_iteration,
                'error_history': error_history,
                'match_history': match_history,
                'iterations': len(error_history),
                'use_multi_metric': True,
                'max_matches': max(match_history) if match_history else 0,
                'final_matches': match_history[-1] if match_history else 0,
                'search_space_info': {
                    'total_configs': int(search_info['total_configs']),
                    'unique_configs_tested': int(search_info['unique_configs_tested']),
                    'coverage_percent': float(search_info['coverage_percent']),
                    'iterations': int(search_info['iterations'])
                },
                'note': 'Parameters predicted using ONLY performance metrics. Actual parameters used only for validation.'
            }, f, indent=2)
        
        # Calculate match percentage
        matches = sum(1 for k in actual_params.keys() 
                     if best_config.get(k) == actual_params.get(k))
        match_pct = matches / len(actual_params) * 100
        
        print()
        print("=" * 70)
        print("Results Summary")
        print("=" * 70)
        print(f"Best configuration: {best_config}")
        print(f"Actual parameters: {actual_params}")
        print(f"Best found at iteration: {best_iteration}")
        print(f"Minimum performance error: {best_error:.9f}")
        print(f"Parameter matches (validation): {matches}/{len(actual_params)} ({match_pct:.1f}%)")
        print(f"Total iterations: {len(error_history)}")
        print(f"\nSearch Space Coverage:")
        print(f"  Total possible configurations: {search_info['total_configs']:,}")
        print(f"  Unique configurations tested: {search_info['unique_configs_tested']:,}")
        print(f"  Coverage: {search_info['coverage_percent']:.2f}% of search space")
        print(f"  Configurations per iteration: {search_info['unique_configs_tested']/len(error_history):.2f}")
        print(f"\nConvergence plot: {plot_path}")
        print(f"Results JSON: {results_file}")
        
        # Print parameter comparison
        print()
        print("Parameter Comparison:")
        print("-" * 70)
        print(f"{'Parameter':<20} {'Best Config':<15} {'Actual':<15} {'Match':<10}")
        print("-" * 70)
        for param in ['rob_size', 'l1_cache_size', 'l2_cache_size', 'issue_width', 'l1_latency', 'l2_latency']:
            best_val = best_config[param]
            actual_val = actual_params[param]
            match = "YES" if best_val == actual_val else "NO"
            print(f"{param:<20} {best_val:<15} {actual_val:<15} {match:<10}")
        print("-" * 70)
        
    elif args.command == 'collect-ground-truth':
        print("=" * 70)
        print("Collecting Ground Truth using Intel VTune Profiler")
        print("=" * 70)
        print()
        
        benchmark_runner = BenchmarkRunner()
        
        # Use ALL workloads if not specified
        if args.workloads is None:
            print(f"Using ALL workloads from registry (will collect for all {len(get_all_workloads())} workloads)")
        else:
            print(f"Using specified {len(args.workloads)} workloads")
        
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = Path(__file__).parent.parent.parent / 'data' / 'results' / 'ground_truth.json'
        
        ground_truth = benchmark_runner.collect_ground_truth(
            workload_ids=args.workloads,  # None = use ALL workloads
            output_file=output_file,
            use_all_collection_types=args.all_collection_types  # Use ALL collection types
        )
        
        print()
        print("=" * 70)
        print("Ground Truth Collection Complete")
        print("=" * 70)
        if args.workloads:
            print(f"Profiled {len(args.workloads)} workloads")
        else:
            print(f"Profiled all workloads from registry")
        print(f"Results saved to: {output_file}")
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
