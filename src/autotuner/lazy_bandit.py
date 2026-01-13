#!/usr/bin/env python3
"""
Lazy UCB1 Bandit for Large Parameter Spaces

This module provides a lazy configuration generation approach for UCB1
that doesn't require generating all configurations upfront. Instead,
configurations are generated on-demand and tracked using a hash-based approach.
"""

import numpy as np
import random
import hashlib
from typing import Dict, List, Tuple, Optional
from itertools import product


class LazyUCB1Bandit:
    """
    UCB1 Bandit with lazy configuration generation.
    
    For extremely large parameter spaces (e.g., 16 parameters with ~3.5 trillion configs),
    generating all configurations upfront is infeasible. This class generates
    configurations on-demand and tracks them using hash-based indexing.
    """
    
    def __init__(self, tunable_params: Dict[str, List[int]], randomize_order: bool = True):
        """
        Initialize lazy UCB1 bandit.
        
        Args:
            tunable_params: Dictionary of parameter names to possible values
            randomize_order: If True, randomize initial configuration selection
        """
        self.tunable_params = tunable_params
        self.param_keys = list(tunable_params.keys())
        self.param_values = list(tunable_params.values())
        
        # Calculate total possible configurations
        self.total_configs = np.prod([len(v) for v in tunable_params.values()])
        
        # Hash-based tracking of tested configurations
        self.config_hash_to_index = {}  # Maps config hash to internal index
        self.index_to_config = {}  # Maps internal index to config dict
        self.next_index = 0
        
        # UCB1 state variables (indexed by internal index)
        self.counts = {}  # N_k(t): times arm k pulled
        self.values = {}  # Q_k(t): average reward (negative error)
        self.total_pulls = 0  # t: total pulls
        
        # Track unpulled configs (for initialization phase)
        self.unpulled_configs = []  # List of config hashes
        self.randomize_order = randomize_order
        
        print(f"Initialized Lazy UCB1 Bandit")
        print(f"  Total possible configurations: {self.total_configs:,}")
        print(f"  Configurations will be generated on-demand")
        print(f"  Using hash-based tracking for efficient lookups")
    
    def _hash_config(self, config: Dict[str, int]) -> str:
        """Generate a hash for a configuration."""
        # Create a deterministic string representation
        config_str = ','.join(f"{k}={v}" for k, v in sorted(config.items()))
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _get_or_create_index(self, config: Dict[str, int]) -> int:
        """Get internal index for a configuration, creating it if needed."""
        config_hash = self._hash_config(config)
        
        if config_hash not in self.config_hash_to_index:
            # New configuration - assign index
            index = self.next_index
            self.next_index += 1
            self.config_hash_to_index[config_hash] = index
            self.index_to_config[index] = config.copy()
            self.counts[index] = 0
            self.values[index] = 0.0
            return index
        
        return self.config_hash_to_index[config_hash]
    
    def _generate_random_config(self) -> Dict[str, int]:
        """Generate a random configuration."""
        config = {}
        for key, values in self.tunable_params.items():
            config[key] = random.choice(values)
        return config
    
    def _generate_smart_config(self) -> Dict[str, int]:
        """
        Generate a configuration using smart sampling.
        
        This can be extended to use various strategies:
        - Random sampling
        - Latin Hypercube Sampling
        - Focused sampling around promising regions
        """
        # For now, use random sampling
        # In the future, could use more sophisticated methods
        return self._generate_random_config()
    
    def select_arm(self) -> Tuple[Dict[str, int], int]:
        """
        Select next arm (configuration) using UCB1 algorithm.
        
        For unpulled arms, we generate new configurations on-demand.
        For pulled arms, we use UCB1 formula.
        
        Returns:
            Tuple of (configuration dict, arm_index)
        """
        self.total_pulls += 1
        
        # Initialization phase: pull some random configs first
        if len(self.config_hash_to_index) < min(100, self.total_configs):
            # Generate a new random configuration
            config = self._generate_smart_config()
            index = self._get_or_create_index(config)
            return config, index
        
        # UCB1 phase: select arm with highest upper confidence bound
        # Only consider arms that have been created (tested at least once)
        tested_indices = list(self.counts.keys())
        
        if not tested_indices:
            # Fallback: generate random config
            config = self._generate_random_config()
            index = self._get_or_create_index(config)
            return config, index
        
        # Calculate UCB values for all tested arms
        ucb_values = {}
        for index in tested_indices:
            if self.counts[index] == 0:
                ucb_values[index] = float('inf')
            else:
                # UCB1 formula: Q_k(t) + c * sqrt(ln(t) / N_k(t))
                # We use negative error, so higher value = lower error = better
                confidence_bound = np.sqrt(2 * np.log(self.total_pulls) / self.counts[index])
                ucb_values[index] = self.values[index] + confidence_bound
        
        # Select arm with highest UCB value
        best_index = max(ucb_values.keys(), key=lambda i: ucb_values[i])
        
        # With some probability, explore a new random configuration
        # This ensures we continue exploring the vast space
        exploration_prob = 0.1  # 10% chance to explore new config
        if random.random() < exploration_prob:
            config = self._generate_smart_config()
            index = self._get_or_create_index(config)
            return config, index
        
        # Otherwise, return the best arm
        return self.index_to_config[best_index].copy(), best_index
    
    def update(self, arm_index: int, error: float) -> None:
        """
        Update arm statistics after pulling.
        
        Args:
            arm_index: Internal index of the arm
            error: Performance error (lower is better)
        """
        if arm_index not in self.counts:
            # Initialize if not exists
            self.counts[arm_index] = 0
            self.values[arm_index] = 0.0
        
        # Update counts and values
        self.counts[arm_index] += 1
        n = self.counts[arm_index]
        
        # Update average reward (we use negative error as reward)
        # Lower error = higher reward
        reward = -error  # Negative error is the reward
        self.values[arm_index] = ((n - 1) * self.values[arm_index] + reward) / n
    
    def get_best_config(self) -> Dict[str, int]:
        """Get the configuration with the best (lowest) error."""
        if not self.values:
            # No configurations tested yet
            return self._generate_random_config()
        
        # Find index with best (highest) value (lowest error)
        best_index = max(self.values.keys(), key=lambda i: self.values[i])
        return self.index_to_config[best_index].copy()
    
    def get_num_tested_configs(self) -> int:
        """Get number of unique configurations tested."""
        return len(self.config_hash_to_index)
    
    def get_search_space_info(self) -> Dict[str, any]:
        """Get information about search space coverage."""
        return {
            'total_possible_configs': self.total_configs,
            'unique_configs_tested': len(self.config_hash_to_index),
            'coverage_percent': (len(self.config_hash_to_index) / self.total_configs * 100) if self.total_configs > 0 else 0,
            'total_pulls': self.total_pulls,
            'configs_tested_per_pull': len(self.config_hash_to_index) / self.total_pulls if self.total_pulls > 0 else 0
        }
