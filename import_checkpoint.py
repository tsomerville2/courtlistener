#!/usr/bin/env python3
"""
Checkpoint system for resumable imports
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class ImportCheckpoint:
    """Manages checkpoints for resumable imports"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
    def _get_checkpoint_path(self, data_type: str) -> Path:
        """Get checkpoint file path for a data type"""
        return self.checkpoint_dir / f"{data_type}_checkpoint.json"
    
    def save_checkpoint(self, data_type: str, file_path: str, 
                       last_processed_id: str, row_number: int,
                       imported_count: int, error_count: int) -> None:
        """Save checkpoint for a data type"""
        checkpoint = {
            'data_type': data_type,
            'file_path': file_path,
            'last_processed_id': last_processed_id,
            'row_number': row_number,
            'imported_count': imported_count,
            'error_count': error_count,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        checkpoint_path = self._get_checkpoint_path(data_type)
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def load_checkpoint(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint for a data type"""
        checkpoint_path = self._get_checkpoint_path(data_type)
        
        if not checkpoint_path.exists():
            return None
            
        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)
            
            # Validate checkpoint
            required_fields = ['data_type', 'file_path', 'last_processed_id', 
                             'row_number', 'imported_count', 'error_count']
            for field in required_fields:
                if field not in checkpoint:
                    print(f"⚠️  Invalid checkpoint: missing {field}")
                    return None
                    
            return checkpoint
            
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            return None
    
    def clear_checkpoint(self, data_type: str) -> None:
        """Clear checkpoint for a data type"""
        checkpoint_path = self._get_checkpoint_path(data_type)
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            print(f"🗑️  Cleared checkpoint for {data_type}")
    
    def clear_all_checkpoints(self) -> None:
        """Clear all checkpoints"""
        for checkpoint_file in self.checkpoint_dir.glob("*_checkpoint.json"):
            checkpoint_file.unlink()
        print("🗑️  Cleared all checkpoints")
    
    def list_checkpoints(self) -> Dict[str, Dict[str, Any]]:
        """List all available checkpoints"""
        checkpoints = {}
        
        for checkpoint_file in self.checkpoint_dir.glob("*_checkpoint.json"):
            data_type = checkpoint_file.stem.replace("_checkpoint", "")
            checkpoint = self.load_checkpoint(data_type)
            if checkpoint:
                checkpoints[data_type] = checkpoint
                
        return checkpoints
    
    def get_resume_info(self, data_type: str) -> Optional[str]:
        """Get human-readable resume information"""
        checkpoint = self.load_checkpoint(data_type)
        if not checkpoint:
            return None
            
        timestamp = datetime.fromisoformat(checkpoint['timestamp'])
        age = datetime.now() - timestamp
        
        # Format age
        if age.days > 0:
            age_str = f"{age.days} day{'s' if age.days > 1 else ''} ago"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            age_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = age.seconds // 60
            age_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
        return (f"Resume from row {checkpoint['row_number']:,} "
                f"(ID: {checkpoint['last_processed_id']}) "
                f"- {checkpoint['imported_count']:,} imported, "
                f"{checkpoint['error_count']:,} errors - "
                f"saved {age_str}")


if __name__ == "__main__":
    # Test checkpoint system
    cp = ImportCheckpoint()
    
    # Test save
    cp.save_checkpoint(
        data_type="dockets",
        file_path="downloads/dockets-2024-12-31.csv.bz2",
        last_processed_id="12345",
        row_number=5000,
        imported_count=4950,
        error_count=50
    )
    
    # Test load
    checkpoint = cp.load_checkpoint("dockets")
    if checkpoint:
        print("✅ Checkpoint saved and loaded successfully:")
        print(json.dumps(checkpoint, indent=2))
        
    # Test resume info
    info = cp.get_resume_info("dockets")
    if info:
        print(f"\n📍 {info}")
        
    # List all
    print("\n📋 All checkpoints:")
    for data_type, checkpoint in cp.list_checkpoints().items():
        print(f"  - {data_type}: {cp.get_resume_info(data_type)}")