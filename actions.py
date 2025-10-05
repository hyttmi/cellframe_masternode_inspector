from system_requests import system_requests
from utils import utils
from logconfig import logger
from threadpool import run_on_threadpool
from masternode_helpers import masternode_helpers
from updater import updater


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
        "active_networks": lambda: list(masternode_helpers._active_networks_config.keys()),
        "current_node_version": lambda: run_on_threadpool(system_requests.get_node_version),
        "current_plugin_version": lambda: updater._current_plugin_version,
        "external_ip": lambda: run_on_threadpool(system_requests.get_external_ip),
        "hostname": lambda: system_requests._hostname,
        "latest_node_version": lambda: run_on_threadpool(utils.get_latest_node_version),
        "latest_plugin_version": lambda: updater._latest_plugin_version,
        "node_cpu_usage": lambda: run_on_threadpool(system_requests.get_node_cpu_usage),
        "node_memory_usage": lambda: run_on_threadpool(system_requests.get_node_memory_usage),
        "node_pid": lambda: system_requests._node_pid,
        "node_running_as_service": lambda: system_requests._is_running_as_service,
        "node_uptime": lambda: run_on_threadpool(system_requests.get_node_uptime),
        "system_uptime": lambda: run_on_threadpool(system_requests.get_system_uptime),
    }

    # -------------------------
    # Static network actions
    # -------------------------
    STATIC_NETWORK_ACTIONS = {
        "autocollect_status": lambda network: masternode_helpers.get_autocollect_status(network),
        "network_status": lambda network: masternode_helpers.get_network_status(network),  # live fetch
        "sovereign_reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network].get("sovereign_addr"),
        "reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network]["wallet"],
    }

    @staticmethod
    def _build_network_actions_for(net):
        actions = dict(Actions.STATIC_NETWORK_ACTIONS)

        try:
            cache = get_cache_for_network(net)
            for key in cache.keys():
                actions[key] = lambda network, k=key: get_cache_for_network(network).get(k)
        except Exception as e:
            logger.error(f"Error while building dynamic NETWORK_ACTIONS for {net}: {e}", exc_info=True)

        return actions

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
        if "help" in actions_requested:
            return {"available_system_actions": sorted(Actions.SYSTEM_ACTIONS.keys())}

        result = {}
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
        if "help" in network_actions_requested:
            sample_net = next(iter(networks), None)
            if sample_net:
                available = sorted(Actions._build_network_actions_for(sample_net).keys())
            else:
                available = sorted(Actions.STATIC_NETWORK_ACTIONS.keys())
            return {"available_network_actions": available}

        result = {}
        for net in networks:
            if net not in masternode_helpers._active_networks_config:
                logger.warning(f"Requested network '{net}' is not in active networks config.")
                result[net] = "unsupported network"
                continue

            net_actions = Actions._build_network_actions_for(net)
            net_result = {}

            actions_to_process = (
                list(net_actions.keys())
                if "all" in network_actions_requested
                else network_actions_requested
            )

            for action in actions_to_process:
                if action in net_actions:
                    net_result[action] = net_actions[action](net)
                else:
                    net_result[action] = f"unsupported network action: {action}"

            if net_result:
                result[net] = net_result

        return result
