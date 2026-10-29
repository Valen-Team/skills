# Task: tag short clips for a stock-footage library

**Reelbank** sells short stock-footage clips. Every uploaded clip needs three searchable tags before it goes live. Use Valen to build the tagger.

## Output per clip

| Field | Values |
| --- | --- |
| `setting` | `kitchen`, `indoor`, `outdoor`, `screen` |
| `activity` | `cooking`, `sport_or_exercise`, `talking`, `other` |
| `people` | `none`, `one`, `several` |

The labeling rules in `labeling.md` are the business's decisions; follow them.

## Input

Each item is `{"id": "...", "video": "<path to an MP4 file>"}`. Clips are 5 to 60 seconds long, landscape or portrait.

## Deliverable

Write `solution.py` in this folder exposing:

```python
def predict(item: dict) -> dict:
    """Return {"setting": str, "activity": str, "people": str} for one clip."""
```

`predict` is called once per clip by a grader on clips you have not seen. It must call Valen over HTTP and finish within 120 seconds per clip. `dev.json` lists labeled examples whose files are in `media/`.
