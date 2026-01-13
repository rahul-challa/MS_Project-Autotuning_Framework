# Search Space Analysis

## Configuration Space

### Total Possible Configurations

With 6 parameters:
- **ROB Size**: 7 options (64, 96, 128, 160, 192, 224, 256)
- **L1 Cache Size**: 7 options (32, 48, 64, 80, 96, 112, 128 KB)
- **L2 Cache Size**: 7 options (128, 192, 256, 320, 384, 448, 512 KB)
- **Issue Width**: 7 options (2, 3, 4, 5, 6, 7, 8)
- **L1 Latency**: 3 options (2, 3, 4 cycles)
- **L2 Latency**: 7 options (8, 10, 11, 12, 13, 14, 16 cycles)

**Total**: 7 × 7 × 7 × 7 × 3 × 7 = **50,421 configurations**

## Search Coverage by Iterations

| Iterations | Unique Configs Tested | Coverage | Matches | Best Found At |
|------------|---------------------|----------|---------|---------------|
| 500 | ~500 | ~1.0% | 1/6 (16.7%) | 378 |
| 1000 | ~1000 | ~2.0% | 3/6 (50.0%) | 547 |
| 3000 | ~3000 | ~6.0% | 2/6 (33.3%) | 2097 |
| 5000 | ~5000 | ~9.9% | 4/6 (66.7%) | 2709 |
| 10000 | 10,000 | 19.8% | 2/6 (33.3%) | 815 |

## Key Observations

### 1. UCB1 Efficiency

- **1.00 configurations per iteration**: UCB1 efficiently explores unique configurations
- **No redundancy**: Each iteration tests a different configuration
- **Smart exploration**: UCB1 balances exploration vs exploitation

### 2. Coverage vs Accuracy

- **More iterations ≠ Better accuracy**: 
  - 5000 iterations: 66.7% match (best so far)
  - 10000 iterations: 33.3% match (lower)
  
- **Best result found early**: Often found within first 1000-3000 iterations
- **Diminishing returns**: After finding a good solution, more iterations may explore worse regions

### 3. Search Space Size

- **50,421 total configurations**: Large but manageable
- **19.8% coverage with 10,000 iterations**: Still 80% unexplored
- **UCB1 advantage**: Focuses on promising regions, doesn't need exhaustive search

## Recommendations

### For Best Results

1. **Run multiple times** (5-10 runs) with 5000 iterations
2. **Take best result** across all runs
3. **Use ensemble**: Combine top results from multiple runs

### For Maximum Coverage

1. **10,000+ iterations**: Explore more of search space
2. **Different random seeds**: Ensure different exploration paths
3. **Hybrid approach**: Combine UCB1 with random sampling

### Expected Coverage

- **1,000 iterations**: ~2% coverage
- **5,000 iterations**: ~10% coverage  
- **10,000 iterations**: ~20% coverage
- **25,000 iterations**: ~50% coverage
- **Full coverage**: 50,421 iterations (exhaustive)

## Why UCB1 is Efficient

UCB1 doesn't need to test all configurations because:
1. **Exploration phase**: Tests diverse configurations initially
2. **Exploitation phase**: Focuses on promising regions
3. **Confidence bounds**: Guides search to high-reward areas
4. **Statistical efficiency**: Finds good solutions with ~10-20% coverage

## Conclusion

- **Total configurations**: 50,421
- **10,000 iterations**: Tests 10,000 unique configurations (19.8% coverage)
- **UCB1 efficiency**: 1.00 configurations per iteration (no redundancy)
- **Best strategy**: Run multiple times with 5000 iterations, take best result
