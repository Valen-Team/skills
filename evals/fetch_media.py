"""Extract the media the tasks use from Valen-Team/VisualDecisionBench into evals/media/.

python evals/fetch_media.py               downloads assets.zip (about 630 MB) into the Hugging Face cache
python evals/fetch_media.py --archive PATH  uses an assets.zip you already have
"""

import argparse
import json
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download

EVALS = Path(__file__).resolve().parent


def needed():
    paths = set()
    for split in EVALS.glob("tasks/*/*.json"):
        for row in json.loads(split.read_text()):
            paths.update(row[key] for key in ("image", "video") if key in row)
    return paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive")
    args = parser.parse_args()
    paths = needed()
    archive = args.archive or hf_hub_download("Valen-Team/VisualDecisionBench", "assets.zip", repo_type="dataset")
    with zipfile.ZipFile(archive) as zf:
        for path in sorted(paths):
            target = EVALS / path
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read("assets/" + path.removeprefix("media/")))
    print(f"{len(paths)} media files in {EVALS / 'media'}")


if __name__ == "__main__":
    main()
