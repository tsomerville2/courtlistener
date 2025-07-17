#!/usr/bin/env python3
"""Import only people data"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

from courtfinder.storage import CourtFinderStorage

# Import parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

# Create storage
storage = CourtFinderStorage('real_data')

# Import people only
file_path = Path('downloads/people-db-people-2024-12-31.csv.bz2')
print(f"📥 Importing people from {file_path.name}...")

result = import_data_type(storage, file_path, "people", parse_person_row, storage.save_person, limit=1000)

if result['success']:
    print(f"✅ Successfully imported {result['imported_count']} people")
    print(f"⚠️  {result['error_count']} errors")
else:
    print(f"❌ Failed: {result.get('error', 'Unknown error')}")

# Show final stats
stats = storage.get_storage_stats()
people_info = stats.get('people', {})
if isinstance(people_info, dict):
    print(f"\nFinal people count: {people_info.get('total_items', 0)}")
else:
    print(f"\nFinal people count: {people_info}")