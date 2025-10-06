from config import Config
from handlers import request_handler
from threading import Thread
from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from logconfig import logger
from cacher import cacher
from masternode_helpers import masternode_helpers
from updater import updater
from packaging import version

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET", "POST", "OPTIONS"], handler=request_handler)
        logger.info("Registering HTTP server...")
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
        logger.info(f"HTTP server started on /{Config.PLUGIN_URL}")
    except Exception as e:
        logger.error(f"An error occurred in HTTP server: {e}", exc_info=True)

def main():
    from system_requests import system_requests
    if version.parse(system_requests._current_node_version) < version.parse(Config.MIN_NODE_VERSION):
        logger.error(f"Unsupported node version: {system_requests._current_node_version}. Minimum supported version is: {Config.MIN_NODE_VERSION}")
        raise Exception("Unsupported node version")
    if system_requests._current_platform not in Config.SUPPORTED_PLATFORMS:
        logger.error(
            f"Unsupported platform: {system_requests._current_platform}. "
            f"Supported platforms are: {', '.join(Config.SUPPORTED_PLATFORMS)}"
        )
        raise Exception("Unsupported platform")
    if not masternode_helpers._active_networks_config:
        logger.warning("No active masternode configuration found, this plugin will not function on this node!")
        raise Exception("No active masternode configuration found")
    Thread(target=cacher.cache_everything, daemon=True).start()
    Thread(target=http_server, daemon=True).start()
    Thread(target=updater.run, daemon=True).start()
    return 0

def init():
    try:
        return main()
    except Exception as e:
        logger.error(f"Init failed: {e}", exc_info=True)
        return 1

def deinit():
    return 0