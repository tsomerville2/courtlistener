#!/usr/bin/env python3
"""Test people parsing directly"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

# Import necessary modules
from courtfinder.models import Person
from datetime import datetime, date
from typing import Dict, Optional
import bz2
import csv

# Import parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

# Test with sample data
test_row = {
    'id': '`7607`',
    'date_created': '`2016-04-20 15:28:29.008834+00`',
    'date_modified': '`2018-06-27 21:22:40.185313+00`',
    'name_first': '`Robert`',
    'name_middle': '`P.`',
    'name_last': '`Young`',
    'name_suffix': '`jr`',
    'has_photo': '`f`',
    'is_alias_of_id': '`4803`',
    'date_dob': '',
    'date_granularity_dob': '',
    'date_dod': '',
    'date_granularity_dod': '',
    'dob_city': '',
    'dob_state': '',
    'dod_city': '',
    'dod_state': '',
    'gender': '',
    'religion': '',
    'ftm_total_received': '',
    'ftm_eid': ''
}

try:
    person = parse_person_row(test_row)
    print(f'✅ Parsed person: {person.id} - {person.name_first} {person.name_last}')
    print(f'   Has photo: {person.has_photo}')
    print(f'   Is alias of: {person.is_alias_of}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

# Now test with actual file
print("\n📥 Testing with actual file...")
file_path = Path('downloads/people-db-people-2024-12-31.csv.bz2')
if file_path.exists():
    with bz2.open(file_path, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        success_count = 0
        error_count = 0
        
        for i, row in enumerate(reader):
            if i >= 10:  # Test first 10 rows
                break
            
            try:
                person = parse_person_row(row)
                success_count += 1
                if i == 0:
                    print(f"First person: {person.get_full_name()}")
            except Exception as e:
                error_count += 1
                print(f"Error on row {i+1}: {e}")
        
        print(f"\n✅ Successfully parsed {success_count} people")
        print(f"⚠️  Errors: {error_count}")
else:
    print("❌ People file not found")