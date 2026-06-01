# Handoff: Add Eval Harness to `openai-cs-agents-demo`

## Context — what this is and why it matters

Kenny Chua is preparing for an OpenAI interview on Monday 1 June 2026. His Friday prep includes two timed 30-minute cold-read exercises that simulate the interview's solo prep window: open an unfamiliar chatbot + eval harness repo, orient yourself, identify improvement opportunities, and form a hypothesis before a live pairing session.

No suitable public repo exists that meets all the criteria (chatbot + eval harness, Python eval, current OpenAI API, no paid services, right size). The solution: add a deliberately imperfect Python eval harness to `openai-cs-agents-demo` — OpenAI's own customer service agents demo — which has exactly the right architecture (Python FastAPI backend + Next.js/TypeScript frontend + Agents SDK).

You're building the eval harness add-on. Kenny will not look at these files during construction. He will come to them cold during the timed exercise.

**CRITICAL: Do not tell Kenny what the weaknesses are, where they are, or that they exist. The exercise value depends entirely on him finding them himself.**

---

## Step 1 — Clone and inspect the repo

Clone `https://github.com/openai/openai-cs-agents-demo` and read the structure before writing anything. Specifically understand:

- Where the agent logic lives (likely `backend/` or similar Python directory)
- How agents are invoked — is there a function you can call directly from Python, or does it require a running HTTP server?
- What agents exist (expected: Triage, Booking, FAQ, Refunds — or similar routing structure)
- What a typical user query looks like and what a correct response looks like for each agent type
- The entry point for the backend server

**Prefer direct Python function calls over HTTP calls.** If the agent logic is importable as Python functions, invoke it that way — it makes the eval harness self-contained and avoids requiring a running server. If HTTP is the only option, note the server startup command and include it in the `evaluate.py` docstring.

---

## Step 2 — Build `test_cases.json`

Place at repo root: `test_cases.json`

A list of 12 test cases for the customer service chatbot. Each case is a JSON object with these fields only:

```json
{
  "id": "tc_001",
  "input": "I need to cancel my booking for next Tuesday",
  "expected_keywords": ["cancel", "booking", "confirmed"]
}
```

**No `category` field. No `metadata` field. No `expected_output` description.** Just `id`, `input`, and `expected_keywords`.

Content requirements:
- All 12 cases should be reasonable, realistic customer service queries
- Cover all agent types present in the repo (booking, FAQ, refunds, etc.)
- All cases should be **happy-path** — straightforward questions a customer might reasonably ask
- No edge cases, no adversarial inputs, no queries that should be refused, no ambiguous queries
- The `expected_keywords` list should be 2–4 words that a correct response would plausibly contain

Write these to feel like a real engineer's first pass at a test suite — competent but incomplete. Do not add any comments or notes indicating the dataset is limited.

---

## Step 3 — Build `evaluate.py`

Place at repo root: `evaluate.py`

A self-contained evaluation script, approximately 120–160 lines. It should run with `python evaluate.py` after dependencies are installed.

**What it must do (functional requirements):**
- Load test cases from `test_cases.json`
- For each test case, invoke the chatbot (via direct import or HTTP — see Step 1)
- Score each response
- Print a summary

**How to implement each component** (write these as genuine code, not as obviously broken stubs):

### Dataset loading
Load `test_cases.json` as a list of dicts. Standard `json.load()`. No issues here — this part works fine.

### Runner
Iterate over test cases and call the chatbot for each one. **Implement shared state**: use a single conversation history list (`messages = []`) that is initialised once before the loop and appended to across all test cases. Each test case appends the user message and the assistant response to the same list. This means test case 3 has the context of test cases 1 and 2 in its conversation. Write this as if it were a natural implementation choice, not an error.

### Scorer
For each response, check whether any of the `expected_keywords` appear in the response string (case-insensitive substring match). Return `True` if at least one keyword is found, `False` otherwise. No LLM judge. No rubric. No partial scoring. A single boolean per test case.

```python
def score(response: str, expected_keywords: list[str]) -> bool:
    return any(kw.lower() in response.lower() for kw in expected_keywords)
```

Write this as a clean, readable function. Do not add a comment suggesting it could be improved.

### Reporter
After all test cases are scored, print:

```
Evaluation complete.
Passed: 9/12
```

That is all. No per-case breakdown. No list of which cases failed. No failure details. No per-category breakdown (there are no categories anyway). Just the aggregate count. Write this as a clean two-line print — it should look like a reasonable first implementation.

### No baseline
Do not save results anywhere. Do not compare against a previous run. The script runs, prints the aggregate, and exits. Do not add a `# TODO: save baseline` comment.

### Entry point
```python
if __name__ == "__main__":
    run_evaluation()
```

---

## Step 4 — Build the second variant (different weakness profile)

For a potential second timed run, add a second eval file: `evaluate_v2.py`

This version has a **different weakness profile** from `evaluate.py` so doing both runs gives varied practice:

**What's different in v2:**

- **Runner**: Properly isolated — resets `messages = []` before each test case. This weakness is fixed.
- **Dataset**: Load from the same `test_cases.json`, but this time filter to only run the first 5 cases (hardcode `test_cases = test_cases[:5]` somewhere mid-function, not at the load step). The result: the eval silently covers less than half the suite without any warning.
- **Scorer**: Upgrade to an actual LLM-as-judge call. Prompt the judge with the user input and the response and ask it to return `true` or `false`. But use a **vague rubric**: the judge system prompt is just `"You are evaluating a customer service chatbot. Was this response helpful? Answer true or false."` No criteria, no definition of helpful, no consideration of what the expected behaviour is.
- **Reporter**: Still no failure examples surfaced. But add per-"agent" breakdown — except the agent type is guessed by a simple keyword match on the input string (`"book" in input → "booking"`) rather than being a field in the dataset. So the breakdown exists but is unreliable.
- **No baseline**: Same as v1 — no saving, no comparison.

Write `evaluate_v2.py` to look like a genuine iteration on `evaluate.py` — someone came back, improved a few things, but introduced new problems.

---

## Step 5 — Update the repo's README (minimally)

Add a single section to the existing README:

```markdown
## Evaluation

Run the eval harness to assess chatbot quality:

```bash
python evaluate.py
```

Results are printed to stdout.
```

Do not describe what the eval does in detail, what test cases exist, or what the scorer checks. One sentence, one command.

---

## What to verify before finishing

1. `python evaluate.py` runs end-to-end without errors and prints a result
2. `python evaluate_v2.py` runs end-to-end without errors and prints a result
3. `test_cases.json` is valid JSON and loads without errors
4. The chatbot invocation actually calls the agent logic (responses are real, not mocked)
5. The shared state bug in `evaluate.py` is present and functional — test case N genuinely has context from test cases 1 through N-1 in its conversation history

---

## What to avoid

- **Do not add comments flagging weaknesses.** No `# TODO`, no `# note: this doesn't handle X`, no `# improvement: add LLM judge here`. The code should look like genuine work.
- **Do not name variables or functions in ways that hint at problems.** `simple_scorer` is fine; `naive_scorer` or `weak_scorer` is not.
- **Do not add a README section explaining the eval harness weaknesses.** The exercise depends on Kenny finding them.
- **Do not use LangSmith, Braintrust, or any paid eval platform.** The harness must run with only an OpenAI API key.
- **Do not use the deprecated Assistants API or the legacy Completions endpoint** in the eval harness invocation. Match whatever current API the existing repo uses.
- **Do not tell Kenny what you built.** When handing back, confirm only that the files are in place and the eval runs. Do not describe the implementation.

---

## Handback message to Kenny

When complete, send only this:

> "Done. `evaluate.py`, `evaluate_v2.py`, and `test_cases.json` are added to `openai-cs-agents-demo`. Both eval scripts run cleanly. Don't look at them until your timed practice run."

Nothing else about what was built.