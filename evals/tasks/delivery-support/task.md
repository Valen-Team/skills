# Task: route in-app support messages for a food-delivery app

You are building the support router for **Fastbite**, a food-delivery app in Singapore that serves English- and Chinese-speaking customers. Every in-app support message must go to one queue and carry two flags. Use Valen to build it.

## Output per message

| Field | Values |
| --- | --- |
| `queue` | `late_order`, `missing_or_wrong_item`, `food_quality`, `payment_refund`, `account_access`, `human_review` |
| `safety` | `true` when the message reports a health or safety problem (allergic reaction, food poisoning, foreign object, an unsafe rider), else `false` |
| `compensation` | `true` when the customer asks for money back, credit or a voucher, else `false` |

The labeling rules in `labeling.md` are the business's decisions; follow them.

## Input

Each message is a JSON object: `{"id": "...", "message": "...", "order_status": "delivered" | "on_the_way" | "cancelled" | "none"}`. `order_status` comes from the order system and is always correct.

## Deliverable

Write `solution.py` in this folder exposing:

```python
def predict(item: dict) -> dict:
    """Return {"queue": str, "safety": bool, "compensation": bool} for one message."""
```

`predict` is called once per message by a grader on messages you have not seen. It must call Valen over HTTP and finish within 60 seconds per message. `dev.json` has labeled examples you may use for development.
