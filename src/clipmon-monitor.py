#!/usr/bin/env python3
"""
ClipmonWSL Monitor - Python clipboard monitor with references.json
Monitors clipboard and saves captures with proper references
"""

import os
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
import threading

class ClipboardMonitor:
    def __init__(self, project_dir=None):
        self.project_dir = Path(project_dir or os.getcwd())
        self.captures_dir = self.project_dir / '.claude' / 'captures'
        self.references_file = self.captures_dir / 'references.json'
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize references
        self.load_references()
        
        # Tracking
        self.last_image_hash = None
        self.last_text = None
        self.last_files = set()
        self.running = True
        
        # Blacklist for intentionally deleted content
        self.blacklist_file = self.captures_dir / '.blacklist.json'
        self.load_blacklist()
        
    def load_blacklist(self):
        """Load blacklist of hashes to ignore"""
        self.blacklist = set()
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file, 'r') as f:
                    data = json.load(f)
                    self.blacklist = set(data.get('hashes', []))
            except:
                pass
    
    def save_blacklist(self):
        """Save blacklist to file"""
        try:
            with open(self.blacklist_file, 'w') as f:
                json.dump({'hashes': list(self.blacklist)}, f)
        except:
            pass
    
    def add_to_blacklist(self, content_hash):
        """Add a hash to the blacklist"""
        self.blacklist.add(content_hash)
        # Keep blacklist size reasonable (last 100 items)
        if len(self.blacklist) > 100:
            self.blacklist = set(list(self.blacklist)[-100:])
        self.save_blacklist()
    
    def load_references(self):
        """Load existing references or create new"""
        if self.references_file.exists():
            try:
                with open(self.references_file, 'r') as f:
                    self.references = json.load(f)
                    if 'numbered' not in self.references:
                        self.references['numbered'] = {}
            except:
                self.references = {'latest': '', 'numbered': {}, 'updated': ''}
        else:
            self.references = {'latest': '', 'numbered': {}, 'updated': ''}
        
        # Get next capture number
        if self.references['numbered']:
            max_num = max(int(k) for k in self.references['numbered'].keys())
            self.next_number = max_num + 1
        else:
            self.next_number = 1
    
    def save_references(self):
        """Save references to JSON file"""
        self.references['updated'] = datetime.now().isoformat()
        with open(self.references_file, 'w') as f:
            json.dump(self.references, f, indent=2)
    
    def add_capture(self, filepath, filename, size):
        """Add capture to references"""
        self.references['numbered'][str(self.next_number)] = {
            'path': str(filepath),
            'name': filename,
            'size': size,
            'time': datetime.now().strftime('%H:%M:%S')
        }
        self.references['latest'] = filename
        self.save_references()
        self.next_number += 1
        return self.next_number - 1
    
    def get_clipboard_image(self):
        """Get image from clipboard using PowerShell"""
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        $clipboard = [System.Windows.Forms.Clipboard]::GetImage()
        if ($clipboard) {
            $ms = New-Object System.IO.MemoryStream
            $clipboard.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            [Convert]::ToBase64String($ms.ToArray())
        }
        '''
        
        try:
            result = subprocess.run(
                ['powershell.exe', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.stdout.strip():
                import base64
                return base64.b64decode(result.stdout.strip())
        except:
            pass
        return None
    
    def get_clipboard_text(self):
        """Get text from clipboard"""
        try:
            result = subprocess.run(
                ['powershell.exe', '-Command', 'Get-Clipboard -Format Text'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.stdout else None
        except:
            return None
    
    def process_file(self, file_path_str):
        """Process a file from clipboard"""
        # Check if we've already processed this file
        if file_path_str in self.last_files:
            return
            
        file_path = Path(file_path_str)
        if file_path.suffix.lower() in ['.gif', '.png', '.jpg', '.jpeg', '.bmp', '.webp']:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"img_{timestamp}{file_path.suffix.lower()}"
            filepath = self.captures_dir / filename
            
            # Check if file is already in captures (avoid duplicates)
            if filepath.exists():
                return
            
            # Copy file
            import shutil
            shutil.copy2(file_path_str, filepath)
            
            # Add to references
            size = filepath.stat().st_size
            num = self.add_capture(filepath, filename, size)
            
            # Display info
            size_kb = size / 1024
            file_type = "GIF" if file_path.suffix.lower() == '.gif' else "IMAGE"
            print(f"[\033[0;90m{datetime.now().strftime('%H:%M:%S')}\033[0m] "
                  f"\033[0;35m{file_type}\033[0m "
                  f"\033[0;36m#{num}\033[0m "
                  f"\033[0;90m({size_kb:.1f} KB)\033[0m "
                  f"→ \033[1;33m{filename}\033[0m")
            
            # Copy Windows path to clipboard
            self.copy_windows_path_to_clipboard(filepath)
            
            # Track this file
            self.last_files.add(file_path_str)
            # Keep only last 10 files in memory
            if len(self.last_files) > 10:
                self.last_files = set(list(self.last_files)[-10:])
    
    def copy_windows_path_to_clipboard(self, filepath):
        """Copy the file path to Windows clipboard using tilde notation"""
        try:
            # Convert to string path
            path_str = str(filepath)
            home_dir = str(Path.home())
            
            # Replace home directory with ~
            if path_str.startswith(home_dir):
                # Create tilde path
                relative_path = path_str.replace(home_dir, "~", 1)
                # Add quotes around the path
                clipboard_path = f'"{relative_path}"'
            else:
                # Fallback to full path with quotes
                clipboard_path = f'"{path_str}"'
            
            # Use PowerShell to set Windows clipboard
            ps_command = f"Set-Clipboard -Value '{clipboard_path}'"
            subprocess.run(
                ['powershell.exe', '-Command', ps_command],
                capture_output=True
            )
            
            # Show that path was copied (without the quotes for display)
            display_path = clipboard_path.strip('"')
            print(f"  \033[0;90m↳ Path copied: {display_path}\033[0m")
        except Exception as e:
            # Silently fail if can't copy to clipboard
            pass
    
    def get_clipboard_files(self):
        """Get file list from clipboard"""
        try:
            ps_script = '''
            $files = Get-Clipboard -Format FileDropList -ErrorAction SilentlyContinue
            if ($files) {
                $files | ForEach-Object { $_.FullName }
            }
            '''
            result = subprocess.run(
                ['powershell.exe', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.stdout.strip():
                return result.stdout.strip().split('\n')
        except:
            pass
        return None
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print(f"\033[0;36m{'='*40}\033[0m")
        print(f"\033[1;37m  CLIPMONWSL MONITOR\033[0m")
        print(f"\033[0;36m{'='*40}\033[0m")
        print(f"Project: \033[1;33m{self.project_dir}\033[0m")
        print(f"Saving to: \033[1;33m{self.captures_dir}\033[0m")
        print(f"Next capture: #{self.next_number}")
        print(f"\033[0;36m{'='*40}\033[0m")
        print("Press Ctrl+C to stop monitoring\n")
        
        while self.running:
            try:
                # Check for image in clipboard
                image_data = self.get_clipboard_image()
                if image_data:
                    # Calculate hash
                    image_hash = hashlib.sha256(image_data).hexdigest()
                    
                    # Skip if in blacklist
                    if image_hash in self.blacklist:
                        self.last_image_hash = image_hash
                        continue
                    
                    if image_hash != self.last_image_hash:
                        # New image detected
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"img_{timestamp}.png"
                        filepath = self.captures_dir / filename
                        
                        # Save image
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        
                        # Add to references
                        size = len(image_data)
                        num = self.add_capture(filepath, filename, size)
                        
                        # Display info
                        size_kb = size / 1024
                        print(f"[\033[0;90m{datetime.now().strftime('%H:%M:%S')}\033[0m] "
                              f"\033[0;32mIMAGE\033[0m "
                              f"\033[0;36m#{num}\033[0m "
                              f"\033[0;90m({size_kb:.1f} KB)\033[0m "
                              f"→ \033[1;33m{filename}\033[0m")
                        
                        # Copy Windows path to clipboard
                        self.copy_windows_path_to_clipboard(filepath)
                        
                        self.last_image_hash = image_hash
                
                # Check for file drops (for GIFs and other images)
                files = self.get_clipboard_files()
                if files:
                    for file_path_str in files:
                        # Handle Windows paths
                        if file_path_str and os.path.exists(file_path_str):
                            self.process_file(file_path_str)
                        elif file_path_str:
                            # Try converting Windows path to WSL path
                            try:
                                result = subprocess.run(
                                    ['wslpath', '-u', file_path_str],
                                    capture_output=True,
                                    text=True
                                )
                                if result.returncode == 0:
                                    wsl_path = result.stdout.strip()
                                    if os.path.exists(wsl_path):
                                        self.process_file(wsl_path)
                            except:
                                pass
                
                # Also check text clipboard for file paths (fallback for GIFs)
                text = self.get_clipboard_text()
                if text and text != self.last_text:
                    # Check if it's a file path
                    if os.path.exists(text) and os.path.isfile(text):
                        self.process_file(text)
                        self.last_text = text
                
                # Sleep to prevent high CPU usage
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                # Continue on errors
                time.sleep(1)
    
    def run(self):
        """Start monitoring"""
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            pass
        finally:
            print("\n\033[1;33mStopping monitor...\033[0m")
            print("\033[0;32m✓ Monitor stopped\033[0m")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='ClipmonWSL Monitor')
    parser.add_argument('--project', '-p', default=os.getcwd(),
                       help='Project directory path')
    args = parser.parse_args()
    
    monitor = ClipboardMonitor(args.project)
    monitor.run()

if __name__ == "__main__":
    main()