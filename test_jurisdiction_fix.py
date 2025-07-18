#!/usr/bin/env python3

import sys
sys.path.append('src')

from courtfinder.models import Court
from import_ALL_freelaw_data_FIXED import parse_court_row

# Test data with empty jurisdiction (like the real data)
test_rows = [
    {
        'id': 'test1',
        'full_name': 'Test Court 1',
        'short_name': 'TC1',
        'jurisdiction': 'S',  # Has jurisdiction
        'position': '1.0',
        'citation_string': 'TC1',
        'start_date': '',
        'end_date': '',
        'notes': ''
    },
    {
        'id': 'test2', 
        'full_name': 'Test Court 2',
        'short_name': 'TC2',
        'jurisdiction': '',  # Empty jurisdiction - should work now
        'position': '2.0',
        'citation_string': 'TC2',
        'start_date': '',
        'end_date': '',
        'notes': ''
    }
]

print("Testing jurisdiction fix...")

for i, row in enumerate(test_rows, 1):
    try:
        court = parse_court_row(row)
        print(f"✅ Row {i}: SUCCESS - Court '{court.full_name}' with jurisdiction '{court.jurisdiction}'")
    except Exception as e:
        print(f"❌ Row {i}: FAILED - {e}")

print("\nDone!")