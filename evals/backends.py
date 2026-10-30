"""Answer a solution's Valen API calls with another model, without changing the solution.

A solution calls https://api.valen-team.workers.dev/v1/systemone or /v1/decisions through urllib or
requests. install() intercepts those calls in the worker process:

- {"kind": "valen", "model": "valen-2b"} forwards the unchanged request with only `model` replaced;
- {"kind": "llm", "adapter": "LLM-OpenAI", "options": {...}} answers with a JevalKit LLM baseline,
  translating the request and the response, so the solution reads the same answer format.

Every call is appended to the log as {"endpoint", "status", "input_tokens", "output_tokens", "seconds",
"started_utc", "request_id", "solution"}, so token counts can be reconciled with the provider's billing.
"""

import copy
import datetime
import http.client
import io
import json
import threading
import time
import urllib.error
import urllib.request

ENDPOINTS = ("/v1/systemone", "/v1/decisions")
TRANSIENT, RETRIES = {429, 500, 502, 503, 504}, 4
TEXT_PARTS, IMAGE_PARTS = ("text", "input_text"), ("image_url", "input_image")


def image_url(part):
    url = part.get("image_url")
    return url.get("url") if isinstance(url, dict) else url


def message_state(messages):
    """Chat messages with text and image parts in JevalKit's canonical envelope."""
    out = []
    for message in messages:
        content = message.get("content")
        content = [{"type": "text", "text": content}] if isinstance(content, str) else content
        parts = []
        for part in content:
            if part.get("type") in TEXT_PARTS:
                parts.append({"type": "text", "text": part["text"]})
            elif part.get("type") in IMAGE_PARTS:
                parts.append({"type": "image_url", "image_url": {"url": image_url(part)}})
            else:
                raise ValueError("Unsupported input part: " + str(part.get("type")))
        out.append({"role": "user", "content": parts})
    return {"messages": out}


def is_messages(value):
    return isinstance(value, list) and all(isinstance(m, dict) and "content" in m for m in value)


def systemone_request(payload):
    state = payload.get("state", "")
    if isinstance(state, dict) and is_messages(state.get("messages")):
        state = message_state(state["messages"])
    elif payload.get("assets"):
        text = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
        content = [{"type": "text", "text": text}]
        for ref, asset in payload["assets"].items():
            fmt = {"jpg": "jpeg"}.get(asset.get("format", "png"), asset.get("format", "png"))
            content += [{"type": "text", "text": f"Asset `{ref}`:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/{fmt};base64,{asset['data_base64']}"}}]
        state = {"messages": [{"role": "user", "content": content}]}
    questions = {qid: {k: v for k, v in q.items() if k in ("type", "instructions", "criteria")}
                 for qid, q in payload["questions"].items()}
    return {"state": state, "questions": questions}


def decisions_request(payload):
    source = payload.get("input", "")
    state = message_state(source) if is_messages(source) else source
    questions = {}
    for q in payload["questions"]:
        if q["type"] == "predicate":
            questions[q["name"]] = {"type": "noul", "instructions": q["instructions"],
                                    **({"criteria": q["criteria"]} if q.get("criteria") else {})}
        elif q["type"] == "choice":
            questions[q["name"]] = {"type": "choice", "instructions": q["instructions"],
                                    "criteria": {c["value"]: c.get("description") for c in q["choices"]}}
        else:
            questions[q["name"]] = {"type": "score", "instructions": q["instructions"],
                                    "criteria": [level.get("description") or level["label"] for level in q["levels"]]}
    return {"state": state, "questions": questions}


def decisions_response(payload, answers):
    out = []
    for q in payload["questions"]:
        answer = answers[q["name"]]
        if q["type"] == "predicate":
            out.append({"type": "predicate", "name": q["name"], "probability": answer["noul"]})
        elif q["type"] == "choice":
            out.append({"type": "choice", "name": q["name"], "choice": answer["choice"],
                        "probabilities": [{"value": k, "probability": p} for k, p in answer["probabilities"].items()]})
        else:
            out.append({"type": "score", "name": q["name"], "score": answer["score"],
                        "probabilities": [{"value": int(k), "label": level["label"], "probability": answer["probabilities"][k]}
                                          for k, level in zip(answer["probabilities"], q["levels"])]})
    return out


class Router:
    def __init__(self, spec, log_path, solution=None):
        self.spec, self.log_path, self.solution, self.lock = spec, log_path, solution, threading.Lock()
        self.model = None
        if spec["kind"] == "llm":
            from jevalkit.config import build_model

            self.model = build_model(spec["adapter"], **spec.get("options", {}))

    def log(self, **entry):
        with self.lock, open(self.log_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"solution": self.solution, **entry}) + "\n")

    def answer(self, endpoint, payload, forward):
        """(status, body bytes) for one intercepted call."""
        started, request_id = time.perf_counter(), None
        started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.model is None:
            status, body = forward({**payload, "model": self.spec["model"]})
            usage = (json.loads(body).get("usage") or {}) if status == 200 else {}
        else:
            try:
                request = systemone_request(payload) if endpoint.endswith("systemone") else decisions_request(payload)
                response = self.model.predict(request)
                usage, answers, request_id = response.get("usage") or {}, response["answers"], response.get("request_id")
                result = {"answers": answers if endpoint.endswith("systemone") else decisions_response(payload, answers),
                          "model": self.model.model, "usage": usage}
                status, body = 200, json.dumps(result).encode()
            except Exception as exc:
                usage, request_id = getattr(exc, "usage", None) or {}, getattr(exc, "request_id", None)
                # Non-retryable, so a solution does not resend a request the model cannot answer.
                status, body = 422, json.dumps({"detail": f"{type(exc).__name__}: {exc}"[:500]}).encode()
        self.log(endpoint=endpoint, status=status, input_tokens=usage.get("input_tokens"),
                 output_tokens=usage.get("output_tokens"), seconds=time.perf_counter() - started,
                 started_utc=started_utc, request_id=request_id)
        return status, body


def target(url):
    return next((e for e in ENDPOINTS if url.split("?")[0].endswith(e)), None)


class Reply(io.BytesIO):
    def __init__(self, status, body, url):
        super().__init__(body)
        self.status, self.code, self.url = status, status, url
        self.headers = {"Content-Type": "application/json"}

    def getcode(self):
        return self.status


def install(spec, log_path, solution=None):
    router = Router(spec, log_path, solution)
    original_urlopen = urllib.request.urlopen

    def urlopen(request, data=None, timeout=None, **kwargs):
        url = request.full_url if isinstance(request, urllib.request.Request) else request
        body = request.data if isinstance(request, urllib.request.Request) else data
        endpoint = target(url)
        if endpoint is None or body is None:
            return original_urlopen(request, data, timeout or 60, **kwargs)

        def forward(payload):
            headers = dict(request.header_items()) if isinstance(request, urllib.request.Request) else {}
            if not any(k.lower() == "user-agent" for k in headers):
                headers["User-Agent"] = "valen-skill-evals"
            # Transient network failures are retried here, so they never count against a design.
            for attempt in range(RETRIES):
                try:
                    with original_urlopen(urllib.request.Request(url, json.dumps(payload).encode(), headers),
                                          timeout=timeout or 120) as response:
                        return response.status, response.read()
                except urllib.error.HTTPError as exc:
                    if exc.code not in TRANSIENT or attempt == RETRIES - 1:
                        return exc.code, exc.read()
                except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError):
                    if attempt == RETRIES - 1:
                        raise
                time.sleep(2 ** attempt)

        status, reply = router.answer(endpoint, json.loads(body), forward)
        if status != 200:
            raise urllib.error.HTTPError(url, status, "Error", {}, io.BytesIO(reply))
        return Reply(status, reply, url)

    urllib.request.urlopen = urlopen
    try:
        import requests
    except ImportError:
        return router
    original_request = requests.Session.request

    def session_request(self, method, url, **kwargs):
        endpoint = target(url)
        if method.upper() != "POST" or endpoint is None:
            return original_request(self, method, url, **kwargs)
        payload = kwargs.get("json")
        if payload is None:
            payload = json.loads(kwargs["data"])

        def forward(changed):
            sent = {k: v for k, v in kwargs.items() if k not in ("json", "data")}
            for attempt in range(RETRIES):
                try:
                    response = original_request(self, method, url, json=changed, **sent)
                    if response.status_code not in TRANSIENT or attempt == RETRIES - 1:
                        return response.status_code, response.content
                except requests.exceptions.ConnectionError:
                    if attempt == RETRIES - 1:
                        raise
                time.sleep(2 ** attempt)

        status, reply = router.answer(endpoint, copy.deepcopy(payload), forward)
        response = requests.models.Response()
        response.status_code, response._content, response.url = status, reply, url
        response.headers["Content-Type"] = "application/json"
        response.encoding = "utf-8"
        return response

    requests.Session.request = session_request
    return router
