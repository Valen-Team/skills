"""Summarize evals/results/models: first-version score by backend, task and arm, with cost per item.

python evals/summarize_models.py [--solution v1/solution.py] [--calls calls.csv]
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from models import BACKENDS

EVALS = Path(__file__).resolve().parent
TASKS = ("delivery-support", "upload-intake", "clip-tagging")


def load(root, solution):
    rows = []
    for path in sorted((root).rglob("*.json")):
        result = json.loads(path.read_text())
        graded = result["solutions"].get(solution)
        if not isinstance(graded, dict) or "missing" in graded:
            continue
        rows.append({**{k: result[k] for k in ("backend", "run", "task", "workspace", "agent", "arm")},
                     "solution": solution, "cost_usd": result["usage"][solution]["cost_usd"],
                     "score": graded.get("score", 0.0), "crashed": "crashed" in graded,
                     "errors": graded.get("errors"), "n": graded.get("n"), "calls_path": path.with_suffix(".calls.jsonl")})
    return rows


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def table(rows):
    cells = defaultdict(list)
    for r in rows:
        cells[r["backend"], r["task"], r["arm"]].append(r["score"])
    costs = defaultdict(lambda: [0.0, 0])
    for r in rows:
        if r["cost_usd"] is not None and r["n"]:
            costs[r["backend"]][0] += r["cost_usd"]
            costs[r["backend"]][1] += r["n"]
    pct = lambda v: "–" if v is None else f"{100 * v:.1f}"
    lines = ["| Backend | " + " | ".join(f"{t} no skill | {t} skill" for t in TASKS) + " | Mean no skill | Mean skill | USD / item |",
             "| --- |" + " ---: |" * (2 * len(TASKS) + 3)]
    for backend in BACKENDS:
        if not any(k[0] == backend for k in cells):
            continue
        row = [pct(mean(cells[backend, t, arm])) for t in TASKS for arm in ("no-skill", "skill")]
        overall = [pct(mean(mean(cells[backend, t, arm]) for t in TASKS if cells[backend, t, arm]))
                   for arm in ("no-skill", "skill")]
        spent, items = costs[backend]
        cost = f"{spent / items:.5f}" if items else "–"
        lines.append(f"| {backend} | " + " | ".join(row + overall + [cost]) + " |")
    return "\n".join(lines) + "\n"


def export_calls(rows, path):
    with open(path, "w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["started_utc", "request_id", "backend", "task", "workspace", "status", "input_tokens",
                         "output_tokens", "estimated_usd"])
        from jevalkit.pricing import load_pricing

        prices = load_pricing()
        for r in rows:
            rate = prices.get(BACKENDS[r["backend"]]["price"])
            if not r["calls_path"].exists():
                continue
            for line in r["calls_path"].read_text().splitlines():
                c = json.loads(line)
                if c.get("solution") != r["solution"]:
                    continue
                usd = None if rate is None else ((c["input_tokens"] or 0) * rate[0] + (c["output_tokens"] or 0) * rate[1]) / 1e6
                writer.writerow([c.get("started_utc"), c.get("request_id"), r["backend"], r["task"], r["workspace"],
                                 c["status"], c["input_tokens"], c["output_tokens"], usd])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution", default="v1/solution.py")
    parser.add_argument("--calls", help="Write every model call to this CSV for billing reconciliation")
    args = parser.parse_args()
    rows = load(EVALS / "results" / "models", args.solution)
    print(table(rows), end="")
    crashed = [f"{r['backend']}/{r['run']}/{r['task']}/{r['workspace']}" for r in rows if r["crashed"]]
    if crashed:
        print("\nCrashed (scored 0):", ", ".join(crashed))
    if args.calls:
        export_calls(rows, args.calls)


if __name__ == "__main__":
    main()
