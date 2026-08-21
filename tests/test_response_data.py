import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from utils.response_data import normalize_response_data


class TestNormalizeResponseData(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_text_stored_as_is(self) -> None:
        result = normalize_response_data(
            "hello world",
            workspace_root=self.workspace,
            task_id=1,
        )
        self.assertEqual(result, "hello world")

    def test_dict_serialized_to_json(self) -> None:
        payload = {"status": "ok", "url": "https://example.com"}
        result = normalize_response_data(
            payload,
            workspace_root=self.workspace,
            task_id=2,
        )
        self.assertEqual(json.loads(result), payload)

    def test_bytes_written_to_file_and_returns_relative_path(self) -> None:
        data = b"\x89PNG\r\n\x1a\nbinary"
        result = normalize_response_data(
            data,
            workspace_root=self.workspace,
            task_id=3,
            content_type="image/png",
        )
        self.assertTrue(result.startswith("task_responses/3_"))
        self.assertTrue(result.endswith(".png"))
        absolute = Path(self.workspace) / result.replace("/", os.sep)
        self.assertTrue(absolute.exists())
        self.assertEqual(absolute.read_bytes(), data)

    def test_requests_response_binary_content_type(self) -> None:
        resp = MagicMock()
        resp.headers = {"Content-Type": "application/octet-stream"}
        resp.content = b"\x00\x01\x02"
        resp.text = "should-not-use"
        result = normalize_response_data(
            resp,
            workspace_root=self.workspace,
            task_id=4,
        )
        self.assertTrue(result.startswith("task_responses/4_"))
        absolute = Path(self.workspace) / result.replace("/", os.sep)
        self.assertEqual(absolute.read_bytes(), b"\x00\x01\x02")

    def test_requests_response_text(self) -> None:
        resp = MagicMock()
        resp.headers = {"Content-Type": "application/json"}
        resp.content = b'{"a":1}'
        resp.text = '{"a":1}'
        result = normalize_response_data(
            resp,
            workspace_root=self.workspace,
            task_id=5,
        )
        self.assertEqual(result, '{"a":1}')

    def test_none_returns_empty(self) -> None:
        result = normalize_response_data(
            None,
            workspace_root=self.workspace,
            task_id=6,
        )
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
