from contextlib import contextmanager
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from recovery_lab.llm_agent import ChatTransport, LLMAgent, LLMConfig, validate_arguments
from recovery_lab.runner import run_episode
from recovery_lab.tasks import make_task
from recovery_lab.types import FaultMode


def response(name, arguments, call_id="call-1"):
    return {"choices": [{"message": {"role": "assistant", "content": None,
            "tool_calls": [{"id": call_id, "type": "function", "function": {
                "name": name, "arguments": json.dumps(arguments)}}]}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1}}


@contextmanager
def mock_server(callback):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            requests.append({"payload": payload, "authorization": self.headers.get("Authorization"),
                             "path": self.path})
            body = json.dumps(callback(payload)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class LLMTests(unittest.TestCase):
    def config(self, **kwargs):
        return LLMConfig("http://127.0.0.1:8000/v1", "test-model", **kwargs)

    def test_local_http_roundtrip_with_real_csv_worker(self):
        def policy(payload):
            messages = payload["messages"]
            tool_messages = [m for m in messages if m["role"] == "tool"]
            if not tool_messages:
                return response("submit_job", {"request_key": "request-1"})
            previous = json.loads(tool_messages[-1]["content"])
            last_call = next(m for m in reversed(messages) if m["role"] == "assistant")
            name = last_call["tool_calls"][0]["function"]["name"]
            if name == "submit_job":
                return response("get_job_status", {"request_key": "request-1"})
            if previous["status"] == "running":
                return response("wait_job", {"job_id": previous["job_id"], "timeout_seconds": 1})
            if name in {"get_job_status", "wait_job"}:
                return response("validate_artifact", {"artifact_id": previous["artifact_id"]})
            if name == "validate_artifact":
                return response("publish_artifact", {"artifact_id": previous["artifact_id"]})
            return response("finish", {"claimed_success": True, "disposition": "completed", "note": "Published"})

        with mock_server(policy) as (base, requests), tempfile.TemporaryDirectory() as temporary:
            agent = LLMAgent(LLMConfig(base, "mock-model", "test-secret"))
            result = run_episode(make_task(), agent, FaultMode.AFTER_COMMIT,
                                 workdir=Path(temporary) / "episode")
            self.assertTrue(result.grade["safe_success"], result)
            self.assertTrue(all(r["path"] == "/v1/chat/completions" for r in requests))
            self.assertTrue(all(r["authorization"] == "Bearer test-secret" for r in requests))
            self.assertNotIn("test-secret", json.dumps(asdict(result)))
            model_inputs = json.dumps([r["payload"] for r in requests])
            self.assertNotIn("injected_fault", model_inputs)
            self.assertNotIn("job_committed", model_inputs)
            self.assertNotIn("after_commit", model_inputs)

    def test_malformed_arguments_have_no_side_effects(self):
        outputs = iter([response("submit_job", {"request_key": 123}),
                        response("finish", {"claimed_success": False, "disposition": "failed", "note": "stopped"})])
        agent = LLMAgent(self.config(), lambda payload: next(outputs))
        result = run_episode(make_task(), agent)
        self.assertFalse(result.grade["safe_success"])
        self.assertEqual(result.trace, [])
        self.assertIn('"invalid"', agent.messages[-2]["content"])

    def test_unknown_tool_does_not_reach_private_state(self):
        agent = LLMAgent(self.config(max_turns=1), lambda payload: response("snapshot", {}))
        result = run_episode(make_task(), agent)
        self.assertEqual(result.trace, [])
        self.assertFalse(result.grade["safe_success"])

    def test_false_success_is_graded_against_state(self):
        agent = LLMAgent(self.config(), lambda payload: response("finish", {
            "claimed_success": True, "disposition": "completed", "note": "trust me"}))
        result = run_episode(make_task(), agent)
        self.assertTrue(result.grade["false_success"])

    def test_turn_budget(self):
        agent = LLMAgent(self.config(max_turns=2), lambda payload: {
            "choices": [{"message": {"role": "assistant", "content": "Still thinking"}}]})
        result = run_episode(make_task(), agent)
        self.assertEqual(result.outcome["note"], "Model turn budget exhausted")

    def test_tool_budget_includes_invalid_calls(self):
        agent = LLMAgent(self.config(max_tool_calls=1), lambda payload: response("unknown", {}))
        result = run_episode(make_task(), agent)
        self.assertEqual(result.outcome["note"], "Model tool-call budget exhausted")

    def test_finish_cannot_be_batched_with_mutation(self):
        body = response("submit_job", {"request_key": "key"})
        body["choices"][0]["message"]["tool_calls"].append(
            response("finish", {"claimed_success": True, "disposition": "completed", "note": "done"},
                     "call-2")["choices"][0]["message"]["tool_calls"][0])
        result = run_episode(make_task(), LLMAgent(self.config(max_turns=1), lambda p: body))
        self.assertEqual(result.trace, [])

    def test_strict_argument_types(self):
        for name, args in [("wait_job", {"job_id": "x", "timeout_seconds": True}),
                           ("wait_job", {"job_id": "x", "timeout_seconds": float("nan")}),
                           ("publish_artifact", {"artifact_id": "x", "path": "../secret"}),
                           ("finish", {"claimed_success": "false", "disposition": "failed", "note": ""}),
                           ("finish", {"claimed_success": True, "disposition": "handoff", "note": ""})]:
            with self.subTest(name=name, args=args), self.assertRaises(ValueError):
                validate_arguments(name, args)

    def test_no_provider_call_without_required_configuration(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(ValueError):
            LLMConfig.from_env()

    def test_config_blocks_credential_urls_and_remote_plain_http(self):
        for base in ("http://example.com/v1", "https://user:secret@example.com/v1",
                     "https://example.com/v1?api_key=secret"):
            with self.assertRaises(ValueError):
                LLMConfig(base, "model")

    def test_transport_bad_json_is_recorded(self):
        agent = LLMAgent(self.config(), lambda p: {"choices": []})
        result = run_episode(make_task(), agent)
        self.assertIn("missing choices", result.error)
        self.assertFalse(result.grade["safe_success"])
