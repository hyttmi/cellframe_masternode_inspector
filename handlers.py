from logconfig import logger
from urllib.parse import parse_qs
from utils import utils
from response_helpers import ResponseHelpers as RH
from actions import Actions

def request_handler(request):
    try:
        method = request.method
        url = request.url
        headers = request.headers
        query = request.query
        client_ip = request.client_address
        body = request.body

        logger.info(
            f"Received {method} request for {url} with headers: {headers}, "
            f"query: {query if query else 'N/A'}, "
            f"body: {body if body else 'N/A'}, "
            f"client IP: {client_ip if client_ip else 'N/A'}"
        )

        if method not in ["GET", "POST"]:
            logger.error(f"Method {method} not allowed for {url}")
            return RH.error("Method not allowed", code=405)

        return GET_request_handler(headers, query)

    except Exception as e:
        logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        return RH.error("Internal server error", code=500)

def GET_request_handler(headers=None, query=None):
    if not query:
        return RH.error("Missing query", code=400)

    parsed = parse_qs(query)
    logger.debug(f"Parsed query parameters: {parsed}")

    token = parsed.get("access_token", [None])[0] or headers.get("X-API-Key")
    if not token:
        return RH.error("Access token is required", code=400)
    if token != utils._generate_random_token:
        logger.warning(f"Invalid access token attempt: {token}")
        return RH.error("Invalid access token", code=403)
    logger.info("Access token validated successfully!")

    actions_requested = parsed.get("action", [])
    networks = parsed.get("networks", [])
    network_actions_requested = parsed.get("network_action", [])

    if actions_requested:
        actions_requested = actions_requested[0].split(",")
        logger.debug(f"Requested system actions: {actions_requested}")

    if networks:
        networks = networks[0].split(",")
        logger.debug(f"Requested networks: {networks}")

    if network_actions_requested:
        network_actions_requested = network_actions_requested[0].split(",")
        logger.debug(f"Requested network actions: {network_actions_requested}")

    result = {}
    if actions_requested:
        result.update(Actions.parse_system_actions(actions_requested))
    if networks and network_actions_requested:
        result.update(Actions.parse_network_actions(networks, network_actions_requested))

    return RH.success(result)
