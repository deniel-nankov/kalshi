#!/bin/bash
# Setup Bronze Automation Service for macOS
# This installs the Bronze data automation as a macOS launchd service

set -e  # Exit on error

echo "=================================================="
echo "Bronze Automation Setup for macOS"
echo "=================================================="
echo ""

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/Gas/scripts/automate_bronze.py"
PLIST_NAME="com.kalshi.bronze-automation"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at: $VENV_PYTHON"
    echo "Please create a virtual environment first:"
    echo "  python -m venv .venv"
    exit 1
fi

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Automation script not found at: $SCRIPT_PATH"
    exit 1
fi

echo "✅ Project directory: $PROJECT_DIR"
echo "✅ Python interpreter: $VENV_PYTHON"
echo "✅ Automation script: $SCRIPT_PATH"
echo ""

# Ask for check interval
read -p "Check interval in seconds (default: 3600 = 1 hour): " INTERVAL
INTERVAL=${INTERVAL:-3600}

echo ""
echo "Configuration:"
echo "  - Check interval: $INTERVAL seconds ($(($INTERVAL/60)) minutes)"
echo "  - Log file: $PROJECT_DIR/Gas/logs/bronze_automation.log"
echo "  - Error log: $PROJECT_DIR/Gas/logs/bronze_automation_error.log"
echo ""

# Create logs directory
mkdir -p "$PROJECT_DIR/Gas/logs"

# Check if service already exists
if [ -f "$PLIST_PATH" ]; then
    echo "⚠️  Service already exists. Unloading..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
fi

# Create the plist file
echo "Creating launchd service configuration..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$SCRIPT_PATH</string>
        <string>--daemon</string>
        <string>--interval</string>
        <string>$INTERVAL</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR/Gas</string>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/Gas/logs/bronze_automation.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/Gas/logs/bronze_automation_error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

echo "✅ Created: $PLIST_PATH"
echo ""

# Load the service
echo "Loading service..."
launchctl load "$PLIST_PATH"

# Wait a moment for service to start
sleep 2

# Check if service is running
if launchctl list | grep -q "$PLIST_NAME"; then
    echo ""
    echo "=================================================="
    echo "✅ Bronze Automation Service Installed!"
    echo "=================================================="
    echo ""
    echo "The service will:"
    echo "  - Start automatically on boot"
    echo "  - Check for new data every $INTERVAL seconds"
    echo "  - Download data based on source schedules:"
    echo "    • EIA: Wednesday 10:30 AM ET"
    echo "    • RBOB: Mon-Fri during market hours"
    echo "    • Retail: Monday mornings"
    echo ""
    echo "Management commands:"
    echo "  View logs:  tail -f $PROJECT_DIR/Gas/logs/bronze_automation.log"
    echo "  Stop:       launchctl stop $PLIST_NAME"
    echo "  Start:      launchctl start $PLIST_NAME"
    echo "  Restart:    launchctl unload '$PLIST_PATH' && launchctl load '$PLIST_PATH'"
    echo "  Uninstall:  launchctl unload '$PLIST_PATH' && rm '$PLIST_PATH'"
    echo ""
    echo "Check status:"
    echo "  launchctl list | grep bronze-automation"
    echo ""
    echo "=================================================="
else
    echo ""
    echo "❌ Service failed to start"
    echo "Check error log: $PROJECT_DIR/Gas/logs/bronze_automation_error.log"
    exit 1
fi
