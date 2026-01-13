# Codebase Structure

## Directory Organization

```
MS_Project-Autotuning_Framework/
├── src/                          # Source code
│   ├── autotuner/               # Core autotuning modules
│   │   ├── mab_autotuner.py     # Main MAB autotuner
│   │   ├── sequential_tuner.py  # Sequential parameter tuning
│   │   ├── enhanced_performance_model.py
│   │   ├── system_profiler.py
│   │   └── ...
│   ├── interfaces/              # User interfaces
│   │   └── cli.py               # Command-line interface
│   └── vtune_autotuner/         # VTune integration (legacy)
│
├── scripts/                      # Utility scripts
│   ├── collect_ground_truth.py
│   ├── analyze_sequential_results.py
│   └── archive/                  # Old/unused scripts
│
├── data/                         # Data files
│   ├── benchmarks/              # Benchmark workloads
│   └── results/                 # Output results
│
├── docs/                         # Documentation
│   ├── README.md                # Documentation index
│   ├── VTUNE_CAPABILITIES.md
│   └── archive/                 # Old documentation
│
├── configs/                      # Configuration files
│   └── default_config.json
│
├── logs/                         # Temporary output files
│
├── main.py                       # Main entry point
├── README.md                     # Main documentation
└── requirements.txt              # Dependencies
```

## Key Files

### Entry Points
- `main.py` - Main CLI entry point
- `src/interfaces/cli.py` - CLI implementation

### Core Modules
- `src/autotuner/mab_autotuner.py` - Multi-Armed Bandit autotuner
- `src/autotuner/sequential_tuner.py` - Sequential tuning approach
- `src/autotuner/enhanced_performance_model.py` - Performance prediction model

### Scripts
- `scripts/collect_ground_truth.py` - Collect VTune ground truth
- `scripts/analyze_sequential_results.py` - Analyze tuning results

## Usage

See `README.md` for usage instructions.
