#!/usr/bin/env python3
"""
Clipboard Monitor System Tray (Windows Native)
Uses pystray to create a Windows system tray icon
"""

import sys
import os
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
import json

# Try to import pystray and PIL
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: pystray and Pillow are required")
    print("Install with: pip install pystray pillow")
    sys.exit(1)

class ClipmonSystemTray:
    def __init__(self):
        # Paths - convert WSL paths to Windows paths as needed
        self.wsl_base = Path.home() / '.claude'
        self.pid_file = self.wsl_base / 'clipmon.pid'
        self.refs_file = self.wsl_base / 'clipboard' / 'references.txt'
        
        # Monitor state
        self.monitor_running = False
        self.last_capture_count = 0
        
        # Create tray icon
        self.icon = None
        self.create_tray_icon()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_status, daemon=True)
        self.monitor_thread.start()
    
    def create_image(self, color='red'):
        """Create a simple colored circle icon"""
        # Create an image
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw circle
        if color == 'green':
            fill_color = (0, 255, 0, 255)
        elif color == 'yellow':
            fill_color = (255, 255, 0, 255)
        else:  # red
            fill_color = (255, 0, 0, 255)
        
        # Draw outer circle (border)
        draw.ellipse([8, 8, 56, 56], fill=(64, 64, 64, 255))
        # Draw inner circle (colored)
        draw.ellipse([12, 12, 52, 52], fill=fill_color)
        
        return image
    
    def is_monitor_running(self):
        """Check if monitor is running via WSL"""
        try:
            # First check if PID file exists
            check_file = subprocess.run(
                'wsl.exe test -f /home/cory-ubuntu/.claude/clipmon.pid && echo exists',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True
            )
            
            if 'exists' not in check_file.stdout:
                return False
            
            # Get the PID
            get_pid = subprocess.run(
                'wsl.exe cat /home/cory-ubuntu/.claude/clipmon.pid',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True
            )
            
            if not get_pid.stdout.strip():
                return False
            
            pid = get_pid.stdout.strip()
            
            # Check if process exists
            check_process = subprocess.run(
                f'wsl.exe ps -p {pid}',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True
            )
            
            # If ps command succeeds and output contains the PID, process is running
            return pid in check_process.stdout
        except Exception as e:
            print(f"Error checking monitor status: {e}")
            return False
    
    def get_capture_count(self):
        """Get number of captures"""
        try:
            result = subprocess.run(
                f'wsl.exe bash -c "if [ -f {self.refs_file} ]; then wc -l < {self.refs_file}; else echo 0; fi"',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True
            )
            return int(result.stdout.strip())
        except:
            return 0
    
    def get_recent_captures(self, limit=5):
        """Get recent captures"""
        try:
            result = subprocess.run(
                f'wsl.exe bash -c "if [ -f {self.refs_file} ]; then tail -n {limit} {self.refs_file}; fi"',
                capture_output=True,
                text=True,
                timeout=2,
                shell=True
            )
            
            captures = []
            for line in reversed(result.stdout.strip().split('\n')):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        timestamp = datetime.fromtimestamp(float(parts[0]))
                        captures.append({
                            'id': parts[2].strip(),
                            'type': 'GIF' if 'gif' in parts[1] else 'Image',
                            'time': timestamp.strftime("%H:%M"),
                            'path': parts[1].strip()
                        })
            return captures
        except:
            return []
    
    def start_monitor(self, icon, item):
        """Start the clipboard monitor"""
        subprocess.run(
            'wsl.exe bash -c "/home/cory-ubuntu/.claude/tools/clipmon bg"',
            capture_output=True,
            shell=True
        )
        time.sleep(2)  # Give it time to start
        self.update_icon()
    
    def stop_monitor(self, icon, item):
        """Stop the clipboard monitor"""
        subprocess.run(
            'wsl.exe bash -c "/home/cory-ubuntu/.claude/tools/clipmon stop"',
            capture_output=True,
            shell=True
        )
        time.sleep(1)  # Give it time to stop
        self.update_icon()
    
    def toggle_monitor(self, icon, item):
        """Toggle monitor on/off"""
        if self.monitor_running:
            self.stop_monitor(icon, item)
        else:
            self.start_monitor(icon, item)
    
    def show_gui(self, icon, item):
        """Show the GTK GUI window"""
        # Use wsl.exe to run the GUI command properly
        # Run Python directly to avoid shell issues
        subprocess.Popen(
            'wsl.exe -e python3 /home/cory-ubuntu/.claude/tools/clipmon-gui',
            shell=True,
            cwd='C:\\'  # Set working directory to avoid UNC path issues
        )
    
    def view_captures(self, icon, item):
        """View captures in comprehensive GUI"""
        # Launch the captures viewer GUI
        subprocess.Popen(
            'wsl.exe -e python3 /home/cory-ubuntu/.claude/tools/clipmon-viewer',
            shell=True,
            cwd='C:\\'  # Set working directory to avoid UNC path issues
        )
    
    def open_folder(self, icon, item):
        """Open captures folder"""
        # Get Windows path and open in Explorer
        result = subprocess.run(
            f'wsl.exe wslpath -w "{self.wsl_base}/clipboard"',
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            win_path = result.stdout.strip()
            subprocess.Popen(f'explorer.exe "{win_path}"', shell=True)
    
    def clean_captures(self, icon, item):
        """Clean old captures"""
        result = subprocess.run(
            ['wsl.exe', '-e', 'bash', '-c', 'cd ~ && clipmon clean'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            self.show_notification("Old captures cleaned")
        else:
            self.show_notification("Failed to clean captures")
    
    def copy_capture_path(self, capture_id):
        """Copy a capture path to clipboard"""
        def handler(icon, item):
            # Get the capture path
            captures = self.get_recent_captures(10)
            for cap in captures:
                if cap['id'] == capture_id:
                    # Copy to Windows clipboard
                    subprocess.run(
                        ['powershell', '-command', f'Set-Clipboard -Value "{cap["path"]}"'],
                        capture_output=True
                    )
                    self.show_notification(f"Copied path for {cap['type']} #{cap['id']}")
                    break
        return handler
    
    def show_notification(self, message):
        """Show Windows notification"""
        if self.icon:
            self.icon.notify(message, "Clipboard Monitor")
    
    def quit_app(self, icon, item):
        """Quit the application"""
        self.monitoring = False
        
        # Ask if should stop monitor
        if self.monitor_running:
            # For simplicity, just stop it
            self.stop_monitor(icon, item)
        
        icon.stop()
    
    def update_icon(self):
        """Update tray icon based on status"""
        is_running = self.is_monitor_running()
        self.monitor_running = is_running
        
        if self.icon:
            # Update icon color
            if is_running:
                self.icon.icon = self.create_image('green')
                self.icon.title = "Clipboard Monitor - Running"
            else:
                self.icon.icon = self.create_image('red')
                self.icon.title = "Clipboard Monitor - Stopped"
    
    def monitor_status(self):
        """Background thread to monitor status"""
        while self.monitoring:
            try:
                # Check monitor status
                old_status = self.monitor_running
                self.update_icon()
                
                # Check for new captures
                current_count = self.get_capture_count()
                if current_count > self.last_capture_count and self.last_capture_count > 0:
                    diff = current_count - self.last_capture_count
                    if diff == 1:
                        self.show_notification(f"New capture #{current_count}")
                    else:
                        self.show_notification(f"{diff} new captures")
                self.last_capture_count = current_count
                
            except Exception as e:
                print(f"Monitor thread error: {e}")
            
            time.sleep(3)  # Check every 3 seconds
    
    def create_menu(self):
        """Create the tray menu"""
        menu_items = []
        
        # Status indicator (changes based on state)
        if self.monitor_running:
            menu_items.append(pystray.MenuItem("● Running", None, enabled=False))
            menu_items.append(pystray.MenuItem("Stop Monitor", self.stop_monitor))
        else:
            menu_items.append(pystray.MenuItem("● Stopped", None, enabled=False))
            menu_items.append(pystray.MenuItem("Start Monitor", self.start_monitor))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Actions
        menu_items.append(pystray.MenuItem("Show Control Panel", self.show_gui))
        menu_items.append(pystray.MenuItem("View All Captures", self.view_captures))
        menu_items.append(pystray.MenuItem("Open Captures Folder", self.open_folder))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Recent captures submenu
        recent_captures = self.get_recent_captures(5)
        if recent_captures:
            capture_items = []
            for cap in recent_captures:
                label = f"#{cap['id']}: {cap['type']} - {cap['time']}"
                capture_items.append(
                    pystray.MenuItem(label, self.copy_capture_path(cap['id']))
                )
            menu_items.append(pystray.MenuItem("Recent Captures", pystray.Menu(*capture_items)))
        else:
            menu_items.append(pystray.MenuItem("Recent Captures", None, enabled=False))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Utilities
        menu_items.append(pystray.MenuItem("Clean Old Captures", self.clean_captures))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Quit
        menu_items.append(pystray.MenuItem("Quit", self.quit_app))
        
        return pystray.Menu(*menu_items)
    
    def create_tray_icon(self):
        """Create and setup the system tray icon"""
        # Create initial icon
        image = self.create_image('red')
        
        # Create the tray icon with dynamic menu
        self.icon = pystray.Icon(
            "clipmon",
            image,
            "Clipboard Monitor",
            menu=self.create_menu()  # Pass the menu directly, not a lambda
        )
    
    def run(self):
        """Run the system tray application"""
        # Initial status check
        self.update_icon()
        
        # Run the icon (this blocks)
        self.icon.run()

def main():
    """Main entry point"""
    try:
        app = ClipmonSystemTray()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()