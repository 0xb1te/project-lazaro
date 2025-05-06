#!/usr/bin/env python3
"""
Simple script to run the application from the command line.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the main function
from backend.run import main

if __name__ == "__main__":
    main() 