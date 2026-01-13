#!/usr/bin/env python3
"""
Main entry point for the Autotuning Framework
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from interfaces.cli import main

if __name__ == '__main__':
    main()
