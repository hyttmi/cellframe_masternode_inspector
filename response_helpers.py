import json
import gzip
from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
from logconfig import logger
from utils import utils
from config import Config

class ResponseHelpers:
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Accept-Encoding, Authorization",
        "Access-Control-Expose-Headers": "Content-Type, Content-Encoding",
    }

    @staticmethod
    def _encode_body(data, gzip_enabled=None):
        gzip_enabled = Config.COMPRESS_RESPONSES

        body = json.dumps(data).encode()
        headers = dict(ResponseHelpers.DEFAULT_HEADERS)

        if gzip_enabled:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        return body, headers

    @staticmethod
    def success(data, code=200, gzip_enabled=None):
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "ok", "data": data},
            gzip_enabled
        )
        logger.debug(f"Response body size: {len(body)} bytes")
        logger.debug(f"Response headers: {headers}")
        return CFSimpleHTTPResponse(body=body, code=code, headers=headers)

    @staticmethod
    def error(message, code=400, gzip_enabled=None):
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "error", "message": message},
            gzip_enabled
        )
        return CFSimpleHTTPResponse(body=body, code=code, headers=headers)

    @staticmethod
    def redirect(url, code=302):
        logger.debug(f"Redirecting to URL: {url}, code: {code}")
        headers = dict(ResponseHelpers.DEFAULT_HEADERS)
        headers["Location"] = url
        return CFSimpleHTTPResponse(body=b"", code=code, headers=headers)

    @staticmethod
    def options():
        headers = dict(ResponseHelpers.DEFAULT_HEADERS)
        headers["Content-Length"] = "0"
        headers["Content-Type"] = "text/plain"
        return CFSimpleHTTPResponse(body=b"", code=204, headers=headers)