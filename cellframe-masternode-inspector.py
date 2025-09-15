from config import Config
from handlers import request_handler
from threading import Thread
from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from logconfig import logger
from cacher import cacher

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET", "POST"], handler=request_handler)
        logger.info("Registering HTTP server...")
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
        logger.info(f"HTTP server started on /{Config.PLUGIN_URL}")
    except Exception as e:
        logger.error(f"An error occurred in HTTP server: {e}", exc_info=True)

def main():
    try:
        supported_node_versions = Config.SUPPORTED_NODE_VERSIONS
        from system_requests import system_requests
        if system_requests._current_node_version not in supported_node_versions:
            logger.error(f"Unsupported node version: {system_requests._current_node_version}. Supported versions are: {', '.join(supported_node_versions)}")
            return 1
        Thread(target=http_server, daemon=True).start()
        Thread(target=cacher.cache_everything, daemon=True).start()
    except Exception as e:
        logger.error(f"Failed to start HTTP server thread: {e}", exc_info=True)

def init():
    try:
        main()
        return 0
    except Exception as e:
        return 1

def deinit():
    return 0