#!/usr/bin/env python3
"""
Cross-Codex plan QA loop.

Flow:
1. Judge current plan with second Codex lane.
2. If strict pass (pass=true and no problems), stop and publish final artifacts.
3. Otherwise rewrite plan and continue.
4. Default safety cap is max_rounds=10; optional --no-cap overrides.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LoopError(Exception):
    pass


class StopRequested(Exception):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path, default: Optional[Any] = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=True) + "\n")


def print_info(msg: str) -> None:
    print(msg, flush=True)


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def parse_markdown_sections(md: str) -> Dict[str, str]:
    lines = md.splitlines()
    sections: Dict[str, List[str]] = {}
    current = "_root"
    sections[current] = []
    header_re = re.compile(r"^#{1,3}\s+(.+?)\s*$")
    for line in lines:
        match = header_re.match(line)
        if match:
            current = normalize_title(match.group(1))
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def extract_list_items(text: str) -> List[str]:
    items: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
        elif stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def build_objective_snapshot(plan_text: str) -> Dict[str, Any]:
    sections = parse_markdown_sections(plan_text)
    summary = sections.get("summary", "")
    scope = sections.get("scope", "")
    acceptance = sections.get("acceptance criteria", "")
    assumptions = sections.get("assumptions and defaults", "")
    goal = ""
    heading_match = re.search(r"^#\s+(.+?)\s*$", plan_text, flags=re.MULTILINE)
    if heading_match:
        goal = heading_match.group(1).strip()
    if not goal:
        goal = summary.splitlines()[0].strip() if summary else "Plan quality feedback loop"

    return {
        "goal": goal,
        "summary_excerpt": summary[:1800],
        "scope_excerpt": scope[:1800],
        "acceptance_criteria": extract_list_items(acceptance),
        "constraints": extract_list_items(assumptions),
        "raw_excerpt": plan_text[:2400],
    }


def format_list(items: List[str]) -> str:
    if not items:
        return "[]"
    return "\n".join(f"- {item}" for item in items)


def validate_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate_against_schema(data: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    expected_type = schema.get("type")
    if expected_type and not validate_type(data, expected_type):
        errors.append(f"{path}: expected {expected_type}, got {type(data).__name__}")
        return errors

    if expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_allowed = schema.get("additionalProperties", True)
        assert isinstance(data, dict)
        for key in required:
            if key not in data:
                errors.append(f"{path}.{key}: missing required field")
        for key, value in data.items():
            if key in properties:
                errors.extend(validate_against_schema(value, properties[key], f"{path}.{key}"))
            elif additional_allowed is False:
                errors.append(f"{path}.{key}: additional property not allowed")
    elif expected_type == "array":
        item_schema = schema.get("items")
        if item_schema is not None:
            assert isinstance(data, list)
            for idx, item in enumerate(data):
                errors.extend(validate_against_schema(item, item_schema, f"{path}[{idx}]"))

    return errors


def extract_fenced_blocks(raw: str) -> List[str]:
    blocks: List[str] = []
    for match in re.finditer(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL):
        blocks.append(match.group(1).strip())
    return blocks


def extract_json_objects(raw: str) -> List[str]:
    objects: List[str] = []
    start: Optional[int] = None
    depth = 0
    in_string = False
    escaped = False
    for idx, ch in enumerate(raw):
        if start is None:
            if ch == "{":
                start = idx
                depth = 1
                in_string = False
                escaped = False
            continue

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                objects.append(raw[start : idx + 1])
                start = None
    return objects


def parse_json_robust(raw: str) -> Tuple[Optional[Dict[str, Any]], str]:
    candidates: List[Tuple[str, str]] = []
    stripped = raw.strip()
    candidates.append((stripped, "strict"))
    first_line = stripped.splitlines()[0].strip() if stripped else ""
    if first_line:
        candidates.append((first_line, "first-line"))
    for block in extract_fenced_blocks(raw):
        candidates.append((block, "fenced"))
    for obj in extract_json_objects(raw):
        candidates.append((obj, "embedded-object"))

    for payload, source in candidates:
        if not payload:
            continue
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value, source
    return None, "none"


def run_subprocess(
    cmd: List[str],
    cwd: Path,
    timeout_sec: int = 1200,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        input=input_text,
        timeout=timeout_sec,
    )


def run_codex_exec(prompt: str, schema_path: Path, cwd: Path, model: Optional[str] = None) -> Tuple[int, str, str]:
    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--output-schema",
        str(schema_path),
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append("-")
    
    proc = run_subprocess(cmd, cwd=cwd, input_text=prompt)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def parse_with_validation(raw_stdout: str, schema: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
    parsed, parse_mode = parse_json_robust(raw_stdout)
    if parsed is None:
        return None, parse_mode, ["No JSON object could be parsed from output."]
    errors = validate_against_schema(parsed, schema)
    if errors:
        return None, parse_mode, errors
    return parsed, parse_mode, []


def repair_json_with_codex(raw_output: str, schema_path: Path, schema: Dict[str, Any], cwd: Path, model: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], str, List[str], str]:
    schema_text = json.dumps(schema, indent=2, ensure_ascii=True)
    repair_prompt = (
        "You are a strict JSON repair tool.\n"
        "Return only one JSON object that conforms exactly to the schema.\n"
        "Do not add commentary.\n\n"
        "Schema:\n"
        f"{schema_text}\n\n"
        "Raw output to repair:\n"
        "```text\n"
        f"{raw_output[:24000]}\n"
        "```"
    )
    try:
        code, out, err = run_codex_exec(repair_prompt, schema_path, cwd, model=model)
    except FileNotFoundError:
        code, out, err = -1, "", "codex CLI not found"
        
    combined = out + (("\n" + err) if err else "")
    if code != 0:
        return None, "repair-failed", [f"repair codex exec failed with exit code {code}"], combined
    parsed, parse_mode, errors = parse_with_validation(out, schema)
    if parsed is None:
        return None, f"repair-{parse_mode}", errors, combined
    return parsed, f"repair-{parse_mode}", [], combined


def should_stop(state_path: Path) -> bool:
    state = read_json(state_path, {})
    return bool(state.get("stop_requested"))


def write_manual_handoff_files(
    round_dir: Path,
    phase: str,
    prompt: str,
    schema_path: Path,
    output_file: Path,
) -> None:
    prompt_file = round_dir / f"manual_{phase}_prompt.md"
    instructions_file = round_dir / f"manual_{phase}_instructions.txt"
    write_text(prompt_file, prompt)
    instructions = (
        f"Manual handoff required for phase: {phase}\n\n"
        "In another terminal/session, run:\n"
        f"Get-Content -Raw \"{prompt_file}\" | codex exec --ephemeral --skip-git-repo-check --output-schema \"{schema_path}\" - > \"{output_file}\"\n\n"
        "Save full command output to the output file shown above.\n"
        "This loop will continue automatically after the file appears and parses.\n"
    )
    write_text(instructions_file, instructions)


def wait_for_manual_result(
    round_dir: Path,
    phase: str,
    prompt: str,
    schema_path: Path,
    schema: Dict[str, Any],
    state_path: Path,
) -> Tuple[Dict[str, Any], str, str]:
    output_file = round_dir / f"manual_{phase}_output.txt"
    write_manual_handoff_files(round_dir, phase, prompt, schema_path, output_file)
    print_info(f"[fallback/manual] waiting for {phase} output file: {output_file}")
    wait_tick = 0
    last_seen_mtime: Optional[float] = None
    while True:
        if should_stop(state_path):
            raise StopRequested("stop_requested=true in loop_status.json")
        if output_file.exists() and output_file.stat().st_size > 0:
            current_mtime = output_file.stat().st_mtime
            if last_seen_mtime is None or current_mtime != last_seen_mtime:
                last_seen_mtime = current_mtime
                raw = read_text(output_file)
                parsed, parse_mode, errors = parse_with_validation(raw, schema)
                if parsed is not None:
                    return parsed, raw, f"manual-{parse_mode}"
                print_info(f"[fallback/manual] invalid JSON for {phase}: {'; '.join(errors)}")
                print_info("[fallback/manual] overwrite the same output file with corrected content.")
        wait_tick += 1
        if wait_tick % 10 == 0:
            print_info(f"[fallback/manual] still waiting for {phase} output...")
        time.sleep(3)


def summarize_fix_history(fix_history: List[str], max_items: int = 8) -> List[str]:
    if not fix_history:
        return []
    return fix_history[-max_items:]


def build_judge_prompt(
    plan_text: str,
    objective_snapshot: Dict[str, Any],
    fix_history: List[str],
    objective_header: str,
    judge_rubric: str,
) -> str:
    return (
        f"{objective_header}\n\n"
        f"{judge_rubric}\n\n"
        "# Objective Snapshot\n"
        "```json\n"
        f"{json.dumps(objective_snapshot, indent=2, ensure_ascii=True)}\n"
        "```\n\n"
        "# Previously Applied Fixes (recent)\n"
        f"{format_list(summarize_fix_history(fix_history))}\n\n"
        "# Plan To Judge\n"
        "```markdown\n"
        f"{plan_text}\n"
        "```\n"
    )


def build_rewrite_prompt(
    plan_text: str,
    objective_snapshot: Dict[str, Any],
    fix_history: List[str],
    judge_result: Dict[str, Any],
    objective_header: str,
    rewrite_prompt_template: str,
) -> str:
    problems = judge_result.get("problems", [])
    rewrite_instructions = judge_result.get("rewrite_instructions", [])
    return (
        f"{objective_header}\n\n"
        f"{rewrite_prompt_template}\n\n"
        "# Objective Snapshot\n"
        "```json\n"
        f"{json.dumps(objective_snapshot, indent=2, ensure_ascii=True)}\n"
        "```\n\n"
        "# Previously Applied Fixes (recent)\n"
        f"{format_list(summarize_fix_history(fix_history))}\n\n"
        "# Judge Findings\n"
        "```json\n"
        f"{json.dumps(judge_result, indent=2, ensure_ascii=True)}\n"
        "```\n\n"
        "# Rewrite Instructions (priority order)\n"
        f"{format_list([str(x) for x in rewrite_instructions])}\n\n"
        "# Problems To Resolve\n"
        f"{format_list([str(x) for x in problems])}\n\n"
        "# Current Plan\n"
        "```markdown\n"
        f"{plan_text}\n"
        "```\n\n"
        "Important:\n"
        "1. Preserve prior resolved issues unless a newer finding makes them invalid.\n"
        "2. Keep the plan decision-complete.\n"
    )


def load_required_file(path: Path) -> str:
    if not path.exists():
        raise LoopError(f"required file not found: {path}")
    return read_text(path)


def strict_pass(judge_result: Dict[str, Any]) -> bool:
    return bool(judge_result.get("pass")) and len(judge_result.get("problems", [])) == 0


def run_phase(
    phase: str,
    prompt: str,
    schema_path: Path,
    schema: Dict[str, Any],
    round_dir: Path,
    state: Dict[str, Any],
    state_path: Path,
    repo_root: Path,
    mode: str,
    model: Optional[str] = None,
) -> Tuple[Dict[str, Any], str, str]:
    raw_path = round_dir / f"{phase}_raw_output.txt"
    prompt_path = round_dir / f"{phase}_prompt.md"
    parsed_path = round_dir / f"{phase}_result.json"
    write_text(prompt_path, prompt)

    active_lane = state.get("current_lane", "auto" if mode in ("auto", "hybrid") else "manual")
    if mode == "manual":
        active_lane = "manual"

    if active_lane == "auto":
        try:
            code, out, err = run_codex_exec(prompt, schema_path, repo_root, model=model)
        except FileNotFoundError:
            code, out, err = -1, "", "codex CLI not found"
            
        combined = out + (("\n" + err) if err else "")
        write_text(raw_path, combined)
        if code == 0:
            parsed, parse_mode, errors = parse_with_validation(out, schema)
            if parsed is not None:
                write_json(parsed_path, parsed)
                return parsed, combined, f"auto-{parse_mode}"

            repaired, repair_mode, repair_errors, repair_raw = repair_json_with_codex(out, schema_path, schema, repo_root, model=model)
            write_text(round_dir / f"{phase}_repair_raw_output.txt", repair_raw)
            if repaired is not None:
                write_json(parsed_path, repaired)
                return repaired, repair_raw, f"auto-{repair_mode}"

            auto_error = f"{phase} parse failed: {'; '.join(errors + repair_errors)}"
        else:
            auto_error = f"{phase} codex exec failed with exit code {code}"

        if mode == "hybrid":
            print_info(f"[fallback] auto lane failed for {phase}: {auto_error}")
            print_info("[fallback] switching to manual lane for the remainder of this run.")
            state["current_lane"] = "manual"
            state["last_updated_at"] = now_iso()
            write_json(state_path, state)
        else:
            raise LoopError(auto_error)

    parsed, manual_raw, parse_mode = wait_for_manual_result(
        round_dir=round_dir,
        phase=phase,
        prompt=prompt,
        schema_path=schema_path,
        schema=schema,
        state_path=state_path,
    )
    write_text(raw_path, manual_raw)
    write_json(parsed_path, parsed)
    return parsed, manual_raw, parse_mode


def collect_round_summaries(run_dir: Path) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for round_dir in sorted(run_dir.glob("round_*")):
        path = round_dir / "round_summary.json"
        data = read_json(path)
        if isinstance(data, dict):
            summaries.append(data)
    return summaries


def build_final_report(
    state: Dict[str, Any],
    run_dir: Path,
    final_report_path: Path,
    approved_plan_path: Path,
) -> None:
    summaries = collect_round_summaries(run_dir)
    lines: List[str] = []
    lines.append("# Plan Loop Final Report")
    lines.append("")
    lines.append(f"- status: `{state.get('status', 'unknown')}`")
    lines.append(f"- run_id: `{state.get('run_id', '')}`")
    lines.append(f"- rounds_completed: `{state.get('round', 0)}`")
    lines.append(f"- mode: `{state.get('mode', '')}`")
    lines.append(f"- current_lane: `{state.get('current_lane', '')}`")
    lines.append(f"- started_at: `{state.get('started_at', '')}`")
    lines.append(f"- ended_at: `{state.get('last_updated_at', '')}`")
    lines.append("")

    if summaries:
        lines.append("| Round | Lane | Judge Pass | Problems | Blocking | Summary |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for item in summaries:
            lines.append(
                f"| {item.get('round', '')} | {item.get('lane', '')} | "
                f"{item.get('judge_pass', '')} | {item.get('problem_count', '')} | "
                f"{item.get('blocking', '')} | {str(item.get('judge_summary', '')).replace('|', '/')} |"
            )
        lines.append("")

    latest_plan = state.get("current_plan_path", "")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- latest_plan: `{latest_plan}`")
    lines.append(f"- run_dir: `{run_dir}`")
    lines.append(f"- approved_plan: `{approved_plan_path}`")
    lines.append("")

    if state.get("status") == "passed":
        lines.append("Result: strict pass achieved (`pass=true` and `problems=[]`).")
    elif state.get("status") == "needs_human_tiebreaker":
        lines.append("Result: max rounds reached without strict pass.")
    elif state.get("status") == "stopped":
        lines.append("Result: stopped manually.")
    else:
        lines.append("Result: run ended without strict pass.")
    lines.append("")
    lines.append("Manual review is required before implementation.")
    lines.append("")

    write_text(final_report_path, "\n".join(lines))


def ensure_layout(output_base: Path) -> None:
    dirs = [
        output_base / "iterations",
        output_base / "final",
        output_base / "state",
        output_base / "manual_handoff",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_tool_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-Codex plan feedback loop")
    parser.add_argument("--plan", required=True, help="Path to the current plan markdown file")
    parser.add_argument("--mode", choices=["auto", "hybrid", "manual"], default="hybrid")
    parser.add_argument("--max-rounds", type=int, default=999)
    parser.add_argument("--no-cap", action="store_true", help="Disable max-round limit")
    parser.add_argument("--resume", action="store_true", help="Resume from loop_status.json")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Specify the model to use for codex exec")
    return parser.parse_args()
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tool_root = get_tool_root()
    
    input_plan = Path(args.plan).resolve()
    if not input_plan.exists() and not args.resume:
        raise LoopError(f"plan file not found: {input_plan}")
        
    plan_stem = input_plan.stem
    workspace_root = input_plan.parent
    output_base = workspace_root / f".{plan_stem}_loop"
    ensure_layout(output_base)

    state_dir = output_base / "state"
    state_path = state_dir / "loop_status.json"
    objective_path = state_dir / "objective_snapshot.json"
    final_dir = output_base / "final"
    approved_plan_path = final_dir / "approved_plan.md"
    final_report_path = final_dir / "final_report.md"

    judge_schema_path = tool_root / "schemas" / "plan_judge_result.schema.json"
    rewrite_schema_path = tool_root / "schemas" / "plan_rewrite_result.schema.json"
    judge_schema = read_json(judge_schema_path)
    rewrite_schema = read_json(rewrite_schema_path)
    if not isinstance(judge_schema, dict) or not isinstance(rewrite_schema, dict):
        raise LoopError("invalid schema JSON file(s)")

    prompt_dir = tool_root / "prompts"
    objective_header = load_required_file(prompt_dir / "objective_header.md")
    judge_rubric = load_required_file(prompt_dir / "judge_rubric.md")
    rewrite_template = load_required_file(prompt_dir / "rewrite_prompt.md")

    if args.resume:
        state = read_json(state_path)
        if not isinstance(state, dict):
            raise LoopError("cannot resume: missing/invalid loop_status.json")
        if state.get("status") in {"passed", "needs_human_tiebreaker"}:
            raise LoopError("cannot resume a completed run; start a new run without --resume")
        run_dir = Path(state.get("run_dir", ""))
        if not run_dir.exists():
            raise LoopError(f"cannot resume: run_dir not found: {run_dir}")
        current_plan_path = Path(state.get("current_plan_path", ""))
        if not current_plan_path.exists():
            raise LoopError(f"cannot resume: current_plan_path not found: {current_plan_path}")
        objective_snapshot = read_json(objective_path)
        if not isinstance(objective_snapshot, dict):
            objective_snapshot = build_objective_snapshot(read_text(current_plan_path))
            write_json(objective_path, objective_snapshot)
        mode = str(state.get("mode", args.mode))
        max_rounds = int(state.get("max_rounds", args.max_rounds))
        no_cap = bool(state.get("no_cap", args.no_cap))
        state["status"] = "running"
        state["last_updated_at"] = now_iso()
        write_json(state_path, state)
    else:
        run_id = dt.datetime.now(dt.timezone.utc).strftime("run_%Y%m%d_%H%M%S")
        run_dir = output_base / "iterations" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        current_plan_path = input_plan
        plan_text = read_text(current_plan_path)
        objective_snapshot = build_objective_snapshot(plan_text)
        write_json(objective_path, objective_snapshot)
        write_json(run_dir / "objective_snapshot.json", objective_snapshot)
        mode = args.mode
        max_rounds = args.max_rounds
        no_cap = args.no_cap
        state = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "round": 0,
            "mode": mode,
            "current_lane": "auto" if mode in ("auto", "hybrid") else "manual",
            "max_rounds": max_rounds,
            "no_cap": no_cap,
            "status": "running",
            "last_result": None,
            "current_plan_path": str(current_plan_path),
            "fix_history": [],
            "started_at": now_iso(),
            "last_updated_at": now_iso(),
            "stop_requested": False,
        }
        write_json(state_path, state)

    print_info("[plan-loop] started")
    print_info(f"[plan-loop] run_dir={run_dir}")
    print_info(f"[plan-loop] mode={mode}, no_cap={no_cap}, max_rounds={max_rounds}")

    try:
        while True:
            if should_stop(state_path):
                raise StopRequested("stop_requested=true in loop_status.json")

            rounds_completed = int(state.get("round", 0))
            if not no_cap and rounds_completed >= max_rounds:
                state["status"] = "needs_human_tiebreaker"
                state["last_updated_at"] = now_iso()
                write_json(state_path, state)
                break

            round_num = rounds_completed + 1
            round_dir = run_dir / f"round_{round_num:04d}"
            round_dir.mkdir(parents=True, exist_ok=True)

            current_plan_path = Path(state["current_plan_path"])
            plan_text = read_text(current_plan_path)
            write_text(round_dir / "input_plan.md", plan_text)

            judge_prompt = build_judge_prompt(
                plan_text=plan_text,
                objective_snapshot=objective_snapshot,
                fix_history=list(state.get("fix_history", [])),
                objective_header=objective_header,
                judge_rubric=judge_rubric,
            )
            print_info(f"[round {round_num}] judging...")
            judge_result, _judge_raw, judge_parse_mode = run_phase(
                phase="judge",
                prompt=judge_prompt,
                schema_path=judge_schema_path,
                schema=judge_schema,
                round_dir=round_dir,
                state=state,
                state_path=state_path,
                repo_root=workspace_root,
                mode=mode,
                model=args.model,
            )

            pass_strict = strict_pass(judge_result)
            problem_count = len(judge_result.get("problems", []))
            round_summary: Dict[str, Any] = {
                "round": round_num,
                "lane": state.get("current_lane", ""),
                "judge_pass": bool(judge_result.get("pass")),
                "strict_pass": pass_strict,
                "problem_count": problem_count,
                "blocking": bool(judge_result.get("blocking")),
                "judge_summary": str(judge_result.get("summary", "")),
                "judge_parse_mode": judge_parse_mode,
            }

            if pass_strict:
                write_text(approved_plan_path, plan_text)
                round_summary["status"] = "passed"
                write_json(round_dir / "round_summary.json", round_summary)

                state["round"] = round_num
                state["status"] = "passed"
                state["current_plan_path"] = str(current_plan_path)
                state["approved_plan_path"] = str(approved_plan_path)
                state["last_result"] = judge_result
                state["last_updated_at"] = now_iso()
                write_json(state_path, state)
                break

            rewrite_prompt = build_rewrite_prompt(
                plan_text=plan_text,
                objective_snapshot=objective_snapshot,
                fix_history=list(state.get("fix_history", [])),
                judge_result=judge_result,
                objective_header=objective_header,
                rewrite_prompt_template=rewrite_template,
            )
            print_info(f"[round {round_num}] rewriting...")
            rewrite_result, _rewrite_raw, rewrite_parse_mode = run_phase(
                phase="rewrite",
                prompt=rewrite_prompt,
                schema_path=rewrite_schema_path,
                schema=rewrite_schema,
                round_dir=round_dir,
                state=state,
                state_path=state_path,
                repo_root=workspace_root,
                mode=mode,
                model=args.model,
            )

            revised_plan = str(rewrite_result.get("revised_plan_markdown", "")).strip()
            if not revised_plan:
                raise LoopError(f"round {round_num}: rewrite result has empty revised_plan_markdown")

            revised_plan_path = round_dir / "revised_plan.md"
            write_text(revised_plan_path, revised_plan + "\n")
            round_summary["rewrite_parse_mode"] = rewrite_parse_mode
            round_summary["rewrite_summary"] = str(rewrite_result.get("summary", ""))
            round_summary["status"] = "continued"
            write_json(round_dir / "round_summary.json", round_summary)

            fix_history = list(state.get("fix_history", []))
            for item in rewrite_result.get("applied_fixes", []):
                fix_history.append(str(item))
            state["fix_history"] = fix_history[-80:]
            state["round"] = round_num
            state["current_plan_path"] = str(revised_plan_path)
            state["last_result"] = judge_result
            state["last_updated_at"] = now_iso()
            write_json(state_path, state)

        build_final_report(state, run_dir, final_report_path, approved_plan_path)
        print_info("[plan-loop] completed")
        print_info(f"[plan-loop] status={state.get('status')}")
        print_info(f"[plan-loop] final_report={final_report_path}")
        if state.get("status") == "passed":
            print_info(f"[plan-loop] approved_plan={approved_plan_path}")
            print_info("CROSS-CHECK DONE: no remaining plan problems.")
            print_info("Manual review required before implementation.")
        elif state.get("status") == "needs_human_tiebreaker":
            print_info("Loop reached max rounds. Manual tie-breaker required.")
        return 0

    except StopRequested as exc:
        state["status"] = "stopped"
        state["last_updated_at"] = now_iso()
        write_json(state_path, state)
        build_final_report(state, run_dir, final_report_path, approved_plan_path)
        print_info(f"[plan-loop] stopped: {exc}")
        print_info(f"[plan-loop] final_report={final_report_path}")
        return 2
    except KeyboardInterrupt:
        state["status"] = "stopped"
        state["last_updated_at"] = now_iso()
        write_json(state_path, state)
        build_final_report(state, run_dir, final_report_path, approved_plan_path)
        print_info("[plan-loop] interrupted by user")
        print_info(f"[plan-loop] final_report={final_report_path}")
        return 130
    except Exception as exc:  # pylint: disable=broad-except
        state["status"] = "error"
        state["last_updated_at"] = now_iso()
        state["error"] = str(exc)
        write_json(state_path, state)
        try:
            build_final_report(state, Path(state.get("run_dir", output_base / "iterations")), final_report_path, approved_plan_path)
        except Exception:
            pass
        print_info(f"[plan-loop] error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
