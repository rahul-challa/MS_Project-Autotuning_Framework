#!/usr/bin/env python3
"""List all available workloads."""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autotuner.workload_registry import list_all_workloads

if __name__ == '__main__':
    list_all_workloads()
