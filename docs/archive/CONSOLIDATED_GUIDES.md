# Consolidated Documentation

This document consolidates information from various guide files.

## Installation & Setup

See main README.md for installation instructions.

## Methodology

The framework uses a **performance-based prediction** approach:
1. Collect ground truth performance metrics using VTune
2. Use Multi-Armed Bandit (UCB1) to search parameter space
3. Predict parameters that best match observed performance
4. Validate against actual parameters (not used during optimization)

## Accuracy Improvement Strategies

### Multi-Metric Approach
- Use all available VTune metrics (execution time, CPI, cache misses, etc.)
- Weight metrics based on their importance
- Aggregate errors across all metrics

### Sequential Tuning
- Tune one parameter at a time
- Use multiple rounds for refinement
- Recommended: 5 rounds × 5000 iterations per parameter

### Parameter Space Exploration
- Use UCB1 algorithm for efficient exploration
- Balance exploration vs exploitation
- Track convergence over iterations

## VTune Capabilities

See `docs/VTUNE_CAPABILITIES.md` for detailed information about:
- Supported collection types
- Available metrics
- Platform-specific limitations

## Architecture

See `ARCHITECTURE.md` for system design and component overview.
