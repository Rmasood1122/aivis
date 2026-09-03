"""Mocked tests for openai_adapter — no network, no credentials.

Covers: A10 row schema · sha256-over-text-alone · K05 no-key-in-row ·
C11 no-row-on-error · fast-fail on auth · bounded retry on 429/timeout ·
declared parameter adaptation on 400-temperature · D0 malformed-200 refusal.
"""

import hashlib
import io
import json
import unittest
import urllib.error
from unittest import mock

import openai_adapter as oa

KEY = "sk-test-FAKE-KEY-0000"


def _ok_response(text="Purple and Tempur-Pedic are often recommended.",
                 model="gpt-4o-mini-2024-07-18"):
    payload = {
        "id": "chatcmpl-test123",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 9},
    }

    class _Resp:
        headers = {"x-request-id": "req_test_abc"}

        def read(self):
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return _Resp()


def _http_error(code, body=""):
    return urllib.error.HTTPError(
        oa.OPENAI_URL, code, "err", hdrs=None, fp=io.BytesIO(body.encode())
    )


class TestOpenAIAdapter(unittest.TestCase):
    def _run(self, side_effect, **kw):
        with mock.patch.object(oa.urllib.request, "urlopen") as m:
            m.side_effect = side_effect
            row = oa.run_once_openai(
                "best mattress for back pain?", "gpt-4o-mini", KEY,
                prompt_id="MT-B01", bank_version="v1",
                backoff_base=0, _sleep=lambda s: None, **kw,
            )
        return row, m

    def test_success_row_schema_and_hash(self):
        row, m = self._run([_ok_response()])
        for field in ("engine", "surface", "model", "model_requested",
                      "temperature", "ts", "request_id", "prompt_id",
                      "bank_version", "request_payload", "response_text",
                      "sha256", "usage", "param_adaptations"):
            self.assertIn(field, row)
        self.assertEqual(
            row["sha256"],
            hashlib.sha256(row["response_text"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(row["model"], "gpt-4o-mini-2024-07-18")  # served
        self.assertEqual(m.call_count, 1)

    def test_sha256_over_response_text_alone(self):
        row, _ = self._run([_ok_response(text="same text")])
        row2, _ = self._run([_ok_response(text="same text",
                                          model="different-model")])
        self.assertEqual(row["sha256"], row2["sha256"])  # payload-independent

    def test_no_key_anywhere_in_row(self):
        row, _ = self._run([_ok_response()])
        self.assertNotIn(KEY, json.dumps(row))
        self.assertNotIn("Authorization", json.dumps(row))

    def test_auth_error_fast_fail_no_row(self):
        with mock.patch.object(oa.urllib.request, "urlopen") as m:
            m.side_effect = [_http_error(401, '{"error":"invalid key"}')]
            with self.assertRaises(oa.EngineError):
                oa.run_once_openai("q", "gpt-4o-mini", KEY,
                                   backoff_base=0, _sleep=lambda s: None)
            self.assertEqual(m.call_count, 1)  # no retry on auth

    def test_retry_on_429_then_success(self):
        row, m = self._run([_http_error(429, "rate limit"), _ok_response()])
        self.assertEqual(m.call_count, 2)
        self.assertTrue(row["response_text"])

    def test_timeout_bounded_then_error_no_row(self):
        with mock.patch.object(oa.urllib.request, "urlopen") as m:
            m.side_effect = TimeoutError("timed out")
            with self.assertRaises(oa.EngineError):
                oa.run_once_openai("q", "gpt-4o-mini", KEY, max_retries=3,
                                   backoff_base=0, _sleep=lambda s: None)
            self.assertEqual(m.call_count, 4)  # 1 + 3 bounded retries

    def test_temperature_rejected_is_omitted_and_declared(self):
        err = _http_error(
            400, '{"error":{"message":"temperature is not supported"}}'
        )
        row, m = self._run([err, _ok_response()])
        self.assertEqual(row["temperature"], "omitted (api_rejected)")
        self.assertIn("temperature omitted (api_rejected)",
                      row["param_adaptations"])
        self.assertNotIn("temperature", row["request_payload"])
        self.assertEqual(m.call_count, 2)

    def test_max_tokens_rename_adaptation(self):
        err = _http_error(
            400, '{"error":{"message":"max_tokens is not supported, use '
                 'max_completion_tokens"}}'
        )
        row, _ = self._run([err, _ok_response()])
        self.assertIn("max_completion_tokens", row["request_payload"])
        self.assertNotIn("max_tokens", row["request_payload"])

    def test_malformed_200_is_error_not_row(self):
        class _Bad:
            headers = {}
            def read(self):
                return json.dumps({"choices": []}).encode()
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        with mock.patch.object(oa.urllib.request, "urlopen") as m:
            m.side_effect = [_Bad()]
            with self.assertRaises(oa.EngineError):
                oa.run_once_openai("q", "gpt-4o-mini", KEY,
                                   backoff_base=0, _sleep=lambda s: None)


if __name__ == "__main__":
    unittest.main()
