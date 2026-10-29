---
name: valen
license: Apache-2.0
description: >
  Integration craft for Valen, a multimodal System One decision model that answers typed questions
  about text, images and video with probabilities over the candidates you supply. Use when
  building, reviewing or debugging code that calls Valen (hosted API, Python / JavaScript SDK,
  ONNX, GGUF, vLLM or SGLang); when writing its questions, candidates or state; when replacing an
  LLM prompt-and-parse step, keyword rules or a hand-tuned image heuristic with a typed question;
  or when choosing a model size and runtime.
---

# Build with Valen

Valen (万澜) is a System One decision model in three sizes (0.8B, 2B, 4B). Your application sends
**state**: text, images, or frames from a video. It also sends typed **questions**. Valen answers
each question with probabilities over the candidates you supplied:

- **Noul** (Decisions: `predicate`): the probability that one statement is true.
- **Choice**: one of several mutually exclusive candidates, with a distribution over all of them.
- **Score**: ordered levels you describe; returns the level distribution and the expected index.

Both API protocols run the same model. **System One** (`POST /v1/systemone`) keys questions by
ID. **Decisions** (`POST /v1/decisions`) uses a question list. Pick the one that matches the
codebase; the TypeSafe-compatible System One format is the natural fit for code already written
against Jev. The field names differ:

| | System One | Decisions |
| --- | --- | --- |
| Evidence | `state`: a string or a JSON object | `input`: a string or messages with `input_text` / `input_image` parts |
| Questions | object keyed by ID | list with `name` |
| Yes/no type | `noul`, optional `criteria: {"true": "...", "false": "..."}` | `predicate` |
| Choice | `choice`, `criteria: {value: description}` | `choice`, `choices: [{value, description}]` |
| Score | `score`, `criteria: [lowest, ..., highest]` | `score`, `levels: [{label, description}]` |
| Answer fields | `noul`; `choice` + `probabilities`; `score` + `probabilities` | `probability`; `choice` + `probabilities`; `score` + `probabilities` |

The hosted endpoints accept, per request, **one image**, **up to 8 questions**, up to 16 candidates
per question, criteria of up to 300 characters each and instructions of up to 2,000 characters.
Requests over a limit return HTTP 400 with the limit in `detail`. Local runtimes set their own
limits (`VALEN_MAX_IMAGES` and similar).

This skill collects patterns that produce reliable integrations. Test alternatives when the
application calls for them.

## Judgments from Valen, decisions in code

Valen makes the judgments; code decides what to do with them. Write each decision as a **truth
table**. Valen supplies the inputs, such as "Is the product photo blurred?" or "Which intent does
the message express?". Code maps those inputs to an action.

A question like "Should this listing be rejected?" asks Valen to make the decision. Break it into
the judgments it depends on (logo present, watermark present, product matches the title) and put
the rule in code, where it is visible and testable. Writing out the table also exposes gaps in the
business logic: a combination with no defined outcome is a product decision to settle in code.

## Live docs

The website is the source of truth for request syntax, SDK APIs, model files and measured results.
Read the relevant pages as part of the task.

- Start at the [documentation index](https://valen-team.github.io/llms.txt). Append `.md` to any
  documentation or cookbook path to get the page as Markdown, for example
  `https://valen-team.github.io/docs/valen/api/systemone.md`.
- Request and response schemas: the [OpenAPI spec](https://valen-team.github.io/openapi.json),
  [System One](https://valen-team.github.io/docs/valen/api/systemone.md),
  [Decisions](https://valen-team.github.io/docs/valen/api/decisions.md) and
  [List Models](https://valen-team.github.io/docs/valen/api/list-models.md).
- Writing questions and known hard cases:
  [question design](https://valen-team.github.io/docs/valen/question-design.md).
- Reading probabilities, confidence and thresholds:
  [probabilities](https://valen-team.github.io/docs/valen/probabilities.md) and
  [calibration](https://valen-team.github.io/docs/valen/calibration.md).
- Choosing a size and runtime: [choosing](https://valen-team.github.io/docs/valen/choosing.md),
  [ONNX & SDKs](https://valen-team.github.io/docs/valen/onnx.md),
  [GGUF](https://valen-team.github.io/docs/valen/gguf.md),
  [vLLM](https://valen-team.github.io/docs/valen/vllm-plugin.md),
  [SGLang](https://valen-team.github.io/docs/valen/sglang-plugin.md).
- Complete, tested recipes: the [cookbook](https://valen-team.github.io/cookbook/).

Every `.md` URL has an HTML page at the same path with a trailing slash instead, such as
`https://valen-team.github.io/docs/valen/api/systemone/`; `/sitemap.xml` lists them all. If the
docs are unreachable, use the protocol table above, or read the types in the installed `valen-sdk` (Python) or
`@valen-team/sdk` (JavaScript) package and tell the user which source you used.

## Pick a runtime

| The application needs | Use |
| --- | --- |
| A quick trial or a prototype | Free hosted API at `https://api.valen-team.workers.dev`, no key |
| Higher quotas | Keyed endpoint `https://llm-proxy.openxxlab.com` with `Authorization: Bearer $VALEN_API_KEY` |
| In-process Python or JavaScript, CPU or GPU, text / images / video | ONNX through `Valen.local(...)` in the SDK |
| A local HTTP service on CPU | `valen serve` from the Python SDK, or GGUF with the Valen-patched llama.cpp / Ollama |
| An existing NVIDIA serving stack | The vLLM or SGLang plugin |

Both hosted endpoints serve `/v1/systemone`, `/v1/decisions` and `/v1/models`; the SDK's
`Valen.remote(...)` takes the base URL with `/v1` appended.

Start with 0.8B locally and 2B on the hosted API, then compare 2B and 4B on the user's own cases.
`GET /v1/models` on the hosted endpoints also lists models that are not Valen; use the IDs that
start with `valen-` (`valen-0.8b`, `valen-2b`, `valen-4b`). Send an explicit `User-Agent` header;
the free API's edge rejects some default client agents (Python `urllib`) with HTTP 403
`error code: 1010`. It answers HTTP 429 when its quota is used up; wait a minute and back off
rather than retrying in a tight loop.

## Workflow

1. **Start from the decision logic.** Begin with what the application will show, accept, route or
   hand to a person. Sketch the truth table and list the inputs it needs. Inputs that need an
   understanding of language or images make good questions. Arithmetic, dates, exact lookups and
   policy belong in code. Give every combination of answers an outcome, including the band where a
   Noul sits between its thresholds. If code alone can decide reliably, tell the user: a fixed
   format (one ID pattern, one date layout) belongs to a regex, while a value written many ways or
   across languages makes a good question.
2. **Keep all question wording in one module.** Questions, candidates, criteria and thresholds are
   what people audit and edit most. Version them together with the model ID.
3. **Probe the API** with representative, hard and negative cases, as described in
   [Test against real cases](#test-against-real-cases).
4. **Integrate.** Log the exact request payload and the returned `model_id` (hosted endpoints
   report `revision` as `local`, so `model_id` plus your question-set version identify a run).
   Surface a failed call as an error, never as a "no". Keep API keys on the server.

If the request is open-ended, offer the two or three [patterns](#patterns) that best fit the goal
and recommend one. If it is concrete, build it.

## Design the state

Apply the **human test**: could a smart person, shown only this state and this question, answer
quickly by intuition? When a question fails it, fix the state before the wording.

- **Give what a person would look at.** The subject line and body of an email, the sender of each
  message, the full thread rather than the last line, names rather than raw IDs, the item in
  question rather than the whole catalogue.
  State facts code already knows ("all replies arrived after the refund was issued").
- **Say what the text is.** A field such as `"inbox": "Customer support email for a small online
  clothing shop"` gives terse messages their meaning: with it, "where's my stuff" moved from `none`
  to shipment tracking at 0.99.
- **Supply facts the model may lack**, such as what an internal product name refers to.
- **Keep every field relevant.** A field added for one question can sway another, and an empty list
  can read as a signal.
- **Use named fields.** In System One, `state` can be a JSON object; descriptive keys work better
  than a serialized string, and questions can refer to parts by path in backticks, such as
  `message` or `order.items`.
- **Keep the user's language.** English questions work over state in Chinese or other languages;
  translate neither.
- **Images.** Send one image per request on the hosted endpoints. In System One, put it in `assets`
  under a descriptive reference, mention that
  reference in `state`, and send the header `TypeSafe-Danger-Zone-Images: true`. In Decisions,
  send `input_image` content parts next to `input_text`. PNG, JPEG and WebP are accepted. Crop to
  the region a person would inspect; a full-resolution screenshot where the target is a few pixels
  wide fails the human test.
- **Video.** The SDKs read video directly with `valen-sdk[onnx,video]`. For HTTP backends, extract
  frames in code: the middle frame for a static attribute, several evenly spaced frames for an
  action. On the hosted endpoints send one frame per request (or tile a few frames into one
  contact-sheet image), average each candidate's probability over the frames in code, and record
  which frame indices and timestamps each answer used. Count people per frame; never add counts
  across frames, since the same person appears in many of them.
- **Leave out what nobody can judge**, such as an unreadable crop. The answer there is noise that
  code will treat as signal.

## Write the questions

Break complex judgments into atomic ones and combine them in code with boolean logic, weighted sums
or thresholds. Rather than "Is this listing fraudulent?", ask the concrete things that make a
listing fraudulent. Each question should ask for **one judgment** a person could make at a glance.

- **Ask the observable thing.** "Is there a watermark over the product?" rather than "Does the image
  have quality problems?".
- **One judgment per question; beware the "or".** Two conditions that lead to different actions
  work better as two questions, and a list of rules as one question per rule. Several signs of
  one judgment (tone, sarcasm and threats all meaning "the customer is angry") work better as one
  Noul whose criteria name them; separate Nouls ORed in code add up their false positives.
- **Name the subject directly** and anchor intent to the user's goal: "Which item in `order.items`
  does the customer want to return?".
- **Write plainly.** A question is not an LLM prompt. Preambles, "think step by step" and output
  format instructions add noise. Option descriptions belong in the criteria. Phrase it so that a
  true answer means yes, and avoid double negatives.
- **Name the confusing case in the candidate it belongs to.** If policy questions keep landing on
  `refund`, describe them in `none` ("questions about shop policies before buying"). Writing
  "a policy question is not a refund request" into the `refund` description mentions the concept
  there and pulls probability towards `refund`. After the change, rerun the cases that were already
  right. If the case still lands on the wrong candidate, add a Noul that separates it structurally
  ("`message` is about an order the customer has already placed") and combine the answers in code.

### Candidates and criteria

- **Give Choice a `none` candidate when nothing may fit.** Choice spreads probability over the
  candidates you supply, so a missing category still produces a confident wrong answer. In the
  [unknown-categories study](https://valen-team.github.io/cookbook/unknown-categories.md) an
  address-change request went to shipment tracking at 99.3% until a described `none` was added.
  Describe what `none` covers ("outside refunds, tracking and invoices, or too little information
  to choose") and route it to review. For Score and single-statement checks, pair the question with
  a Noul that asks whether the subject is present at all.
- **Use descriptive candidate values.** `refund_request` and `shipping_delay` help the model;
  `A` / `option_1` give it nothing and can bias the answer. Candidate values are part of the input.
- **Ask the distinctions the model can see; map to business buckets in code.** When a business
  bucket lumps unlike things together (`other` covering dancing, music and walking), ask for the
  concrete categories and map them in code. When several candidates lead to the same action, add
  their probabilities before thresholding, so a split between them does not look like doubt.
- **Keep candidates distinct and concrete.** Shared wording pulls probability together. Split a
  candidate that covers several meanings. Ask direction and magnitude as separate questions.
- **Use two or more candidates.** A single-candidate Choice always returns probability 1.
- **Describe each Score level as a situation** that makes sense on its own: "The customer mentions
  a minor inconvenience", not "More upset than the previous level".
- **Describe a Noul's `false` case concretely** with `criteria: {"true": "...", "false": "..."}`
  ("the package arrived on time" rather than "not late").
- **Use one Noul per statement when several can be true.** A message that is both a complaint and a
  refund request should not force a Choice to split probability between them.
- **Detect mixed requests with one Noul.** Pair the intent Choice with "The customer makes more
  than one separate request". One Noul per category drifts high on near-empty messages ("hi").
  Its `false` criterion should name what is not a second request: a fallback ("exchange it, or
  refund if you can't") and background remarks. Set where its middle band goes from the cost of
  review; sending the whole band to people over-routes single requests.

## Compose requests

**Bundle questions that share state.** Valen reads the state once and scores every question in one
forward pass, so one request with five questions is far cheaper than five requests. The hosted
endpoints take up to 8 questions per request; send a second request with the same state for more.

**Ask speculatively.** Ask "Is this a return request?" together with "Which item in `order.items` is
being returned?" and read the second answer only when the first is yes. The second question needs
no "if" clause; code handles the condition.

**Keep a request's question set and order stable.** Valen places all questions of a request in one
causal sequence, so the other questions and their order can shift an answer. Later questions
barely move earlier ones (shifts under 0.01 in tests), so put the most important, most stable
question first. Freeze the set and order you validated, and revalidate the
questions after any you add, remove, reword or reorder. Split into separate requests when:

- code needs one answer to build the next state or candidates;
- a question measurably moves another question's answer;
- different question sets are versioned or cached separately.

## Read the answers

- **A probability is the model's estimate for that candidate.** Do probability arithmetic in code.
  A Noul near 0.5 usually means the state does not settle the question.
- **`confidence` measures concentration, not accuracy.** For Choice it is how far the top
  probability rises above uniform. Compare distributions, and use held-out accuracy to decide what
  to automate.
- **Start Noul thresholds at 0.7 and 0.3** and route the band between them to its own row of the
  truth table (often human review). A flag that is only displayed and triggers no action can
  use a single 0.5 cut. Start Choice gates at a top probability of 0.8 and a gap
  of 0.2 to the second candidate. Fit the final values on labeled validation cases from the
  user's workflow, with the
  [calibration tools](https://valen-team.github.io/docs/valen/calibration.md), and check them on
  cases you did not tune on.
- **Score returns the expected index** (`sum(i * p[i])`). It can sit in the middle of a two-peaked
  distribution, so read the level probabilities. Map levels to business values with an explicit
  utility table in code.
- **Answers are deterministic** for a given payload and model, so one run per wording is enough to
  compare variants.
- **`temperature`** rescales the logits. Leave it at `1.0` unless it was fitted on a calibration set
  for this model and question set.
- Thresholds belong to a model ID, runtime, question set and candidate order. Revalidate when any
  of them changes.

## Test against real cases

Ask the user before sending their data to the hosted API: say which endpoint, which cases, and
point out any personal data. The free endpoint needs no key; the keyed one uses `VALEN_API_KEY`.
For private data, prefer a local runtime.

- Write the labeling rule for edge cases first ("delivered but not received" goes to which queue?);
  it is a business decision, and expected labels follow from it.
- Start with a few representative cases, plus hard ones and some whose answer is "no" or `none`.
- Compare wordings by sending each variant over the same state and reading individual answers, not
  only aggregates.
- Keep the exact payload and returned `model_id` for each case so any result can be rerun.
- Write a held-out set before you iterate, and a second one after you freeze the final version.
  Check each change on cases you did not tune on: a clause that fixes one tuning case often moves
  others.

### When an answer looks wrong

Check, in this order:

1. the payload as actually sent, including images and the model ID;
2. the state, against the human test;
3. the candidates: is the right answer among them, and is there a `none`?
4. the scope: can the question be split into smaller judgments?
5. the other questions in the request and their order;
6. the wording.

Then read the [question design](https://valen-team.github.io/docs/valen/question-design.md) page for
the hard cases already recorded and how to restructure around them. If a clear question with
complete state still gets a confidently wrong answer, collect the payload and open an issue at
[Valen-Team/Valen](https://github.com/Valen-Team/Valen/issues).

### Yellow flags

A good change makes a definition clearer or improves the state. Wording written to produce a
particular value is **prompt gymnastics** and tends to break on new inputs and the next model.
Watch for criteria that name specific test items, a new clause per failing case, thresholds fitted
to a handful of cases, tests that assert exact probabilities, and code that quietly overrides
answers. The structural fix is usually better state, a separate question, or code.

## Patterns

Complete recipes in the [cookbook](https://valen-team.github.io/cookbook/), grouped by goal. Each runs end to end, offline from recorded answers or live against the API:

| Goal | Questions | Recipe |
| --- | --- | --- |
| Route and fill arguments | Choice over intents or functions, a predicate for the null case, every argument asked speculatively | [function calling](https://valen-team.github.io/cookbook/function-calling.md), [support router built with this skill](https://valen-team.github.io/cookbook/skill-support-router.md), [calibrated routing](https://valen-team.github.io/cookbook/calibrated-routing.md), [unknown categories](https://valen-team.github.io/cookbook/unknown-categories.md) |
| Select instead of generate | Code finds candidate values; a choice picks one, a predicate says whether any fits | [pick the right date](https://valen-team.github.io/cookbook/value-extraction.md) |
| Find and judge evidence | One predicate per retrieved item, in its own request; sort in code | [rerank](https://valen-team.github.io/cookbook/rerank.md) |
| Verify and escalate | Separate "supported" and "contradicted" predicates; one predicate per policy rule | [citation check](https://valen-team.github.io/cookbook/citation-check.md), [LLM guardrails](https://valen-team.github.io/cookbook/llm-guardrails.md) |
| Inspect images and video | One predicate per field or checklist rule; the same questions per frame, smoothed in code | [scanned forms](https://valen-team.github.io/cookbook/document-check.md), [product screening](https://valen-team.github.io/cookbook/product-screening.md), [event timeline](https://valen-team.github.io/cookbook/event-monitoring.md), [video tagging](https://valen-team.github.io/cookbook/video-tagging.md) |
| Turn answers into data | One score per dimension; weights live in code | [composite scoring](https://valen-team.github.io/cookbook/composite-scoring.md) |
| Run locally or adapt | Same request shape over ONNX or a local service; fine-tune when state and wording are not enough | [local inference](https://valen-team.github.io/cookbook/local-inference.md), [domain fine-tuning](https://valen-team.github.io/cookbook/domain-finetuning.md) |
