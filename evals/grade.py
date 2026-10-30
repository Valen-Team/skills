"""Grade a workspace's solution files on a task's hidden test set.

python evals/grade.py WORKSPACE TASK [--solution solution.py solution_v1.py]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent


def test_items(task):
    """Hidden test items without labels; media paths made absolute."""
    rows = json.loads((EVALS / "tasks" / task / "test.json").read_text())
    items = []
    for row in rows:
        item = {k: v for k, v in row.items() if k != "expected"}
        for key in ("image", "video"):
            if key in item:
                item[key] = str(EVALS / item[key])
        items.append(item)
    return rows, items


def interpreter(workspace):
    for candidate in (".venv/bin/python", "venv/bin/python"):
        if (workspace / candidate).exists():
            return str(workspace / candidate)
    return sys.executable


def score(rows, outputs):
    by_id = {o["id"]: o for o in outputs}
    fields = list(rows[0]["expected"])
    correct = {f: 0 for f in fields}
    exact = errors = 0
    per_item = []
    for row in rows:
        out = by_id.get(row["id"], {})
        got = out.get("output") if isinstance(out.get("output"), dict) else {}
        errors += "output" not in out
        hits = {f: got.get(f) == row["expected"][f] for f in fields}
        for f, hit in hits.items():
            correct[f] += hit
        exact += all(hits.values())
        per_item.append({"id": row["id"], "expected": row["expected"], "got": got,
                         **({"error": out["error"]} if "error" in out else {})})
    n = len(rows)
    accuracy = {f: correct[f] / n for f in fields}
    balanced = {}
    for f in fields:
        recalls = []
        for label in {repr(r["expected"][f]) for r in rows}:
            members = [i for i, r in enumerate(rows) if repr(r["expected"][f]) == label]
            recalls.append(sum(per_item[i]["got"].get(f) == rows[i]["expected"][f] for i in members) / len(members))
        balanced[f] = sum(recalls) / len(recalls)
    return {"n": n, "score": sum(balanced.values()) / len(fields), "balanced_accuracy": balanced,
            "accuracy": accuracy, "exact_match": exact / n, "errors": errors, "items": per_item}


def grade(workspace, task, solutions=("v1/solution.py", "solution.py"), timeout=3600, env=None, tag=""):
    workspace = Path(workspace).resolve()
    rows, items = test_items(task)
    items_file = workspace / f".grade_items{tag}.json"
    items_file.write_text(json.dumps(items, ensure_ascii=False))
    report = {"task": task}
    for name in solutions:
        path = workspace / name
        if not path.exists():
            report[name] = {"missing": True}
            continue
        out_file = workspace / f".grade_{name.replace('/', '_')}{tag}.json"
        proc = subprocess.run([interpreter(workspace), str(EVALS / "predict_worker.py"), str(path),
                               str(items_file), str(out_file)], cwd=workspace, capture_output=True,
                              text=True, timeout=timeout, env=env)
        if proc.returncode or not out_file.exists():
            report[name] = {"crashed": True, "stderr": proc.stderr[-2000:]}
            continue
        report[name] = score(rows, json.loads(out_file.read_text()))
    items_file.unlink()
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("task")
    parser.add_argument("--solution", nargs="+", default=["v1/solution.py", "solution.py"])
    args = parser.parse_args()
    report = grade(args.workspace, args.task, args.solution)
    for name in args.solution:
        result = report[name]
        print(name, json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False))
    (Path(args.workspace) / "grade.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
