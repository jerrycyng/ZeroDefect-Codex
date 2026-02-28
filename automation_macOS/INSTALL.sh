#!/bin/bash

# Installation script for Codex Plan Loop on macOS
# This adds the tool to your PATH by modifying ~/.zshrc or ~/.bashrc

set -e

INSTALL_DIR="$HOME/CodexPlanLoop"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Codex Plan Loop globally to: $INSTALL_DIR"

# 1. Create the installation directory
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# 2. Copy the tool files (excluding git and artifacts)
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/ 2>/dev/null || true
rm -rf "$INSTALL_DIR/.git" "$INSTALL_DIR/plans" "$INSTALL_DIR/INSTALL.sh" 2>/dev/null || true

# Ensure the plans directory exists but is empty
mkdir -p "$INSTALL_DIR/plans"

# 3. Create the global wrapper script
cat > "$INSTALL_DIR/plan-loop" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/scripts/plan_loop.py" "$@"
EOF
chmod +x "$INSTALL_DIR/plan-loop"

# 4. Add to PATH if not already there
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

if ! grep -q "CodexPlanLoop" "$SHELL_RC" 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "Added $INSTALL_DIR to PATH in $SHELL_RC"
    echo "Please run 'source $SHELL_RC' or restart your terminal."
else
    echo "Directory is already in your PATH."
fi

echo ""
echo "Installation Complete! 🎉"
echo "You can now run 'plan-loop <plan_file.md>' from any folder."
echo "If the command isn't found, run: source $SHELL_RC"