import unittest
from unittest.mock import Mock, patch

import prisma_client


class PrismaClientTests(unittest.TestCase):
    def test_v25_request_uses_documented_multipart_fields(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "success": True,
            "transcript": "one two three",
            "request_id": "request-1",
        }
        with (
            patch.object(prisma_client, "_api_key", return_value="test-key"),
            patch.object(prisma_client.requests, "post", return_value=response) as post,
        ):
            result = prisma_client.transcribe(
                b"wav-data", "recording.wav", "en-IN", "v25"
            )

        self.assertEqual(result["transcript"], "one two three")
        args, kwargs = post.call_args
        self.assertEqual(args, (prisma_client.API_URL,))
        self.assertEqual(kwargs["headers"], {"X-API-Key-ID": "test-key"})
        self.assertEqual(
            kwargs["files"]["audio_file"],
            ("recording.wav", b"wav-data", "audio/wav"),
        )
        self.assertEqual(
            kwargs["data"], {"language_code": "en-IN", "format": "transcribe"}
        )
        self.assertEqual(kwargs["timeout"], 60)

    def test_v30_selects_model_and_rejects_unsuccessful_response(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "success": True,
            "transcript": "123",
        }
        with (
            patch.object(prisma_client, "_api_key", return_value="test-key"),
            patch.object(prisma_client.requests, "post", return_value=response) as post,
        ):
            prisma_client.transcribe(b"wav-data", "recording.wav", "kn-IN", "v30")
        self.assertEqual(
            post.call_args.kwargs["data"],
            {
                "language_code": "kn-IN",
                "format": "transcribe",
                "model": "prisma-v3.0",
            },
        )

        response.status_code = 429
        response.json.return_value = {
            "error": {"type": "RATE_LIMIT", "message": "Too many requests."}
        }
        with self.assertRaisesRegex(prisma_client.PrismaError, "HTTP 429"):
            prisma_client.validate_response(response)

    def test_invalid_inputs_do_not_make_requests(self):
        with patch.object(prisma_client.requests, "post") as post:
            with self.assertRaises(ValueError):
                prisma_client.transcribe(b"", "recording.wav", "en-IN", "v25")
            with self.assertRaises(ValueError):
                prisma_client.transcribe(b"audio", "recording.wav", "en-IN", "other")
            with self.assertRaises(ValueError):
                prisma_client.transcribe(b"audio", "recording.wav", "xx-XX", "v25")
        post.assert_not_called()

    def test_network_error_is_not_retried(self):
        import requests

        with (
            patch.object(prisma_client, "_api_key", return_value="test-key"),
            patch.object(
                prisma_client.requests,
                "post",
                side_effect=requests.Timeout("timed out"),
            ) as post,
        ):
            with self.assertRaisesRegex(prisma_client.PrismaError, "not retried"):
                prisma_client.transcribe(b"wav-data", "recording.wav", "en-IN", "v25")
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
