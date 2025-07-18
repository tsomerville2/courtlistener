#!/usr/bin/env python3
"""
Download CourtListener bulk data with asciimatics progress bars
Shows real-time download progress with file sizes and percentages
"""

import subprocess
import os
import sys
import argparse
import time
import requests
from pathlib import Path
from asciimatics.widgets import Frame, MultiColumnListBox, Layout, Divider, Text, Button, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import KeyboardEvent
import threading
import queue

class DownloadProgressFrame(Frame):
    def __init__(self, screen, files_to_download):
        super(DownloadProgressFrame, self).__init__(screen,
                                                   screen.height * 2 // 3,
                                                   screen.width * 2 // 3,
                                                   hover_focus=True,
                                                   title="FreeLaw Data Download Progress",
                                                   reduce_cpu=True)
        
        self.files_to_download = files_to_download
        self.current_file_index = 0
        self.download_queue = queue.Queue()
        self.download_thread = None
        self.is_downloading = False
        
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        
        # Current file info
        self.current_file_label = Label("Current File: None")
        layout.add_widget(self.current_file_label)
        
        # File progress bar (manual text representation)
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
        
        # File list
        self.file_list = MultiColumnListBox(
            Widget.FILL_FRAME,
            ["<30", "<15", "<10"],
            [("File", "Size", "Status")],
            titles=["File", "Size", "Status"],
            name="file_list"
        )
        layout.add_widget(self.file_list)
        
        # Populate initial file list
        self.update_file_list()
        
        layout.add_widget(Divider())
        
        # Control buttons
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        
        self.start_button = Button("Start Download", self.start_download)
        layout2.add_widget(self.start_button, 0)
        
        self.pause_button = Button("Pause", self.pause_download)
        layout2.add_widget(self.pause_button, 1)
        
        self.cancel_button = Button("Cancel", self.cancel_download)
        layout2.add_widget(self.cancel_button, 2)
        
        self.quit_button = Button("Quit", self.quit_app)
        layout2.add_widget(self.quit_button, 3)
        
        self.fix()
    
    def update_file_list(self):
        """Update the file list display"""
        options = []
        for i, (filename, description, size_estimate) in enumerate(self.files_to_download):
            if i < self.current_file_index:
                status = "✅ Done"
            elif i == self.current_file_index and self.is_downloading:
                status = "🔄 Downloading"
            else:
                status = "⏳ Pending"
            
            options.append(([filename, size_estimate, status], i))
        
        self.file_list.options = options
        self.file_list.value = self.current_file_index
    
    def start_download(self):
        """Start the download process"""
        if not self.is_downloading:
            self.is_downloading = True
            self.start_button.disabled = True
            self.pause_button.disabled = False
            
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
        self.current_file_index = 0
        self.update_file_list()
    
    def quit_app(self):
        """Quit the application"""
        self.is_downloading = False
        raise StopApplication("User quit")
    
    def download_files(self):
        """Download files with progress tracking"""
        base_url = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data"
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        for i, (filename, description, size_estimate) in enumerate(self.files_to_download):
            if not self.is_downloading:
                break
                
            self.current_file_index = i
            self.current_file_label.text = f"Current File: {filename}"
            self.overall_progress_label.text = f"Overall Progress: {i+1}/{len(self.files_to_download)} files"
            
            file_path = downloads_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                continue
                
            url = f"{base_url}/{filename}"
            
            try:
                # Download with progress tracking
                self.download_file_with_progress(url, file_path, filename)
            except Exception as e:
                # Handle download errors
                pass
            
            self.update_file_list()
        
        # Download complete
        self.is_downloading = False
        self.start_button.disabled = False
        self.pause_button.disabled = True
        self.current_file_label.text = "Download Complete!"
    
    def download_file_with_progress(self, url, file_path, filename):
        """Download a single file with progress tracking"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.is_downloading:
                        break
                        
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.file_progress_label.text = f"File Progress: {percent:.1f}%"
                            
                            # Calculate speed (simplified)
                            speed_mb = (downloaded / 1024 / 1024) / max(1, time.time() - getattr(self, 'start_time', time.time()))
                            self.speed_label.text = f"Speed: {speed_mb:.1f} MB/s"
                            
                            # Calculate ETA
                            if speed_mb > 0:
                                remaining_mb = (total_size - downloaded) / 1024 / 1024
                                eta_seconds = remaining_mb / speed_mb
                                eta_minutes = int(eta_seconds // 60)
                                eta_seconds = int(eta_seconds % 60)
                                self.eta_label.text = f"ETA: {eta_minutes:02d}:{eta_seconds:02d}"
            
            if not hasattr(self, 'start_time'):
                self.start_time = time.time()
                
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

def get_file_list(complete_dataset=False):
    """Get the list of files to download"""
    date = "2024-12-31"
    
    if complete_dataset:
        # Complete dataset (~300GB)
        files = [
            (f"courts-{date}.csv.bz2", "Court metadata", "~80KB"),
            (f"people-{date}.csv.bz2", "Judge information", "~5MB"),
            (f"opinion-clusters-{date}.csv.bz2", "Opinion metadata", "~2GB"),
            (f"opinions-{date}.csv.bz2", "Full opinion text", "~25GB"),
            (f"citations-{date}.csv.bz2", "Citation data", "~5GB"),
            (f"dockets-{date}.csv.bz2", "Case dockets", "~50GB"),
            (f"recap-documents-{date}.csv.bz2", "RECAP documents", "~200GB"),
            (f"docket-entries-{date}.csv.bz2", "Docket entries", "~20GB"),
            # Add more files for complete dataset
        ]
    else:
        # Essential files (~30GB total - corrected estimate)
        files = [
            (f"courts-{date}.csv.bz2", "Court metadata", "~80KB"),
            (f"people-{date}.csv.bz2", "Judge information", "~5MB"),
            (f"opinion-clusters-{date}.csv.bz2", "Opinion metadata", "~2GB"),
            (f"opinions-{date}.csv.bz2", "Full opinion text", "~25GB"),
            (f"citations-{date}.csv.bz2", "Citation data", "~5GB"),
            (f"dockets-{date}.csv.bz2", "Case dockets", "~50GB"),
        ]
    
    return files

def main():
    parser = argparse.ArgumentParser(description='Download CourtListener bulk data with progress bars')
    parser.add_argument('--complete', action='store_true', 
                       help='Download complete dataset (~300GB) instead of essential files (~30GB)')
    args = parser.parse_args()
    
    files = get_file_list(args.complete)
    
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