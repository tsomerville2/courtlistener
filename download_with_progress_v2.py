#!/usr/bin/env python3
"""
Download CourtListener bulk data with beautiful asciimatics progress bars
Smart file detection to avoid re-downloading existing files
"""

import subprocess
import os
import sys
import argparse
import time
import requests
from pathlib import Path
from asciimatics.widgets import Frame, MultiColumnListBox, Layout, Divider, Text, Button, Label, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent
import threading
import queue

class DownloadProgressFrame(Frame):
    def __init__(self, screen, files_to_download):
        super(DownloadProgressFrame, self).__init__(screen,
                                                   screen.height * 4 // 5,
                                                   screen.width * 4 // 5,
                                                   hover_focus=True,
                                                   title="🏛️ FreeLaw Data Download Progress",
                                                   reduce_cpu=True)
        
        self.files_to_download = files_to_download
        self.current_file_index = -1
        self.download_thread = None
        self.is_downloading = False
        self.start_time = None
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Check existing files and update status
        self._check_existing_files()
        
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        
        # Title and summary
        self.summary_label = Label("📊 Download Summary")
        layout.add_widget(self.summary_label)
        
        # Current file info
        self.current_file_label = Label("Current File: Ready to start")
        layout.add_widget(self.current_file_label)
        
        # File progress bar
        self.file_progress_label = Label("File Progress: 0%")
        layout.add_widget(self.file_progress_label)
        
        # Overall progress
        self.overall_progress_label = Label("Overall Progress: 0/0 files")
        layout.add_widget(self.overall_progress_label)
        
        # Speed and ETA
        self.speed_label = Label("Speed: 0 MB/s")
        layout.add_widget(self.speed_label)
        
        self.eta_label = Label("ETA: --:--")
        layout.add_widget(self.eta_label)
        
        layout.add_widget(Divider())
        
        # File list with better formatting
        self.file_list = MultiColumnListBox(
            Widget.FILL_FRAME,
            ["<35", "<15", "<15", "<15"],
            [],
            titles=["File", "Size", "Status", "Progress"],
            name="file_list"
        )
        layout.add_widget(self.file_list)
        
        # Update file list display
        self.update_file_list()
        
        layout.add_widget(Divider())
        
        # Control buttons with keyboard shortcuts
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        
        self.start_button = Button("<(S)tart Download>", self.start_download)
        layout2.add_widget(self.start_button, 0)
        
        self.pause_button = Button("<(P)ause>", self.pause_download)
        layout2.add_widget(self.pause_button, 1)
        
        self.cancel_button = Button("<(C)ancel>", self.cancel_download)
        layout2.add_widget(self.cancel_button, 2)
        
        self.quit_button = Button("<(Q)uit>", self.quit_app)
        layout2.add_widget(self.quit_button, 3)
        
        self.pause_button.disabled = True
        self.skip_existing = True  # Always skip existing files
        
        self.fix()
        
        # Add keyboard help
        layout.add_widget(Divider())
        help_text = Label("🔥 Keyboard Shortcuts: (S)tart, (P)ause, (C)ancel, (Q)uit | Always skips existing files")
        layout.add_widget(help_text)
    
    def process_event(self, event):
        """Handle keyboard events for shortcuts"""
        if isinstance(event, KeyboardEvent):
            key = event.key_code
            if key == ord('s') or key == ord('S'):
                if not self.start_button.disabled:
                    self.start_download()
                return None  # Consume the event
            elif key == ord('p') or key == ord('P'):
                if not self.pause_button.disabled:
                    self.pause_download()
                return None  # Consume the event
            elif key == ord('c') or key == ord('C'):
                self.cancel_download()
                return None  # Consume the event
            elif key == ord('q') or key == ord('Q'):
                self.quit_app()
                return None  # Consume the event
        
        # Call parent process_event for other keys
        return super(DownloadProgressFrame, self).process_event(event)
    
    def _check_existing_files(self):
        """Check which files already exist and update their status"""
        for i, (filename, description, size_estimate) in enumerate(self.files_to_download):
            file_path = self.downloads_dir / filename
            if file_path.exists():
                actual_size = file_path.stat().st_size
                size_mb = actual_size / (1024 * 1024)
                # Update the file info with actual size and existing status
                self.files_to_download[i] = (filename, description, f"{size_mb:.1f}MB", "✅ Downloaded")
            else:
                # Add status to tuple
                self.files_to_download[i] = (filename, description, size_estimate, "⏳ Pending")
    
    def update_file_list(self):
        """Update the file list display"""
        options = []
        total_files = len(self.files_to_download)
        existing_files = 0
        
        for i, file_info in enumerate(self.files_to_download):
            filename, description, size_estimate, status = file_info
            
            if status == "✅ Downloaded":
                existing_files += 1
                progress = "100%"
            elif i == self.current_file_index and self.is_downloading:
                status = "🔄 Downloading"
                progress = "..."
            elif i < self.current_file_index:
                status = "✅ Done"
                progress = "100%"
            else:
                progress = "0%"
            
            options.append(([filename[:30], size_estimate, status, progress], i))
        
        self.file_list.options = options
        
        # Update summary
        if existing_files > 0:
            self.summary_label.text = f"📊 {existing_files}/{total_files} files already downloaded"
        else:
            self.summary_label.text = f"📊 {total_files} files to download"
    
    
    def start_download(self):
        """Start the download process"""
        if not self.is_downloading:
            self.is_downloading = True
            self.start_button.disabled = True
            self.pause_button.disabled = False
            self.start_time = time.time()
            
            # Start download in separate thread
            self.download_thread = threading.Thread(target=self.download_files)
            self.download_thread.daemon = True
            self.download_thread.start()
    
    def pause_download(self):
        """Pause the download"""
        self.is_downloading = False
        self.start_button.disabled = False
        self.pause_button.disabled = True
    
    def cancel_download(self):
        """Cancel the download"""
        self.is_downloading = False
        self.start_button.disabled = False
        self.pause_button.disabled = True
        self.current_file_index = -1
        self.update_file_list()
    
    def quit_app(self):
        """Quit the application"""
        self.is_downloading = False
        raise StopApplication("User quit")
    
    def download_files(self):
        """Download files with progress tracking"""
        base_url = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data"
        files_to_process = []
        
        # Build list of files to actually download
        for i, file_info in enumerate(self.files_to_download):
            filename, description, size_estimate, status = file_info
            file_path = self.downloads_dir / filename
            
            if self.skip_existing and file_path.exists():
                continue  # Skip existing files
            
            files_to_process.append((i, filename, description, size_estimate))
        
        if not files_to_process:
            self.current_file_label.text = "✅ All files already downloaded!"
            self.is_downloading = False
            self.start_button.disabled = False
            self.pause_button.disabled = True
            return
        
        # Download each file
        for idx, (i, filename, description, size_estimate) in enumerate(files_to_process):
            if not self.is_downloading:
                break
                
            self.current_file_index = i
            self.current_file_label.text = f"📥 Downloading: {filename}"
            self.overall_progress_label.text = f"Overall: {idx+1}/{len(files_to_process)} files"
            
            file_path = self.downloads_dir / filename
            url = f"{base_url}/{filename}"
            
            try:
                # Download with progress tracking
                self.download_file_with_progress(url, file_path, filename)
                
                # Update file info with actual size
                actual_size = file_path.stat().st_size
                size_mb = actual_size / (1024 * 1024)
                self.files_to_download[i] = (filename, description, f"{size_mb:.1f}MB", "✅ Downloaded")
                
            except Exception as e:
                self.current_file_label.text = f"❌ Error downloading {filename}: {str(e)[:50]}..."
                time.sleep(2)  # Show error for 2 seconds
            
            self.update_file_list()
        
        # Download complete
        self.is_downloading = False
        self.start_button.disabled = False
        self.pause_button.disabled = True
        
        if self.current_file_index >= 0:
            self.current_file_label.text = "✅ Download Complete!"
            total_time = time.time() - self.start_time
            self.eta_label.text = f"Total time: {total_time/60:.1f} minutes"
    
    def download_file_with_progress(self, url, file_path, filename):
        """Download a single file with progress tracking"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        start_time = time.time()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not self.is_downloading:
                    break
                    
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Update progress every 100KB
                    if downloaded % (100 * 1024) == 0 or downloaded == total_size:
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.file_progress_label.text = f"File Progress: {percent:.1f}% ({downloaded/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB)"
                            
                            # Calculate speed
                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                speed_mb = (downloaded / 1024 / 1024) / elapsed
                                self.speed_label.text = f"Speed: {speed_mb:.1f} MB/s"
                                
                                # Calculate ETA
                                if speed_mb > 0:
                                    remaining_mb = (total_size - downloaded) / 1024 / 1024
                                    eta_seconds = remaining_mb / speed_mb
                                    eta_minutes = int(eta_seconds // 60)
                                    eta_seconds = int(eta_seconds % 60)
                                    self.eta_label.text = f"ETA: {eta_minutes:02d}:{eta_seconds:02d}"

def get_file_list():
    """Get the list of essential files to download (75GB compressed)"""
    date = "2024-12-31"
    
    # Essential files that expand to ~300GB when processed
    files = [
        ("courts-2024-12-31.csv.bz2", "Court metadata", "~80KB"),
        ("people-2024-12-31.csv.bz2", "Judge information", "~5MB"),
        ("opinion-clusters-2024-12-31.csv.bz2", "Opinion metadata", "~2GB"),
        ("opinions-2024-12-31.csv.bz2", "Full opinion text", "~23GB"),
        ("citations-2024-12-31.csv.bz2", "Citation data", "~5GB"),
        ("dockets-2024-12-31.csv.bz2", "Case dockets", "~5GB"),
    ]
    
    return files

def main():
    parser = argparse.ArgumentParser(description='Download CourtListener bulk data with beautiful progress bars')
    parser.add_argument('--complete', action='store_true', 
                       help='Download complete dataset (same files - use for compatibility)')
    args = parser.parse_args()
    
    files = get_file_list()
    
    def demo(screen):
        screen.play([Scene([DownloadProgressFrame(screen, files)], -1)], stop_on_resize=True)
    
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False)
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene

if __name__ == "__main__":
    main()