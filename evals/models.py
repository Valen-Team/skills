"""Grade the agents' solutions with other models answering their Valen calls.

python evals/models.py --runs evals/results/baseline-2 evals/results/codex-baseline-2 evals/results/smoke-1 \\
    --backends valen-0.8b valen-2b valen-4b

LLM backends need an OpenAI-compatible gateway that also serves Anthropic's /messages:
    --gateway https://gateway.example/v1 --gateway-token-env GATEWAY_API_KEY
Results land in evals/results/models/<backend>/<run>/<task>/<workspace>.json.
"""

import argparse
import concurrent.futures
import json
import os
from pathlib import Path

from grade import grade

EVALS = Path(__file__).resolve().parent
BACKENDS = {
    "valen-0.8b": {"kind": "valen", "model": "valen-0.8b", "price": "valen:valen-0.8b"},
    "valen-2b": {"kind": "valen", "model": "valen-2b", "price": "valen:valen-2b"},
    "valen-4b": {"kind": "valen", "model": "valen-4b", "price": "valen:valen-4b"},
    "gpt-6-luna": {"kind": "llm", "adapter": "LLM-OpenAI", "model": "gpt-6-luna", "price": "openai:gpt-6-luna"},
    "gpt-5.6-terra": {"kind": "llm", "adapter": "LLM-OpenAI", "model": "gpt-5.6-terra", "price": "openai:gpt-5.6-terra"},
    "gemini-3.8-flash": {"kind": "llm", "adapter": "LLM-OpenAI", "model": "gemini-3.8-flash",
                         "price": "gemini:gemini-3.8-flash"},
    "claude-haiku-4-5": {"kind": "llm", "adapter": "LLM-Anthropic", "model": "claude-haiku-4-5",
                         "price": "anthropic:claude-haiku-4-5"},
    "claude-sonnet-5-5": {"kind": "llm", "adapter": "LLM-Anthropic", "model": "claude-sonnet-5-5",
                          "price": "anthropic:claude-sonnet-5-5"},
}
PATHS = {"LLM-OpenAI": "/chat/completions", "LLM-Anthropic": "/messages"}


def spec(name, gateway, token_env):
    backend = BACKENDS[name]
    if backend["kind"] == "valen":
        return {"kind": "valen", "model": backend["model"]}
    if not gateway:
        raise SystemExit(f"{name} needs --gateway")
    return {"kind": "llm", "adapter": backend["adapter"],
            "options": {"model": backend["model"], "endpoint": gateway.rstrip("/") + PATHS[backend["adapter"]],
                        "token_env": token_env}}


def usage(calls_path, price, solution):
    from jevalkit.pricing import load_pricing

    calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
    calls = [c for c in calls if c.get("solution") == solution]
    rate = load_pricing().get(price)
    known = all(c["input_tokens"] is not None and c["output_tokens"] is not None for c in calls if c["status"] == 200)
    tokens = {k: sum(c[k] or 0 for c in calls) for k in ("input_tokens", "output_tokens")}
    cost = None if rate is None or not known else (tokens["input_tokens"] * rate[0] + tokens["output_tokens"] * rate[1]) / 1e6
    return {"calls": len(calls), "failed_calls": sum(c["status"] != 200 for c in calls), **tokens, "cost_usd": cost}


def workspaces(runs):
    for run in map(Path, runs):
        for task_dir in sorted(p for p in run.iterdir() if p.is_dir()):
            for arm_dir in sorted(p for p in task_dir.iterdir() if (p / "workspace").is_dir()):
                yield run.name, task_dir.name, arm_dir


def evaluate(name, run, task, arm_dir, args):
    out = EVALS / "results" / "models" / name / run / task / (arm_dir.name + ".json")
    if out.exists() and not args.force:
        return out
    import jevalkit

    calls = out.with_suffix(".calls.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    calls.unlink(missing_ok=True)
    env = {**os.environ, "VALEN_EVAL_BACKEND": json.dumps(spec(name, args.gateway, args.gateway_token_env)),
           "VALEN_EVAL_CALLS": str(calls),
           "PYTHONPATH": os.pathsep.join(filter(None, [str(Path(jevalkit.__file__).parents[1]),
                                                        os.environ.get("PYTHONPATH")]))}
    tag = f".{name}"
    report = grade(arm_dir / "workspace", task, args.solutions, env=env, tag=tag)
    result = {"backend": name, "run": run, "task": task, "workspace": arm_dir.name,
              "agent": "codex" if "codex" in arm_dir.name else "claude",
              "arm": "no-skill" if "no-skill" in arm_dir.name else "skill",
              "solutions": report,
              "usage": {s: usage(calls, BACKENDS[name]["price"], s) for s in args.solutions}}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--backends", nargs="+", choices=BACKENDS, required=True)
    parser.add_argument("--solutions", nargs="+", default=["v1/solution.py"])
    parser.add_argument("--tasks", nargs="+")
    parser.add_argument("--gateway")
    parser.add_argument("--gateway-token-env", default="GATEWAY_API_KEY")
    parser.add_argument("--parallel", type=int, default=3, help="Workspaces graded at once")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    jobs = [(name, run, task, arm) for name in args.backends for run, task, arm in workspaces(args.runs)
            if not args.tasks or task in args.tasks]
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        for path in pool.map(lambda job: evaluate(*job, args), jobs):
            result = json.loads(path.read_text())
            scores = {k: v.get("score") for k, v in result["solutions"].items() if isinstance(v, dict) and k != "task"}
            print(json.dumps({k: result[k] for k in ("backend", "task", "workspace")} | {"scores": scores}))


if __name__ == "__main__":
    main()
