# Codex Plan Loop Tool (macOS)

A headless, automated QA loop that uses Codex to review, critique, and rewrite implementation plans until they meet a strict zero-defect standard.

## Quick Start (Global CLI)
This makes `plan-loop` available in any folder on your macOS system.

1. **Install**: Run the installer in the root of this folder:
   ```bash
   ./INSTALL.sh
   ```
2. **Source your shell**: Run `source ~/.zshrc` (or `~/.bashrc` if using bash) or restart your terminal.
3. **Run**: Now you can type `plan-loop your-plan.md` from anywhere!

---

## Detailed Usage Guide
If you don't want to install it globally, you can use the local scripts.

## Usage

The tool is configured to use the **Viciously Critical Auditor** persona and the **GPT-5.3-Codex** model with high reasoning for maximum technical rigor. By default, it will run for up to **999 rounds** to ensure perfection.

### The Whole Flow

1. **Step 1: Write Your First Draft**
   Create a markdown file (e.g., `my_plan.md`) and paste your rough ideas, research report, or initial implementation plan into it. Save it anywhere on your computer.

2. **Step 2: Start the Loop**
   Open your terminal in that folder and run:
   ```bash
   plan-loop my_plan.md
   ```
   *The AI will now enter a brutal judging/rewriting loop in the background.*

3. **Step 3: Monitor Progress**
   Watch the terminal output. You will see it performing rounds:
   - `[round 1] judging...`
   - `[round 1] rewriting...`
   - `[round 2] judging...`
   - *This will continue until the Judge finds ZERO loopholes.*

4. **Step 4: Get Your "Pass-Through" Version**
   Once the terminal says `CROSS-CHECK DONE`, look for a new hidden folder called `.<plan_name>_loop` next to your original file.
   - **`final/approved_plan.md`**: Your cleaned, hardened, and AI-critiqued final version.
   - **`final/final_report.md`**: A full audit report of every flaw found and fixed during the process.

## Command Reference

```bash
# Standard run (uses high-depth GPT-5.3-Codex, max 999 rounds)
plan-loop my_plan.md

# Override model if needed
plan-loop my_plan.md --model gpt-5.3-codex

# Resume an interrupted run
plan-loop my_plan.md --resume

# Forced stop
# Press Ctrl+C in the terminal at any time.
```

### Where do the files go?
The tool will create a hidden folder right next to your plan file called `.<plan_name>_loop`. 
For example, if you run `plan-loop my_plan.md`, it will create a `.my_plan_loop` folder containing:
- `iterations/`: The round-by-round history of the AI's critiques and rewrites.
- `final/approved_plan.md`: The final, perfect plan (only created if it passes!).
- `final/final_report.md`: A summary of the run.
- `state/`: The internal state files (so you can resume if it stops).

Because the state is tied to the specific plan name, **you can safely run multiple plan loops in the same folder at the same time**, as long as they have different file names!
