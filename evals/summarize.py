"""Summarize graded runs: python evals/summarize.py RESULTS_DIR [RESULTS_DIR ...]"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def cell(values):
    if not values:
        return "–"
    mean = statistics.mean(values)
    return f"{mean:.1%} ± {statistics.stdev(values):.1%}" if len(values) > 1 else f"{mean:.1%}"


def main():
    groups = defaultdict(lambda: defaultdict(list))
    for root in map(Path, sys.argv[1:]):
        for path in sorted(root.glob("*/*/grade.json")):
            report = json.loads(path.read_text())
            if report.get("agent_error"):
                print(f"skipped {path.parent}: {report['agent_error'][:120]}")
                continue
            key = (report["task"], f'{report.get("agent", "claude")}/{report["arm"]}')
            for version in ("v1/solution.py", "solution.py"):
                result = report.get(version, {})
                groups[key][version].append(result.get("score", 0.0))
            groups[key]["cost"].append(report.get("agent_cost_usd") or 0.0)
    lines = ["| Task | Arm | Runs | First version | Final version | Agent cost (USD) |", "| --- | --- | ---: | --- | --- | ---: |"]
    for (task, arm), values in sorted(groups.items()):
        lines.append(f"| {task} | {arm} | {len(values['solution.py'])} | {cell(values['v1/solution.py'])} | "
                     f"{cell(values['solution.py'])} | {statistics.mean(values['cost']):.2f} |")
    firsts = defaultdict(list)
    for (task, arm), values in groups.items():
        firsts[arm].append(statistics.mean(values["v1/solution.py"]))
    lines.append("")
    for arm, values in sorted(firsts.items()):
        lines.append(f"Primary metric, {arm}: mean first-version score (balanced accuracy) over {len(values)} tasks = {statistics.mean(values):.1%}")
    text = "\n".join(lines)
    print(text)
    (Path(sys.argv[1]) / "summary.md").write_text(text + "\n")


if __name__ == "__main__":
    main()
