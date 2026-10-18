# Real CSV jobs and LLM tool calls

## Two independent switches

`--agent llm` determines who chooses actions. `--backend process` determines where jobs execute.

| Agent | Backend | Meaning |
|---|---|---|
| scripted | memory | Original deterministic controls |
| scripted | process | Real file/process lifecycle without model charges |
| llm | memory | Model decides; environment remains simulated |
| llm | process | Model decides; fixed worker processes real CSV files |

No command automatically launches an LLM server, downloads a model, reads your existing credentials or enables billing. Configure your chosen endpoint explicitly.

## Process lifecycle

1. Read and validate input CSV. The caller file is not modified.
2. Create a fresh directory and normalized `source.csv`.
3. On submit, launch `python -I worker.py` with fixed arguments, no shell, a minimal environment and per-job stdout/stderr log.
4. Register the job and optional idempotency key. A simulated acknowledgement can be lost here.
5. Poll/wait via public tools. A zero exit code PLUS a parseable artifact is required for `ok`.
6. Worker writes a temporary file then atomically replaces its output. Publish also writes a new local file atomically.
7. On runner exit, terminate/reap unfinished workers. Grade actual published contents and source preservation.

Submission commit means **worker launch/registration**, not successful job completion. `get_job_status` and `wait_job` can return `running`/`failed`. Approval remains simulated. A fresh retry key creates another job; repeat publication creates another local publication.

Process supervision is local and cooperative: job timeout is checked during environment synchronization, not by an independent watchdog. This fixed worker does not spawn descendants. Arbitrary untrusted workloads would need a different isolation and process-tree management design.

## Model loop

`LLMAgent` sends a task view and JSON tool schemas to `/chat/completions`. It executes only allowlisted tool calls with strict argument validation, appends each result with its `tool_call_id`, and asks the model again. Provider reasoning_content is preserved when supplied. It does not accept arbitrary filesystem paths, shell commands or grading access as tool arguments. Worker logs may contain local diagnostic paths; review them before exporting traces. Hidden fault metadata is never inserted into model messages.

`finish` must appear alone in its batch and includes claimed_success/disposition/note. A free-text answer triggers a reminder; it is not interpreted as a successful terminal decision. Invalid tool calls consume the model's tool budget but do not mutate the environment. Tool batches are limited to eight calls and processed sequentially.

The HTTP client has a timeout, a response-size limit, refuses redirects, and does not retry requests automatically. Remote plain HTTP and credentials embedded in URLs are rejected. Local loopback HTTP is supported. Transport errors surface in `RunResult.error` without provider response bodies or API keys.

Model/API failures are distinct from the injected job-submission failures. There is no automatic root-cause classifier or provider-specific retry policy.

## What is tested vs untested

Tests use real subprocess CSV workers and a local mock Chat Completions HTTP server. The server emits deterministic tool calls to validate protocol mechanics, side effects, grading and credential omission. It is **not a real model**.

To establish provider support, run the documented command with your own endpoint and inspect `error`, `outcome`, `grade`, `agent_trace` and process logs. Model latency, task ability, cost and success rate have not been measured here. Current schemas target compatible tool-capable chat models; Responses API and provider-native message APIs are not implemented.

## References

- Kimi tool call guidance: https://github.com/MoonshotAI/Kimi-K2/blob/main/docs/tool_call_guidance.md
- vLLM tool calling: https://docs.vllm.ai/en/stable/features/tool_calling/

Pin provider/model/server versions in actual experiments. Tool-call parser setup varies by model and server version.
