#!/usr/bin/env python3
"""
Simple script to run the Identity Circuit Factory CLI.
This avoids import issues by running the module properly.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from identity_factory.cli import main

if __name__ == "__main__":
    main() 