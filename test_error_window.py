#!/usr/bin/env python3

import sys
sys.path.append('src')
import time
from import_progress import ImportProgress
from import_ui_rich import ImportUIRich

# Test the rolling error window
print("Testing rolling error window...")

progress = ImportProgress()
ui = ImportUIRich(progress)

# Simulate multiple errors
errors = [
    "courts - Error processing row 100: Court ID is required",
    "courts - Error processing row 150: Court name is required", 
    "dockets - Error processing row 200: Docket number is required",
    "dockets - Error processing row 250: Court ID is required",
    "opinions - Error processing row 300: Opinion text is required"
]

for i, error in enumerate(errors):
    print(f"\nAdding error {i+1}:")
    ui.add_error(error)
    time.sleep(2)  # Pause to see the effect

print("\nDone!")