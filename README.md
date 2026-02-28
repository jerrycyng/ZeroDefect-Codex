# Codex Prompt Automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Tired of shipping buggy plans?** This AI-powered system ruthlessly critiques and perfects your implementation plans until they're bulletproof. No more "it should work" - only "it WILL work."

## ⚠️ CRITICAL PREREQUISITE: The "Automation" Requirements
This tool is built specifically for users of the **Codex platform**. 

### 🟢 For Fully Automated Mode (Recommended)
To let the script "self-improve" and loop automatically until your plan is perfect, **you MUST have**:
1. The **Codex CLI** installed: `npm install -g @openai/codex`
2. **Active API Credits** on your OpenAI/Codex account.
3. The **Codex VS Code Extension** installed and authenticated.

### 🟡 For Manual Fallback Mode
If you don't have the CLI or run out of credits, the script still works, but **it is tedious**. You will have to manually copy-paste prompts into the VS Code extension for every single iteration until the judge is satisfied. (Yes, this means you might be copy-pasting 10+ times!)

---

## 🔥 What Makes This Special

Imagine having a **brutally honest AI reviewer** that never lets you get away with:
- Hand-wavy assumptions
- Hidden edge cases
- Logical loopholes
- Vague requirements

This tool doesn't collaborate - it **destroys weak reasoning** and rebuilds your plans from the ground up, iterating until perfection. It uses the `gpt-5.3-codex` model by default to enforce a strict zero-defect standard.

## 🚀 Quick Start (Choose Your Path)

### ⚡ For Non-Technical Users: One-Click Setup
**Just run the notebook!** No command line required for basic setup.

1. **Open the setup notebook in VS Code or Jupyter**:
   - **macOS**: `automation_macOS/Setup_Manual.ipynb`
   - **Windows**: `automation_windows/Setup_Manual.ipynb`
2. **Run all cells** - it will verify your environment and set up the foundation.
3. **Wait! For the "Magic" Automated Loop**: You must also run `npm install -g @openai/codex` in a terminal to enable "Auto Mode."
4. **Start using**: Open a new terminal and type `plan-loop your-plan.md`

### 🛠️ For Developers: Manual Setup

#### macOS
```bash
cd automation_macOS
./INSTALL.sh
source ~/.zshrc  # or restart terminal
plan-loop your-plan.md
```

#### Windows
```powershell
cd automation_windows
.\INSTALL.bat
# Restart terminal/IDE if needed
plan-loop your-plan.md
```

## 🎯 Real-World Impact

**Before Codex Automation:**
- "This plan looks good... I think"
- Weeks spent debugging obvious flaws
- Stakeholder surprises during implementation
- "We didn't think of that edge case"

**After Codex Automation:**
- Zero-defect plans that survive real-world scrutiny
- Confidence in your technical decisions
- Faster development cycles
- Professional-grade documentation

## 🔬 How The Magic Works

1. **Feed it your draft** - Rough ideas, incomplete thoughts, whatever.
2. **Unleash the critic** - The script parses your markdown and feeds it to Codex.
3. **The Loop (Fully Automated)** - If you have the Codex CLI, the script **automatically loops**! It gets the feedback, rewrites the plan, and keeps going until the judge gives a "True" status (perfection).
4. **The Manual Fallback** - If the CLI fails or is missing, the script generates text prompt files for you. You'll have to manually copy-paste into the VS Code extension for every iteration (which can be 10+ times!).
5. **Claim victory** - Perfect plan emerges, battle-tested and ready.

### The AI Arsenal
- **Viciously Critical Auditor**: No mercy, no compromises.
- **GPT-5.3-Codex**: Maximum reasoning power via `codex exec`.
- **999-Round Endurance**: Stops only at perfection (strict pass: `pass=true` and `problems=[]`).
- **State Preservation**: Resume interrupted sessions safely.
- **Hybrid Intelligence**: Automatically switches to manual mode if the CLI hits an API limit.

## 📁 What's Inside

```
├── automation_macOS/          # macOS battle station
│   ├── Setup_Manual.ipynb     # ⚡ One-click setup for beginners
│   ├── scripts/plan_loop.py   # Core AI automation engine
│   ├── prompts/               # Judge & rewrite AI personalities
│   ├── schemas/               # Quality validation rules (JSON schemas)
│   └── INSTALL.sh             # Traditional installer
├── automation_windows/        # Windows command center
│   └── [same structure]
└── README.md                  # You are here
```

## 🛠️ Tech Specs

- **Language**: Python 3.8+ (battle-hardened)
- **AI Engine**: Codex VS Code Extension (default model: `gpt-5.3-codex`)
- **Output**: Surgical JSON critiques + pristine markdown
- **Resilience**: Auto-resume + hybrid/manual fallback lanes
- **Zero Mercy**: Only perfection passes

## ⚠️ Important Battle Notes

- **The AI is mean on purpose** - that's how you get perfection.
- **Zero defects = success** - anything less gets rewritten.
- **Hidden folders created** - `.your-plan_loop` contains your evolution history, state files, and final reports.
- **All iterations saved** - full audit trail for compliance.

## 🤝 Join The Crusade

1. Fork this repository
2. Create your feature branch
3. Test ruthlessly (like our AI)
4. Submit your battle-tested PR

## 📄 License

MIT License - see [LICENSE](LICENSE) for the fine print.

## 🙏 Built For The Uncompromising

For developers who don't settle for "good enough." For teams that demand perfection. For anyone who wants their plans to actually work in the real world.

**Ready to eliminate plan failures forever?** Let's get started.</content>
<parameter name="filePath">c:\Users\jerry\OneDrive\PC\Lenovo X240\Documents\NUS\Github\Codex Prompt Automation\README.md