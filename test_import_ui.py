#!/usr/bin/env python3
"""
Test the import UI without actually importing data
"""

import subprocess
import sys

print("🎨 Testing Import UI")
print("=" * 50)
print("This will demonstrate the asciimatics progress UI")
print("Press 'q' in the UI to quit")
print("=" * 50)

# Run the demo
try:
    subprocess.run([sys.executable, "import_ui_asciimatics.py"])
except KeyboardInterrupt:
    print("\nDemo interrupted")