from system_requests import system_requests
from utils import utils
from logconfig import logger
from threadpool import run_on_threadpool
from masternode_helpers import masternode_helpers


def get_cache_for_network(network):
    try:
        from cacher import cacher
        if not cacher:
            logger.warning("Cacher instance not initialized yet.")
            return {}
        return cacher.get_cache(network) or {}
    except Exception as e:
        logger.error(f"Error accessing cache for {network}: {e}", exc_info=True)
        return {}


class Actions:
    # -------------------------
    # System actions
    # -------------------------
    SYSTEM_ACTIONS = {
        "current_node_version": lambda: run_on_threadpool(system_requests.get_node_version),
        "external_ip": lambda: run_on_threadpool(system_requests.get_external_ip),
        "hostname": lambda: system_requests._hostname,  # make callable
        "latest_node_version": lambda: run_on_threadpool(utils.get_latest_node_version),
        "node_cpu_usage": lambda: run_on_threadpool(system_requests.get_node_cpu_usage),
        "node_memory_usage": lambda: run_on_threadpool(system_requests.get_node_memory_usage),
        "node_pid": lambda: system_requests._node_pid,  # make also callable
        "node_running_as_service": lambda: system_requests._is_running_as_service,  # make also callable
        "node_uptime": lambda: run_on_threadpool(system_requests.get_node_uptime),
        "system_uptime": lambda: run_on_threadpool(system_requests.get_system_uptime),
    }

    # -------------------------
    # Network actions
    # -------------------------
    NETWORK_ACTIONS = {
        "autocollect_status": lambda network: masternode_helpers.get_autocollect_status(network),
        "network_status": lambda network: masternode_helpers.get_network_status(network),  # fetch live
        "sovereign_reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network].get("sovereign_addr"),
        "reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network]["wallet"],
    }
    try:
        sample_network = next(iter(masternode_helpers._active_networks_config), None) # Let's pick the first network as a sample
        if sample_network:
            sample_cache = get_cache_for_network(sample_network)
            for key in sample_cache.keys():
                NETWORK_ACTIONS[key] = lambda network, k=key: get_cache_for_network(network).get(k)
    except Exception as e:
        logger.error(f"Error while building NETWORK_ACTIONS from cache keys: {e}", exc_info=True)

    @staticmethod
    def _resolve_value(val):
        try:
            return val.result()
        except AttributeError:
            return val
        except Exception as e:
            logger.error(f"Error resolving system action value: {e}", exc_info=True)
            return None

    @staticmethod
    def parse_system_actions(actions_requested):
        result = {}

        if "help" in actions_requested:
            return {"available_system_actions": list(Actions.SYSTEM_ACTIONS.keys())}

        actions_to_process = (
            Actions.SYSTEM_ACTIONS.keys()
            if "all" in actions_requested
            else actions_requested
        )

        for action in actions_to_process:
            if action in Actions.SYSTEM_ACTIONS:
                val = Actions.SYSTEM_ACTIONS[action]()
                result[action] = Actions._resolve_value(val)
            else:
                result[action] = f"unknown system action: {action}"
        return result

    @staticmethod
    def parse_network_actions(networks, network_actions_requested):
        result = {}

        if "help" in network_actions_requested:
            return {"available_network_actions": list(Actions.NETWORK_ACTIONS.keys())}

        for net in networks:
            if net not in masternode_helpers._active_networks_config:
                logger.warning(f"Requested network '{net}' is not in active networks config.")
                result[net] = "unsupported network"
                continue

            net_result = {}

            if "all" in network_actions_requested:
                actions_to_process = list(Actions.NETWORK_ACTIONS.keys())
            else:
                actions_to_process = network_actions_requested

            for action in actions_to_process:
                if action in Actions.NETWORK_ACTIONS:
                    net_result[action] = Actions.NETWORK_ACTIONS[action](net)
                else:
                    net_result[action] = f"unsupported network action: {action}"

            if net_result:
                result[net] = net_result

        return result
