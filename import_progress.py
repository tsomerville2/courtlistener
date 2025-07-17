#!/usr/bin/env python3
"""
Progress tracking for imports with speed and ETA calculations
"""

import time
import psutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from collections import deque


class ImportProgress:
    """Tracks import progress with speed and ETA calculations"""
    
    def __init__(self):
        self.data_types = {}
        self.start_time = time.time()
        self.overall_start = time.time()
        
    def start_data_type(self, data_type: str, file_path: str, 
                       estimated_total: Optional[int] = None,
                       resume_from: int = 0) -> None:
        """Start tracking a data type"""
        self.data_types[data_type] = {
            'file_path': file_path,
            'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            'start_time': time.time(),
            'processed': resume_from,
            'imported': 0,
            'errors': 0,
            'estimated_total': estimated_total,
            'speed_samples': deque(maxlen=20),  # Last 20 speed samples
            'last_update': time.time(),
            'status': 'processing',
            'current_id': None
        }
    
    def update_progress(self, data_type: str, processed: int, 
                       imported: int, errors: int, current_id: str = None) -> None:
        """Update progress for a data type"""
        if data_type not in self.data_types:
            return
            
        stats = self.data_types[data_type]
        current_time = time.time()
        
        # Calculate speed
        time_delta = current_time - stats['last_update']
        if time_delta > 0:
            records_delta = processed - stats['processed']
            speed = records_delta / time_delta
            stats['speed_samples'].append(speed)
        
        # Update stats
        stats['processed'] = processed
        stats['imported'] = imported
        stats['errors'] = errors
        stats['last_update'] = current_time
        stats['current_id'] = current_id
    
    def finish_data_type(self, data_type: str) -> None:
        """Mark a data type as finished"""
        if data_type in self.data_types:
            self.data_types[data_type]['status'] = 'completed'
            self.data_types[data_type]['end_time'] = time.time()
    
    def get_speed(self, data_type: str) -> float:
        """Get current processing speed in records/second"""
        if data_type not in self.data_types:
            return 0.0
            
        samples = self.data_types[data_type]['speed_samples']
        if not samples:
            return 0.0
            
        # Use weighted average, recent samples weighted more
        weights = [i + 1 for i in range(len(samples))]
        weighted_sum = sum(s * w for s, w in zip(samples, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def get_eta(self, data_type: str) -> Optional[timedelta]:
        """Get estimated time to completion"""
        if data_type not in self.data_types:
            return None
            
        stats = self.data_types[data_type]
        speed = self.get_speed(data_type)
        
        if speed <= 0 or not stats['estimated_total']:
            return None
            
        remaining = stats['estimated_total'] - stats['processed']
        if remaining <= 0:
            return timedelta(0)
            
        seconds_remaining = remaining / speed
        return timedelta(seconds=int(seconds_remaining))
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def get_overall_progress(self) -> Dict[str, any]:
        """Get overall import progress"""
        total_processed = sum(dt['processed'] for dt in self.data_types.values())
        total_imported = sum(dt['imported'] for dt in self.data_types.values())
        total_errors = sum(dt['errors'] for dt in self.data_types.values())
        
        # Calculate overall percentage
        estimated_totals = [dt['estimated_total'] for dt in self.data_types.values() 
                          if dt['estimated_total']]
        if estimated_totals:
            total_estimated = sum(estimated_totals)
            overall_percent = (total_processed / total_estimated * 100) if total_estimated > 0 else 0
        else:
            overall_percent = 0
        
        # Calculate overall speed
        overall_speed = sum(self.get_speed(dt) for dt in self.data_types.keys())
        
        # Calculate overall ETA
        remaining_time = timedelta(0)
        for data_type in self.data_types:
            eta = self.get_eta(data_type)
            if eta and self.data_types[data_type]['status'] == 'processing':
                remaining_time += eta
        
        elapsed = timedelta(seconds=int(time.time() - self.overall_start))
        
        return {
            'total_processed': total_processed,
            'total_imported': total_imported,
            'total_errors': total_errors,
            'overall_percent': overall_percent,
            'overall_speed': overall_speed,
            'overall_eta': remaining_time,
            'elapsed_time': elapsed,
            'memory': self.get_memory_usage()
        }
    
    def format_eta(self, eta: Optional[timedelta]) -> str:
        """Format ETA for display"""
        if not eta:
            return "Unknown"
            
        total_seconds = int(eta.total_seconds())
        if total_seconds <= 0:
            return "Complete"
            
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_status_line(self, data_type: str) -> str:
        """Get a formatted status line for a data type"""
        if data_type not in self.data_types:
            return f"{data_type}: Not started"
            
        stats = self.data_types[data_type]
        speed = self.get_speed(data_type)
        eta = self.get_eta(data_type)
        
        if stats['status'] == 'completed':
            duration = timedelta(seconds=int(stats['end_time'] - stats['start_time']))
            return (f"{data_type}: ✅ Complete - {stats['imported']:,} imported, "
                   f"{stats['errors']:,} errors - took {duration}")
        
        if stats['estimated_total']:
            percent = (stats['processed'] / stats['estimated_total'] * 100)
            return (f"{data_type}: {percent:.1f}% - {stats['processed']:,}/{stats['estimated_total']:,} "
                   f"@ {speed:.0f}/s - ETA: {self.format_eta(eta)}")
        else:
            return (f"{data_type}: {stats['processed']:,} processed @ {speed:.0f}/s")


if __name__ == "__main__":
    # Test progress tracker
    import time
    
    progress = ImportProgress()
    
    # Simulate import
    progress.start_data_type("dockets", "downloads/dockets.csv.bz2", estimated_total=500000)
    
    for i in range(10):
        time.sleep(0.1)
        progress.update_progress("dockets", i * 1000, i * 950, i * 50)
        print(progress.get_status_line("dockets"))
    
    # Show overall progress
    overall = progress.get_overall_progress()
    print(f"\nOverall: {overall['overall_percent']:.1f}% - "
          f"Speed: {overall['overall_speed']:.0f}/s - "
          f"ETA: {progress.format_eta(overall['overall_eta'])}")