# Task: sort image uploads for a notes app

**Snapnote** is a notes app. Users drop images into a note, and the app files each one so it can offer the right tool: text extraction for documents, a chart reader, a book lookup, and so on. Some uploads come from phone cameras pointed at things, some are screenshots. Use Valen to build the sorter.

## Output per image

| Field | Values |
| --- | --- |
| `kind` | `document`, `screenshot`, `chart`, `book_cover`, `photo`, `diagram` |
| `readable_text` | `true` when the image contains words a person could read and copy out (a heading, a label, a sentence), else `false` |
| `usable` | `false` when the image is too blurry, dark, cut off or badly framed for a person to tell what it shows, else `true` |

The labeling rules in `labeling.md` are the business's decisions; follow them.

## Input

Each item is `{"id": "...", "image": "<path to a JPEG or PNG file>"}`.

## Deliverable

Write `solution.py` in this folder exposing:

```python
def predict(item: dict) -> dict:
    """Return {"kind": str, "readable_text": bool, "usable": bool} for one image."""
```

`predict` is called once per image by a grader on images you have not seen. It must call Valen over HTTP and finish within 60 seconds per image. `dev.json` lists labeled examples whose files are in `media/`.
