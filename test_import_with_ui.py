#!/usr/bin/env python3
"""
Test import with UI - demonstrates the progress display
"""

import subprocess
import sys

print("🚀 Testing Import with Progress UI")
print("=" * 50)
print("This will import a small sample with the progress display")
print("Press Ctrl+C to stop at any time")
print("=" * 50)
print()

# Run import with UI flag
cmd = [sys.executable, "import_ALL_freelaw_data_FIXED.py", "--ui"]
print(f"Running: {' '.join(cmd)}")
print()

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n\n⚠️  Import interrupted by user")