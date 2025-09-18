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
    def _encode_body(data, gzip_enabled=False):
        body = json.dumps(data).encode()
        headers = dict(ResponseHelpers.DEFAULT_HEADERS)
        if gzip_enabled:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"
        return body, headers

    @staticmethod
    def success(data, code=200, gzip_enabled=False):
        logger.debug(f"Success response with data: {data}")
        logger.debug(f"Gzip enabled: {gzip_enabled}, Config.GZIP_RESPONSES: {Config.GZIP_RESPONSES}")
        logger.debug(f"ResponseHelpers.DEFAULT_HEADERS: {ResponseHelpers.DEFAULT_HEADERS}")
        logger.debug(f"Final headers before response: {headers}")
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "ok", "data": data}, gzip_enabled if Config.GZIP_RESPONSES else False
        )
        return CFSimpleHTTPResponse(body=body, code=code, headers=headers)

    @staticmethod
    def error(message, code=400, gzip_enabled=False):
        body, headers = ResponseHelpers._encode_body(
            {"request_timestamp": utils.now_iso(), "status": "error", "message": message}, gzip_enabled if Config.GZIP_RESPONSES else False
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