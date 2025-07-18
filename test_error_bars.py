#!/usr/bin/env python3

import sys
sys.path.append('src')
import time
from import_progress import ImportProgress
from import_ui_rich import ImportUIRich

# Test the error progress bars
print("Testing error progress bars...")

progress = ImportProgress()
ui = ImportUIRich(progress)
ui.start()

# Simulate mixed successes and errors
print("Simulating processing with errors...")
for i in range(50):
    if i % 7 == 0:  # Every 7th record has missing ID
        ui.add_error(f"Error processing row {i}: Court ID is required")
    elif i % 11 == 0:  # Every 11th record has missing name
        ui.add_error(f"Error processing row {i}: Court full name is required")
    elif i % 23 == 0:  # Every 23rd record has other error
        ui.add_error(f"Error processing row {i}: Invalid date format")
    else:  # Success
        ui.add_success()
    
    time.sleep(0.1)

print("\nLet it run for a few seconds to see the bars...")
time.sleep(5)

ui.stop()
print("Done!")