#!/bin/bash

# ClipmonWSL Installation Script
# by BuildAppolis

set -e

# Colors for output
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ASCII Art Logo (8-bit style)
echo -e "${PURPLE}"
cat << "EOF"
 ██████╗██╗     ██╗██████╗ ███╗   ███╗ ██████╗ ███╗   ██╗
██╔════╝██║     ██║██╔══██╗████╗ ████║██╔═══██╗████╗  ██║
██║     ██║     ██║██████╔╝██╔████╔██║██║   ██║██╔██╗ ██║
██║     ██║     ██║██╔═══╝ ██║╚██╔╝██║██║   ██║██║╚██╗██║
╚██████╗███████╗██║██║     ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
 ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                WSL Edition
EOF
echo -e "${CYAN}                by BuildAppolis${NC}"
echo -e "${CYAN}           www.buildappolis.com${NC}"
echo ""

echo -e "${YELLOW}Installing ClipmonWSL...${NC}"
echo ""

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    echo -e "${YELLOW}Warning: This doesn't appear to be WSL${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo -e "${CYAN}Creating directories...${NC}"
mkdir -p ~/.claude/clipboard
mkdir -p ~/.claude/tools
mkdir -p ~/.claude/temp

# Copy files
echo -e "${CYAN}Installing ClipmonWSL files...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy main tools
cp "$SCRIPT_DIR/src/clipmon" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-bg" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-gui" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-viewer" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-tray" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-wintray" ~/.claude/tools/
cp "$SCRIPT_DIR/src/clipmon-systray.py" ~/.claude/tools/

# Make executable
chmod +x ~/.claude/tools/clipmon*

# Copy PowerShell scripts
echo -e "${CYAN}Installing PowerShell components...${NC}"
cp "$SCRIPT_DIR/src/"*.ps1 ~/.claude/tools/ 2>/dev/null || true

# Copy assets
echo -e "${CYAN}Installing assets...${NC}"
cp -r "$SCRIPT_DIR/assets" ~/.claude/tools/

# Create symlink for easy access
echo -e "${CYAN}Creating global command...${NC}"
sudo ln -sf ~/.claude/tools/clipmon /usr/local/bin/clipmon 2>/dev/null || \
    echo -e "${YELLOW}Could not create global symlink. Add ~/.claude/tools to your PATH${NC}"

# Check Python dependencies
echo -e "${CYAN}Checking Python dependencies...${NC}"
if ! python3 -c "import gi" 2>/dev/null; then
    echo -e "${YELLOW}GTK Python bindings not found.${NC}"
    echo "Install with: sudo apt-get install python3-gi gir1.2-gtk-3.0"
fi

# Windows Python check
echo -e "${CYAN}Checking Windows Python...${NC}"
if command -v python3.exe &> /dev/null; then
    echo -e "${GREEN}✓ Windows Python found${NC}"
    
    # Try to install pystray
    echo -e "${CYAN}Installing Windows dependencies...${NC}"
    python3.exe -m pip install pystray pillow --quiet 2>/dev/null || \
        echo -e "${YELLOW}Could not install Windows Python packages. Install manually with:${NC}"
        echo "  python -m pip install pystray pillow"
else
    echo -e "${YELLOW}Windows Python not found. System tray won't work.${NC}"
    echo "Install Python from Microsoft Store for system tray support."
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ClipmonWSL Installation Complete!    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Quick Start:${NC}"
echo -e "  ${PURPLE}clipmon tray${NC}    - Start with system tray"
echo -e "  ${PURPLE}clipmon viewer${NC}  - Open captures viewer"
echo -e "  ${PURPLE}clipmon help${NC}    - Show all commands"
echo ""
echo -e "${CYAN}Thank you for using ClipmonWSL!${NC}"
echo -e "${CYAN}Visit ${PURPLE}www.buildappolis.com${CYAN} for more tools${NC}"
echo ""