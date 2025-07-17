#!/usr/bin/env python3
"""
Asciimatics UI for import progress visualization
"""

from asciimatics.widgets import Frame, Layout, Label, Divider, Text, TextBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.event import KeyboardEvent
import sys
import threading
import time
from datetime import datetime
from typing import Optional
from import_progress import ImportProgress


class ImportProgressFrame(Frame):
    """Main frame for import progress display"""
    
    def __init__(self, screen, progress_tracker: ImportProgress):
        super(ImportProgressFrame, self).__init__(
            screen,
            screen.height,
            screen.width,
            has_border=True,
            title="FreeLaw Data Import Progress",
            reduce_cpu=True
        )
        self.progress = progress_tracker
        self.error_log = []
        self._last_update = 0
        
        # Create the layout
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        
        # Title
        layout.add_widget(Label("Press 'q' to quit, 'p' to pause/resume", align="^"))
        layout.add_widget(Divider())
        
        # Overall progress
        self._overall_label = Label("Overall Progress: Initializing...", align="<")
        self._overall_progress_label = Label("[" + "░" * 50 + "] 0%", align="<")
        layout.add_widget(self._overall_label)
        layout.add_widget(self._overall_progress_label)
        layout.add_widget(Divider())
        
        # Individual data type progress bars
        self._data_type_widgets = {}
        data_types = ["courts", "dockets", "opinion_clusters", "opinions", "citations", "people"]
        
        for data_type in data_types:
            label = Label(f"{data_type.title()}: Waiting...", align="<")
            progress_label = Label("[" + "░" * 50 + "] 0%", align="<")
            self._data_type_widgets[data_type] = {
                'label': label,
                'progress_label': progress_label
            }
            layout.add_widget(label)
            layout.add_widget(progress_label)
        
        layout.add_widget(Divider())
        
        # Stats display
        self._speed_label = Label("Speed: 0 records/sec | Memory: 0MB", align="<")
        self._eta_label = Label("ETA: Unknown | Elapsed: 00:00:00", align="<")
        layout.add_widget(self._speed_label)
        layout.add_widget(self._eta_label)
        layout.add_widget(Divider())
        
        # Error log
        layout.add_widget(Label("Recent Errors:", align="<"))
        self._error_box = TextBox(height=5, as_string=True, readonly=True)
        layout.add_widget(self._error_box)
        
        # Fix the layout
        self.fix()
        
        # Set up refresh
        self._update_timer = None
        self._start_refresh()
    
    def _make_progress_bar(self, percent: float, width: int = 50) -> str:
        """Create a text-based progress bar"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent:.1f}%"
    
    def _start_refresh(self):
        """Start the refresh timer"""
        self._update_timer = threading.Timer(0.5, self._refresh_display)
        self._update_timer.daemon = True
        self._update_timer.start()
    
    def _refresh_display(self):
        """Refresh the display with current progress"""
        try:
            # Get overall stats
            overall = self.progress.get_overall_progress()
            
            # Update overall progress
            self._overall_label.text = f"Overall Progress: {overall['overall_percent']:.1f}%"
            self._overall_progress_label.text = self._make_progress_bar(overall['overall_percent'])
            
            # Update individual data types
            for data_type, widgets in self._data_type_widgets.items():
                if data_type in self.progress.data_types:
                    stats = self.progress.data_types[data_type]
                    speed = self.progress.get_speed(data_type)
                    eta = self.progress.get_eta(data_type)
                    
                    if stats['status'] == 'completed':
                        widgets['label'].text = f"{data_type.title()}: ✅ Complete - {stats['imported']:,} records"
                        widgets['progress_label'].text = self._make_progress_bar(100)
                    elif stats['estimated_total']:
                        percent = (stats['processed'] / stats['estimated_total'] * 100)
                        widgets['label'].text = (f"{data_type.title()}: {stats['processed']:,}/{stats['estimated_total']:,} "
                                               f"({percent:.1f}%) @ {speed:.0f}/s")
                        widgets['progress_label'].text = self._make_progress_bar(percent)
                    else:
                        widgets['label'].text = f"{data_type.title()}: {stats['processed']:,} processed @ {speed:.0f}/s"
                        widgets['progress_label'].text = self._make_progress_bar(0)
                else:
                    widgets['label'].text = f"{data_type.title()}: Waiting..."
                    widgets['progress_label'].text = self._make_progress_bar(0)
            
            # Update stats
            memory = overall['memory']
            self._speed_label.text = f"Speed: {overall['overall_speed']:.0f} records/sec | Memory: {memory['rss_mb']:.1f}MB ({memory['percent']:.1f}%)"
            self._eta_label.text = f"ETA: {self.progress.format_eta(overall['overall_eta'])} | Elapsed: {overall['elapsed_time']}"
            
            # Update error log
            if self.error_log:
                error_text = "\n".join(self.error_log[-5:])  # Last 5 errors
                self._error_box.value = error_text
            
            # Schedule next update
            if hasattr(self, '_screen'):
                self._screen.force_update()
                self._start_refresh()
                
        except Exception as e:
            # Silently handle errors to avoid crashing the UI
            pass
    
    def add_error(self, error_msg: str):
        """Add an error to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.error_log.append(f"[{timestamp}] {error_msg}")
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
    
    def process_event(self, event):
        """Handle keyboard events"""
        if isinstance(event, KeyboardEvent):
            if event.key_code == ord('q'):
                raise StopApplication("User quit")
            elif event.key_code == ord('p'):
                # TODO: Implement pause/resume
                pass
        return super(ImportProgressFrame, self).process_event(event)
    
    def stop(self):
        """Stop the refresh timer"""
        if self._update_timer:
            self._update_timer.cancel()


class ImportUI:
    """Main UI controller"""
    
    def __init__(self, progress_tracker: ImportProgress):
        self.progress = progress_tracker
        self.frame = None
        self.screen = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the UI in a separate thread"""
        ui_thread = threading.Thread(target=self._run_ui)
        ui_thread.daemon = True
        ui_thread.start()
    
    def _run_ui(self):
        """Run the UI"""
        def ui_main(screen):
            self.screen = screen
            self.frame = ImportProgressFrame(screen, self.progress)
            scenes = [Scene([self.frame], -1)]
            screen.play(scenes, stop_on_resize=True)
        
        while not self._stop_event.is_set():
            try:
                Screen.wrapper(ui_main)
                break
            except ResizeScreenError:
                pass
            except StopApplication:
                break
    
    def stop(self):
        """Stop the UI"""
        self._stop_event.set()
        if self.frame:
            self.frame.stop()
    
    def add_error(self, error_msg: str):
        """Add an error to the display"""
        if self.frame:
            self.frame.add_error(error_msg)


def demo():
    """Demo the UI"""
    import random
    
    # Create progress tracker
    progress = ImportProgress()
    
    # Create and start UI
    ui = ImportUI(progress)
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
            for i in range(0, total + 1, 1000):
                progress.update_progress(data_type, i, int(i * 0.95), int(i * 0.05))
                
                # Simulate some errors
                if random.random() < 0.01:
                    ui.add_error(f"Error processing {data_type} row {i}: Invalid data")
                
                time.sleep(0.01)  # Simulate processing time
                
                if i > 10000:  # Speed up demo
                    break
                    
            progress.finish_data_type(data_type)
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        pass
    finally:
        ui.stop()
        print("\nDemo completed!")


if __name__ == "__main__":
    demo()