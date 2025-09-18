import json
from pycfhelpers.node.http.simple import CFSimpleHTTPResponse
from logconfig import logger
import json
import gzip
from utils import utils
from config import Config

class ResponseHelpers:
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST",
        "Access-Control-Allow-Headers": "Content-Type, Accept-Encoding",
    }

    @staticmethod
    def _encode_body(data, gzip_enabled=Config.GZIP_RESPONSES):
        body = json.dumps(data).encode()
        headers = dict(ResponseHelpers.DEFAULT_HEADERS)
        if gzip_enabled:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"
        return body, headers

    @staticmethod
    def success(data, code=200, gzip_enabled=False):
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "ok", "data": data}, gzip_enabled
        )
        logger.debug(f"Response body size: {len(body)} bytes")
        logger.debug(f"Response headers: {headers}")
        return CFSimpleHTTPResponse(body=body, code=code, headers=headers)

    @staticmethod
    def error(message, code=400, gzip_enabled=False):
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "error", "message": message}, gzip_enabled
        )
        return CFSimpleHTTPResponse(body=body, code=code, headers=headers)

    @staticmethod
    def redirect(url, code=302):
        logger.debug(f"Redirecting to URL: {url}, code: {code}")
        return CFSimpleHTTPResponse(
            body=b"",
            code=code,
            headers={**ResponseHelpers.DEFAULT_HEADERS, "Location": url},
        )