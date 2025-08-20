# ClipmonWSL 📋

**A powerful clipboard monitoring system for WSL with automatic screenshot capture, GIF support, and smart path management**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/buildappolis/clipmon-wsl)
[![WSL](https://img.shields.io/badge/WSL-Ubuntu-orange.svg)](https://docs.microsoft.com/en-us/windows/wsl/)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Built with ❤️ by [BuildAppolis](https://www.buildappolis.com)

## 🎯 Overview

ClipmonWSL is a sophisticated clipboard monitoring tool designed specifically for WSL (Windows Subsystem for Linux) environments. It automatically captures screenshots and images from your clipboard, organizes them by project, and provides both GUI and terminal interfaces for management.

### ✨ Key Features

- 🖼️ **Automatic Screenshot Capture** - Captures screenshots from clipboard instantly
- 🎬 **GIF Support** - Handles animated GIFs and other image formats
- 📁 **Project-Based Organization** - Keeps captures organized by project
- 🎨 **Dark Themed GUI** - Beautiful 8-bit themed control panel
- 🔄 **Smart Duplicate Detection** - Prevents capture loops with intelligent blacklisting
- 📋 **Auto Path Copying** - Copies file paths back to clipboard in clean format
- 🗑️ **Capture Management** - Clean captures with confirmation and auto-cleanup
- 🔍 **Universal Viewer** - Browse captures from all projects in one place
- 💾 **Reference Tracking** - JSON-based capture metadata and organization
- 🚫 **Blacklist System** - Prevents re-capture of intentionally deleted content

## 📦 Installation

### Prerequisites

```bash
# Update package list
sudo apt update

# Required system packages
sudo apt install -y \
    python3 python3-pip \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 \
    xclip imagemagick

# Python packages
pip3 install Pillow
```

### Quick Install

1. **Clone the repository:**
```bash
git clone https://github.com/buildappolis/clipmon-wsl.git ~/clipmon-wsl
cd ~/clipmon-wsl
```

2. **Make scripts executable:**
```bash
chmod +x src/*
```

3. **Copy to global tools directory (recommended):**
```bash
# Create tools directory if it doesn't exist
mkdir -p ~/.claude/tools

# Copy all ClipmonWSL components
cp src/* ~/.claude/tools/
chmod +x ~/.claude/tools/clipmon*

# Add to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.claude/tools:$PATH"
```

## 🚀 Quick Start

### Basic Commands

```bash
# Start monitor in background (most common)
clipmon bg

# Open GUI control panel
clipmon gui

# View all captures
clipmon viewer

# Check status
clipmon status

# Stop monitor
clipmon stop
```

## 📸 How It Works

### Capture Flow Diagram

```
┌─────────────────┐
│ Take Screenshot │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Clipboard Event │
└────────┬────────┘
         ↓
┌─────────────────┐     ┌──────────────┐
│ Monitor Detects │ --> │ Check Blacklist │
└────────┬────────┘     └──────┬───────┘
         ↓                     ↓
┌─────────────────┐     ┌──────────────┐
│ Calculate Hash  │ --> │ Skip if Duplicate │
└────────┬────────┘     └──────────────┘
         ↓
┌─────────────────┐
│   Save Image    │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Update References│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Copy Path to    │
│ Windows Clipboard│
└─────────────────┘
```

### File Organization

```
your-project/
└── .claude/
    └── captures/
        ├── img_20250820_143022.png    # Screenshot
        ├── img_20250820_143156.gif    # Animated GIF
        ├── references.json             # Capture metadata
        └── .blacklist.json            # Ignored hashes
```

### References Format

```json
{
  "latest": "img_20250820_143156.gif",
  "numbered": {
    "1": {
      "path": "/home/user/coding/project/.claude/captures/img_20250820_143022.png",
      "name": "img_20250820_143022.png",
      "size": 45632,
      "time": "2025-08-20T14:30:22.123456"
    }
  },
  "updated": "2025-08-20T14:31:56.789012"
}
```

## 🎨 GUI Control Panel

The control panel provides an intuitive interface for managing captures:

### Features
- **Monitor Control** - Start/stop with visual status
- **Project Switching** - Dropdown for active projects
- **Recent Captures** - Live-updating list
- **Quick Actions**:
  - 📁 View All Captures - Opens the viewer
  - 📂 Open Captures Folder - Windows Explorer integration
  - 🗑️ Clean Old Captures - With confirmation dialog

### Dark Theme
The GUI features a custom 8-bit dark theme with:
- Retro pixel-art aesthetic
- High contrast colors
- Consistent styling across all dialogs
- Animated status indicators

## 🔍 Universal Viewer

Browse and manage captures from all projects:

### Features
- **Multi-Project View** - See captures from all projects
- **Filtering** - By project, type, or search term
- **Preview** - Live preview with GIF animation
- **Actions**:
  - View in default application
  - Copy path to clipboard
  - Open containing folder
  - Delete with confirmation
- **GIF Support** - Play animations in browser

## 🛠️ Advanced Features

### Smart Duplicate Detection

The system uses multiple layers to prevent duplicates:

1. **SHA256 Hashing** - Each image gets a unique hash
2. **Blacklist System** - Deleted images are blacklisted
3. **Last Image Tracking** - Remembers the last captured image
4. **File Path Tracking** - Monitors already processed files

### Auto Path Management

When an image is captured:
1. Image saved to: `/home/user/coding/project/.claude/captures/img_TIMESTAMP.ext`
2. Path converted to: `"~/coding/project/.claude/captures/img_TIMESTAMP.ext"`
3. Automatically copied to Windows clipboard
4. Ready to paste in any application

### Blacklist System

Prevents re-capture of deleted content:
- Stored in `.blacklist.json`
- Contains SHA256 hashes of deleted images
- Automatically managed (keeps last 100 entries)
- Updated when using "Clean Captures"

### Auto-Cleanup

The system automatically:
- Detects when files are deleted externally
- Updates `references.json` accordingly
- Renumbers entries to maintain sequence
- Removes orphaned references

## ⚙️ Configuration

### Config File Location
`~/.clipmon/config.json`

### Available Settings

```json
{
  "default_mode": "tray",        // tray, gui, or terminal
  "auto_start_monitor": true,    // Start monitor on launch
  "minimize_to_tray": true,       // Minimize GUI to tray
  "show_notifications": false,    // Desktop notifications (WSL limited)
  "capture_location": "project",  // project or global
  "theme": "8bit-dark"           // UI theme
}
```

### Configure Interactively

```bash
clipmon config
```

## 🔧 Troubleshooting

### Monitor Not Capturing

```bash
# Check if running
clipmon status

# Verify xclip installation
which xclip
xclip -selection clipboard -o

# Check for errors
clipmon stop
clipmon --terminal  # Run in foreground to see output
```

### GUI Not Opening

```bash
# Install required packages
sudo apt install python3-gi gir1.2-gtk-3.0

# Check DISPLAY variable
echo $DISPLAY

# For WSL2 on Windows 10 (need X server)
export DISPLAY=:0

# For WSL2 on Windows 11 (WSLg should work)
# No additional config needed
```

### Path Not Copying to Windows

```bash
# Test PowerShell access
powershell.exe -Command "Get-Clipboard"

# Test WSL path conversion
wslpath -w /home/$USER

# Verify clipboard integration
echo "test" | powershell.exe -Command "Set-Clipboard"
```

### Cleanup Not Working

```bash
# Check blacklist file
cat .claude/captures/.blacklist.json

# Manually clear captures
rm .claude/captures/img_*
echo '{"latest": "", "numbered": {}, "updated": "'$(date -Iseconds)'"}' > .claude/captures/references.json
```

## 📚 API Usage

### Python Integration

```python
import subprocess
import json
from pathlib import Path

class ClipmonAPI:
    def __init__(self):
        self.captures_dir = Path.cwd() / ".claude" / "captures"
    
    def start_monitor(self):
        """Start the clipboard monitor"""
        subprocess.run(["clipmon", "bg"])
    
    def stop_monitor(self):
        """Stop the clipboard monitor"""
        subprocess.run(["clipmon", "stop"])
    
    def get_latest_capture(self):
        """Get the most recent capture"""
        refs_file = self.captures_dir / "references.json"
        if refs_file.exists():
            with open(refs_file) as f:
                data = json.load(f)
                return data.get("latest")
        return None
    
    def get_all_captures(self):
        """Get all captures"""
        refs_file = self.captures_dir / "references.json"
        if refs_file.exists():
            with open(refs_file) as f:
                data = json.load(f)
                return data.get("numbered", {})
        return {}
```

### Shell Script Integration

```bash
#!/bin/bash

# Start monitor for current session
clipmon bg

# Wait for user to take screenshots
echo "Take your screenshots. Press Enter when done..."
read

# Get latest capture
LATEST=$(jq -r '.latest' .claude/captures/references.json)
echo "Latest capture: $LATEST"

# Process all captures
for img in .claude/captures/img_*.png; do
    echo "Processing: $img"
    # Your processing here
done

# Clean up
clipmon stop
```

## 🏗️ Project Structure

```
clipmon-wsl/
├── README.md                   # This file
├── LICENSE                     # MIT License
├── src/
│   ├── clipmon                # Main entry point
│   ├── clipmon-bg             # Background daemon manager
│   ├── clipmon-monitor.py    # Core monitoring engine
│   ├── clipmon-gui            # GTK control panel
│   ├── clipmon-viewer         # Universal viewer
│   ├── clipmon-tray           # Linux system tray
│   ├── clipmon-systray.py    # Windows system tray
│   ├── clipmon-wintray        # Windows tray launcher
│   └── theme.css              # 8-bit dark theme
├── docs/
│   ├── API.md                 # API documentation
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   └── screenshots/           # Screenshots for docs
└── examples/
    ├── integration/           # Integration examples
    └── scripts/               # Utility scripts
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/clipmon-wsl.git
cd clipmon-wsl

# Create branch
git checkout -b feature/your-feature

# Make changes and test
./src/clipmon --terminal

# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by [BuildAppolis](https://www.buildappolis.com)
- GTK and Python communities for excellent documentation
- WSL team at Microsoft for making this possible
- All contributors and users

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/buildappolis/clipmon-wsl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/buildappolis/clipmon-wsl/discussions)
- **Website**: [www.buildappolis.com](https://www.buildappolis.com)
- **Email**: support@buildappolis.com

## 💡 Why I Built This

As a Windows user who loves developing on WSL because things are just easier, I faced a constant frustration with screenshot management. When Claude Code came along, I fell in love with the terminal experience it provided, but I needed to extend its functionality to improve my workflow.

### The Problem

Before ClipmonWSL, sharing screenshots with Claude Code was painful:
- Save screenshot to Windows
- Copy file to Linux filesystem
- Drag into chat or reference the path
- Use special commands to get the image
- Repeat for every single screenshot...

I searched extensively for practical solutions that worked well with Claude Code itself, but couldn't find anything that met my needs. So I decided to build it myself.

### The Solution

With ClipmonWSL, I can now:
- Take a Windows screenshot
- Have it automatically appear in my WSL project within seconds
- Get the path instantly copied to clipboard in the right format
- Reference it directly in Claude Code conversations
- Manage captures across multiple projects with a built-in GUI

This tool transforms what used to be a multi-step interruption into a seamless part of the development workflow. No more context switching, no more manual file management - just capture and continue coding.

## 📊 Performance

- **Capture Speed**: < 0.5 seconds
- **Memory Usage**: ~30MB idle, ~50MB active
- **CPU Usage**: < 1% idle, < 5% during capture
- **Supported Formats**: PNG, JPG, GIF, BMP, WebP
- **Max Image Size**: No limit (tested up to 100MB)
- **Concurrent Projects**: Unlimited

---

<p align="center">
  <strong>ClipmonWSL</strong><br>
  Your clipboard, captured and organized<br>
  Made with 🎮 8-bit style and modern functionality<br>
  <br>
  <a href="https://www.buildappolis.com">BuildAppolis</a> - Modernizing your web
</p>