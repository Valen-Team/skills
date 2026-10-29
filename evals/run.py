"""Run coding agents on the eval tasks, with and without the Valen skill, and grade them.

python evals/run.py --tasks delivery-support upload-intake clip-tagging --arms skill --runs 3
python evals/run.py --agent codex --arms skill no-skill --runs 1
"""

import argparse
import concurrent.futures
import datetime
import json
import shutil
import subprocess
import time
from pathlib import Path

from grade import EVALS, grade

SKILL = EVALS.parent / "skills" / "valen"
PROMPT = """Read task.md and labeling.md in this folder and build the deliverable they describe.

1. Write your first complete version. Before running it on any labeled example (dev.json), copy
   every file it needs into a folder `v1/` so that `v1/solution.py` runs on its own. Never change
   `v1/` afterwards.
2. Then improve it using dev.json and cases you write yourself, and leave the final version in
   `solution.py` (it may import other files in this folder).
3. Finish with NOTES.md: what changed between v1 and the final version, and why.

Use Valen's free hosted API at https://api.valen-team.workers.dev (no key needed).
Work only inside this folder: do not read or write files outside it. A local virtualenv in
`.venv/` is fine; the grader runs your solution with `.venv/bin/python` when it exists."""


# Where each agent discovers a project-level skill.
SKILL_DIRS = {"claude": Path(".claude/skills/valen"), "codex": Path(".agents/skills/valen")}


def prepare(task, arm, workspace, agent="claude"):
    source = EVALS / "tasks" / task
    workspace.mkdir(parents=True)
    for name in ("task.md", "labeling.md", "dev.json"):
        shutil.copy(source / name, workspace / name)
    dev = json.loads((source / "dev.json").read_text())
    for row in dev:
        for key in ("image", "video"):
            if key in row:
                target = workspace / row[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(EVALS / row[key], target)
    if arm == "skill":
        shutil.copytree(SKILL, workspace / SKILL_DIRS[agent])


def finish(run_dir, task, arm, index, agent_seconds=None, agent="claude"):
    """Grade a finished workspace and record the run."""
    report = grade(run_dir / "workspace", task)
    report.update(agent=agent, arm=arm, run=index, agent_seconds=agent_seconds)
    try:
        agent = json.loads((run_dir / "agent.json").read_text())
        report["agent_cost_usd"] = agent.get("total_cost_usd")
        if agent.get("is_error"):
            report["agent_error"] = agent.get("result")
    except (OSError, ValueError):
        report["agent_cost_usd"] = None
    (run_dir / "grade.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return run_dir


def agent_command(agent, workspace, model, budget, permission_mode):
    if agent == "codex":
        # workspace-write keeps writes inside the folder; the agent needs the network for the API and pip.
        command = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "-C", str(workspace),
                   "-s", "workspace-write", "-c", "sandbox_workspace_write.network_access=true",
                   "-o", str(workspace.parent / "agent.last.txt"), PROMPT]
    else:
        command = ["claude", "-p", PROMPT, "--permission-mode", permission_mode, "--output-format", "json",
                   "--setting-sources", "project", "--no-session-persistence", "--max-budget-usd", str(budget)]
    return command + (["--model", model] if model else [])


def run_one(task, arm, index, out, model, budget, timeout, permission_mode, agent="claude"):
    run_dir = out.resolve() / task / (f"{arm}-{index}" if agent == "claude" else f"{agent}-{arm}-{index}")
    workspace = run_dir / "workspace"
    prepare(task, arm, workspace, agent)
    started = time.time()
    command = agent_command(agent, workspace, model, budget, permission_mode)
    try:
        proc = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=timeout)
        if agent == "codex":
            # codex exec prints text, not a JSON result; record failures in the same shape as claude's.
            (run_dir / "agent.log").write_text(proc.stdout)
            (run_dir / "agent.json").write_text(json.dumps(
                {"is_error": proc.returncode != 0, "result": proc.stderr[-2000:] if proc.returncode else None}))
        else:
            (run_dir / "agent.json").write_text(proc.stdout)
        (run_dir / "agent.stderr").write_text(proc.stderr)
    except subprocess.TimeoutExpired:
        (run_dir / "agent.stderr").write_text(f"timeout after {timeout}s")
    return finish(run_dir, task, arm, index, time.time() - started, agent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=sorted(p.name for p in (EVALS / "tasks").iterdir()))
    parser.add_argument("--agent", choices=["claude", "codex"], default="claude")
    parser.add_argument("--arms", nargs="+", choices=["skill", "no-skill"], default=["skill"])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--model", default=None)
    parser.add_argument("--budget-usd", type=float, default=15, help="claude only")
    parser.add_argument("--timeout", type=int, default=5400)
    parser.add_argument("--permission-mode", default="auto",
                        help="claude --permission-mode for agents; auto keeps the safety classifier on")
    parser.add_argument("--prepare-only", action="store_true",
                        help="create the workspaces and print the prompt; run agents yourself, then --grade-only")
    parser.add_argument("--grade-only", action="store_true", help="grade existing workspaces under --out")
    parser.add_argument("--out", type=Path, default=EVALS / "results" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    args = parser.parse_args()
    name = lambda a, i: f"{a}-{i}" if args.agent == "claude" else f"{args.agent}-{a}-{i}"
    jobs = [(t, a, i) for t in args.tasks for a in args.arms for i in range(1, args.runs + 1)]
    if args.prepare_only:
        for t, a, i in jobs:
            prepare(t, a, args.out / t / name(a, i) / "workspace", args.agent)
            print(args.out / t / name(a, i) / "workspace")
        print("\nPrompt for each agent:\n\n" + PROMPT)
        return
    if args.grade_only:
        for t, a, i in jobs:
            print("graded", finish(args.out / t / name(a, i), t, a, i, agent=args.agent), flush=True)
        subprocess.run(["python3", str(EVALS / "summarize.py"), str(args.out)], check=False)
        return
    if args.agent == "codex":
        check = subprocess.run(["codex", "login", "status"], capture_output=True, text=True)
        if check.returncode:
            raise SystemExit("codex CLI is not logged in (run `codex login`): " + (check.stdout + check.stderr)[-400:])
    else:
        check = subprocess.run(["claude", "-p", "Reply with OK.", "--output-format", "json", "--no-session-persistence"],
                               capture_output=True, text=True)
        if check.returncode or json.loads(check.stdout or "{}").get("is_error", True):
            raise SystemExit("claude CLI is not ready (run `claude auth login`): " + (check.stdout or check.stderr)[-400:])
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        futures = [pool.submit(run_one, t, a, i, args.out, args.model, args.budget_usd, args.timeout,
                               args.permission_mode, args.agent) for t, a, i in jobs]
        for future in concurrent.futures.as_completed(futures):
            print("done", future.result(), flush=True)
    subprocess.run(["python3", str(EVALS / "summarize.py"), str(args.out)], check=False)


if __name__ == "__main__":
    main()
