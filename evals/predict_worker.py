"""Run one solution file over items in its own interpreter: python predict_worker.py SOLUTION ITEMS OUT."""

import concurrent.futures
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

solution, items_path, out_path = map(Path, sys.argv[1:4])
if os.environ.get("VALEN_EVAL_BACKEND"):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import backends

    backends.install(json.loads(os.environ["VALEN_EVAL_BACKEND"]), os.environ["VALEN_EVAL_CALLS"],
                     solution.relative_to(Path.cwd()).as_posix())
sys.path.insert(0, str(solution.parent))
spec = importlib.util.spec_from_file_location("solution_under_test", solution)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(item):
    started = time.perf_counter()
    try:
        return {"id": item["id"], "output": module.predict(item), "seconds": time.perf_counter() - started}
    except Exception as exc:
        return {"id": item["id"], "error": f"{type(exc).__name__}: {exc}", "seconds": time.perf_counter() - started}


items = json.loads(items_path.read_text())
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    results = list(pool.map(run, items))
out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str))
