# ZeroDefect Codex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Tired of shipping buggy plans?** This AI-powered system ruthlessly critiques and perfects your implementation plans until they're bulletproof. No more "it should work" - only "it WILL work."

## ⚠️ CRITICAL PREREQUISITE: The "Automation" Requirements
This tool is built specifically for users of the **Codex platform** utilizing the latest high-reasoning models.

### 🟢 For Fully Automated Mode (Recommended)
To let the script "self-improve" and loop automatically until your plan is perfect, **you MUST have**:
1. The **Codex CLI** installed: `npm install -g @openai/codex`
2. **Active API Credits** on your OpenAI/Codex account.
3. The **Codex VS Code Extension** installed and authenticated.

### 🟡 For Manual Fallback Mode
If you don't have the CLI or run out of credits, the script still works, but **it is manual**. You will have to copy-paste prompts into the VS Code extension for every single iteration until the judge is satisfied.

---

## 🔥 What Makes This Special

Imagine having a **brutally honest AI reviewer** that never lets you get away with:
- Hand-wavy assumptions
- Hidden edge cases
- Logical loopholes
- Vague requirements

This tool doesn't collaborate - it **destroys weak reasoning** and rebuilds your plans from the ground up, iterating until perfection. It leverages the specialized reasoning of the `gpt-5.3-codex` engine to enforce a strict zero-defect standard.

## 🚀 Quick Start (Choose Your Path)

### ⚡ For Non-Technical Users: One-Click Setup
**Just run the notebook!** No command line required for basic setup.

1. **Open the setup notebook in VS Code or Jupyter**:
   - **macOS**: [automation_macOS/Setup_Manual.ipynb](automation_macOS/Setup_Manual.ipynb)
   - **Windows**: [automation_windows/Setup_Manual.ipynb](automation_windows/Setup_Manual.ipynb)
2. **Run all cells** - it will verify your environment and set up the foundation.
3. **Enable "Auto Mode"**: Run `npm install -g @openai/codex` in a terminal.
4. **Start using**: Open a new terminal and type `plan-loop your-plan.md`

### 🛠️ For Developers: Manual Setup

#### macOS
```bash
cd automation_macOS
./INSTALL.sh
source ~/.zshrc
plan-loop your-plan.md
```

#### Windows
```powershell
cd automation_windows
.\INSTALL.bat
# Restart terminal/IDE to refresh PATH
plan-loop your-plan.md
```

## 🔬 How The Magic Works

1. **Feed it your draft** - Rough ideas, incomplete thoughts, or full specs.
2. **Unleash the critic** - The script parses your markdown and feeds it to the Codex 5.3 engine.
3. **The Loop (Fully Automated)** - If you have the Codex CLI, the script **automatically loops**! It gets feedback, rewrites the plan, and keeps going until the judge gives a "True" status (perfection).
4. **The Manual Fallback** - If the CLI is missing, the script generates prompt files (`prompt_judge.txt`, `prompt_rewrite.txt`) for manual copy-pasting.
5. **Claim victory** - A perfect plan emerges, battle-tested and ready for execution.

### The AI Arsenal
- **Viciously Critical Auditor**: No mercy, no compromises.
- **GPT-5.3-Codex Powered**: Maximum reasoning power via `codex exec`.
- **999-Round Endurance**: Stops only at perfection (strict pass: `pass=true` and `problems=[]`).
- **State Preservation**: Resume interrupted sessions safely via session markers.
- **Hybrid Intelligence**: Automatically switches to manual mode if CLI limits are reached.

## 📁 What's Inside

```
├── automation_macOS/          # macOS Environment
│   ├── Setup_Manual.ipynb     # ⚡ One-click setup
│   ├── scripts/plan_loop.py   # Core AI automation engine
│   ├── prompts/               # Judge & rewrite AI personalities
│   ├── schemas/               # Quality validation rules (JSON)
│   └── INSTALL.sh             # traditional installer
├── automation_windows/        # Windows Environment
│   └── [same structure]
├── .gitignore                 # Root level protection
└── README.md                  # You are here
```

## 🤝 Join The Crusade

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Test ruthlessly (like our AI)
4. Submit your battle-tested PR

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---
**Built for the Uncompromising.** For teams that demand zero-defect plans before a single line of code is written.