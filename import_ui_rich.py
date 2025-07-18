#!/usr/bin/env python3
"""
Rich-based UI for import progress visualization
Uses the Rich library which is more compatible and already installed
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
import time
import threading
from typing import Optional
from collections import deque
from import_progress import ImportProgress


class ImportUIRich:
    """Rich-based UI controller"""
    
    def __init__(self, progress_tracker: ImportProgress):
        self.progress = progress_tracker
        self.console = Console()
        self._stop_event = threading.Event()
        self._ui_thread = None
        self._errors = deque(maxlen=2)  # Keep only last 2 errors
        self._error_count = 0
        self._error_types = {}  # Track different error types
        self._total_processed = 0
        
    def start(self):
        """Start the UI display"""
        self._ui_thread = threading.Thread(target=self._run_ui)
        self._ui_thread.daemon = True
        self._ui_thread.start()
    
    def _run_ui(self):
        """Run the Rich UI"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=2
        ) as progress_bar:
            
            # Create tasks for each data type
            tasks = {}
            data_types = ["courts", "dockets", "opinion_clusters", "opinions", "citations", "people"]
            
            for data_type in data_types:
                tasks[data_type] = progress_bar.add_task(
                    f"[green]{data_type.replace('_', ' ').title()}",
                    total=100
                )
            
            # Add overall progress
            overall_task = progress_bar.add_task("[bold green]Overall Progress", total=100)
            
            # Add error tracking bars (red background bars showing actual error percentages)
            error_overall_task = progress_bar.add_task("[red]Error Rate %", total=20)  # Cap at 20% for visibility
            error_missing_id_task = progress_bar.add_task("[red]Missing ID %", total=20)  # Percentage of total records
            error_missing_name_task = progress_bar.add_task("[red]Missing Name %", total=20)  # Percentage of total records
            error_missing_other_task = progress_bar.add_task("[red]Other Errors %", total=20)  # Percentage of total records
            
            # Update loop
            while not self._stop_event.is_set():
                # Get overall stats
                overall = self.progress.get_overall_progress()
                
                # Calculate proper overall progress across all data types
                total_completed_data_types = 0
                active_data_types = 0
                
                # Update individual data types
                for data_type, task_id in tasks.items():
                    if data_type in self.progress.data_types:
                        stats = self.progress.data_types[data_type]
                        active_data_types += 1
                        
                        if stats['status'] == 'completed':
                            total_completed_data_types += 100
                            progress_bar.update(task_id, completed=100,
                                              description=f"[green]✅ {data_type.replace('_', ' ').title()} - {stats['imported']:,} records")
                        elif stats['estimated_total']:
                            percent = (stats['processed'] / stats['estimated_total'] * 100)
                            total_completed_data_types += percent
                            speed = self.progress.get_speed(data_type)
                            
                            # For very large files, show progress in K/M format if percentage is tiny
                            if percent < 0.1 and stats['processed'] > 100:
                                if stats['processed'] >= 1000000:
                                    processed_str = f"{stats['processed']/1000000:.1f}M"
                                elif stats['processed'] >= 1000:
                                    processed_str = f"{stats['processed']/1000:.0f}K"
                                else:
                                    processed_str = str(stats['processed'])
                                
                                if stats['estimated_total'] >= 1000000:
                                    total_str = f"{stats['estimated_total']/1000000:.1f}M"
                                elif stats['estimated_total'] >= 1000:
                                    total_str = f"{stats['estimated_total']/1000:.0f}K"
                                else:
                                    total_str = str(stats['estimated_total'])
                                
                                description = f"[green]{data_type.replace('_', ' ').title()} @ {speed:.0f}/s ({processed_str}/{total_str})"
                            else:
                                description = f"[green]{data_type.replace('_', ' ').title()} @ {speed:.0f}/s"
                            
                            progress_bar.update(task_id, completed=max(percent, 0.1),  # Show at least 0.1% for visibility
                                              description=description)
                        else:
                            progress_bar.update(task_id, completed=0,
                                              description=f"[yellow]{data_type.replace('_', ' ').title()} - Processing...")
                
                # Update overall progress (average across active data types)
                if active_data_types > 0:
                    overall_percent = total_completed_data_types / active_data_types
                    progress_bar.update(overall_task, completed=overall_percent)
                
                # Update error bars
                if self._total_processed > 0:
                    overall_error_rate = (self._error_count / self._total_processed) * 100
                    progress_bar.update(error_overall_task, completed=min(overall_error_rate, 20),
                                      description=f"[red]Error Rate: {overall_error_rate:.1f}% ({self._error_count}/{self._total_processed})")
                    
                    # Update specific error type bars - show percentage of total records
                    missing_id = self._error_types.get('missing_id', 0)
                    missing_name = self._error_types.get('missing_name', 0) 
                    other_errors = self._error_types.get('other', 0)
                    
                    # Calculate percentage of total records for each error type
                    id_percent = (missing_id / self._total_processed) * 100
                    name_percent = (missing_name / self._total_processed) * 100
                    other_percent = (other_errors / self._total_processed) * 100
                    
                    progress_bar.update(error_missing_id_task, completed=min(id_percent, 20),
                                      description=f"[red]Missing ID: {id_percent:.1f}% ({missing_id}/{self._total_processed})")
                    progress_bar.update(error_missing_name_task, completed=min(name_percent, 20),
                                      description=f"[red]Missing Name: {name_percent:.1f}% ({missing_name}/{self._total_processed})")
                    progress_bar.update(error_missing_other_task, completed=min(other_percent, 20),
                                      description=f"[red]Other: {other_percent:.1f}% ({other_errors}/{self._total_processed})")
                
                time.sleep(0.5)
    
    def stop(self):
        """Stop the UI"""
        self._stop_event.set()
        if self._ui_thread:
            self._ui_thread.join(timeout=1)
    
    def add_error(self, error_msg: str):
        """Add an error and categorize it for progress bars"""
        self._error_count += 1
        self._total_processed += 1
        
        # Categorize error type
        if "ID is required" in error_msg:
            self._error_types['missing_id'] = self._error_types.get('missing_id', 0) + 1
        elif "name is required" in error_msg or "Name is required" in error_msg:
            self._error_types['missing_name'] = self._error_types.get('missing_name', 0) + 1
        else:
            self._error_types['other'] = self._error_types.get('other', 0) + 1
    
    def add_success(self):
        """Track successful record processing"""
        self._total_processed += 1


def demo():
    """Demo the Rich UI"""
    import random
    
    # Create progress tracker
    progress = ImportProgress()
    
    # Create and start UI
    ui = ImportUIRich(progress)
    ui.start()
    
    # Simulate import progress
    data_types = [
        ("courts", 2000),
        ("dockets", 500000),
        ("opinion_clusters", 100000),
        ("opinions", 1000000),
        ("citations", 2000000),
        ("people", 10000)
    ]
    
    try:
        for data_type, total in data_types:
            progress.start_data_type(data_type, f"downloads/{data_type}.csv.bz2", total)
            
            # Simulate processing
            for i in range(0, min(total, 10000) + 1, 1000):
                progress.update_progress(data_type, i, int(i * 0.95), int(i * 0.05))
                
                # Simulate some errors
                if random.random() < 0.01:
                    ui.add_error(f"Error processing {data_type} row {i}: Invalid data")
                
                time.sleep(0.1)  # Simulate processing time
                    
            progress.finish_data_type(data_type)
            time.sleep(0.5)
        
        # Let it run for a bit more
        time.sleep(2)
    
    except KeyboardInterrupt:
        pass
    finally:
        ui.stop()
        print("\nDemo completed!")


if __name__ == "__main__":
    demo()