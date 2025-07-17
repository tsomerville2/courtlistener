#!/usr/bin/env python3
"""
Test to understand the CSV structure and find a better parsing approach
"""

import bz2
import csv
from pathlib import Path

def analyze_csv_structure():
    """Analyze the CSV structure to understand the format"""
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("❌ Opinion file not found")
        return
    
    print("🔍 Analyzing CSV structure...")
    
    with bz2.open(file_path, 'rt', encoding='utf-8') as f:
        # Get header
        header = f.readline().strip()
        print(f"Header: {header}")
        
        columns = header.split(',')
        print(f"Number of columns: {len(columns)}")
        
        # Look at the first few bytes to understand the format
        print("\n📝 First few data lines:")
        
        line_count = 0
        for line in f:
            line_count += 1
            if line_count > 5:
                break
            
            print(f"Line {line_count}: {line[:200]}...")
            
            # Try to count commas vs backticks
            comma_count = line.count(',')
            backtick_count = line.count('`')
            
            print(f"  Commas: {comma_count}, Backticks: {backtick_count}")
            
            # Check if it starts with backtick
            starts_with_backtick = line.strip().startswith('`')
            print(f"  Starts with backtick: {starts_with_backtick}")
            
            print()

if __name__ == "__main__":
    analyze_csv_structure()