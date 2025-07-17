#!/usr/bin/env python3
"""
Download CourtListener bulk data files manually
Run this script to download real bz2 files from CourtListener S3 bucket
"""

import subprocess
import os
from pathlib import Path

def download_file(url, filename):
    """Download a file using curl"""
    print(f"Downloading {filename}...")
    print(f"URL: {url}")
    
    # Create downloads directory if it doesn't exist
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    output_path = downloads_dir / filename
    
    # Use curl to download
    cmd = [
        "curl", "-L", url, 
        "-o", str(output_path),
        "--progress-bar",
        "--continue-at", "-"  # Resume if interrupted
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"✅ Downloaded: {filename} ({size:,} bytes)")
            return True
        else:
            print(f"❌ Failed: {filename}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def main():
    print("🏛️  CourtListener Bulk Data Downloader")
    print("=" * 50)
    
    base_url = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data"
    date = "2024-12-31"  # Latest available date
    
    # Files to download with descriptions
    files = [
        (f"courts-{date}.csv.bz2", "Court metadata (~79KB)"),
        (f"people-{date}.csv.bz2", "Judge information (~1-5MB)"),
        (f"opinion-clusters-{date}.csv.bz2", "Opinion metadata (~100-500MB)"),
        (f"opinions-{date}.csv.bz2", "Full opinion text (~1-2GB)"),
        (f"citations-{date}.csv.bz2", "Citation data (~1-2GB)"),
        (f"dockets-{date}.csv.bz2", "Case dockets (~4GB)"),
    ]
    
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    print("Checking existing files and downloading missing ones...")
    print()
    
    successful = 0
    failed = 0
    skipped = 0
    
    for filename, description in files:
        file_path = downloads_dir / filename
        
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"⏭️  SKIP: {filename} - already exists ({size:,} bytes)")
            skipped += 1
            continue
        
        print(f"📥 DOWNLOADING: {description}")
        url = f"{base_url}/{filename}"
        if download_file(url, filename):
            successful += 1
        else:
            failed += 1
        print()
    
    print(f"\nDownload Summary:")
    print(f"✅ Downloaded: {successful}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    
    # Show what we have
    print(f"\nAll files in downloads/ directory:")
    total_size = 0
    for file in sorted(downloads_dir.glob("*.bz2")):
        size = file.stat().st_size
        total_size += size
        print(f"  📄 {file.name} ({size:,} bytes)")
    
    print(f"\nTotal downloaded: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()