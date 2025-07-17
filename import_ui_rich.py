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
from import_progress import ImportProgress


class ImportUIRich:
    """Rich-based UI controller"""
    
    def __init__(self, progress_tracker: ImportProgress):
        self.progress = progress_tracker
        self.console = Console()
        self._stop_event = threading.Event()
        self._ui_thread = None
        
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
                    f"[cyan]{data_type.replace('_', ' ').title()}",
                    total=100
                )
            
            # Add overall progress
            overall_task = progress_bar.add_task("[bold magenta]Overall Progress", total=100)
            
            # Update loop
            while not self._stop_event.is_set():
                # Get overall stats
                overall = self.progress.get_overall_progress()
                
                # Update overall progress
                progress_bar.update(overall_task, completed=overall['overall_percent'])
                
                # Update individual data types
                for data_type, task_id in tasks.items():
                    if data_type in self.progress.data_types:
                        stats = self.progress.data_types[data_type]
                        
                        if stats['status'] == 'completed':
                            progress_bar.update(task_id, completed=100,
                                              description=f"[green]✅ {data_type.replace('_', ' ').title()} - {stats['imported']:,} records")
                        elif stats['estimated_total']:
                            percent = (stats['processed'] / stats['estimated_total'] * 100)
                            speed = self.progress.get_speed(data_type)
                            progress_bar.update(task_id, completed=percent,
                                              description=f"[cyan]{data_type.replace('_', ' ').title()} @ {speed:.0f}/s")
                        else:
                            progress_bar.update(task_id, completed=0,
                                              description=f"[yellow]{data_type.replace('_', ' ').title()} - Processing...")
                
                time.sleep(0.5)
    
    def stop(self):
        """Stop the UI"""
        self._stop_event.set()
        if self._ui_thread:
            self._ui_thread.join(timeout=1)
    
    def add_error(self, error_msg: str):
        """Add an error to the display"""
        # In Rich version, we'll just print errors to console
        self.console.print(f"[red]❌ {error_msg}[/red]")


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