from system_requests import system_requests
from utils import utils
from logconfig import logger
from threadpool import run_on_threadpool
from masternode_helpers import masternode_helpers
from updater import updater
from cacher import cacher

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
        "plugin_update_available": lambda: updater._update_available,
        "system_uptime": lambda: run_on_threadpool(system_requests.get_system_uptime),
    }

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

        if "update_plugin" in actions_requested:
            if updater._update_available and updater._tarball_url:
                try:
                    updater.download_and_update(updater._tarball_url)
                    return {"update_plugin": "Update initiated, node will be restarted!"}
                except Exception as e:
                    logger.error(f"Error initiating plugin update: {e}", exc_info=True)
                    return {"update_plugin": f"Error initiating update: {e}"}
            else:
                return {"update_plugin": "No update available :("}

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
    def parse_network_actions(networks, requested):
        result = {}

        for net in networks:
            if net not in masternode_helpers._active_networks_config:
                logger.warning(f"Requested network '{net}' is not in active networks config.")
                result[net] = "unsupported network"
                continue

            actions = {
                "autocollect_status": masternode_helpers.get_autocollect_status(net),
                "network_status": masternode_helpers.get_network_status(net),
                "reward_wallet_address": masternode_helpers._active_networks_config[net]["wallet"]
            }

            cache = cacher.get_cache(net)
            if cache:
                for k, v in cache.items():
                    actions[k] = v

            if "help" in requested:
                result[net] = sorted(actions.keys())
                continue

            actions_to_run = actions if "all" in requested else {a: actions[a] for a in requested if a in actions}

            net_result = {}
            for name, fn in actions_to_run.items():
                try:
                    net_result[name] = fn(net) if callable(fn) else fn
                except Exception as e:
                    logger.error(f"Error running action {name} for {net}: {e}", exc_info=True)
                    net_result[name] = None

            for a in requested:
                if a not in actions and a not in ("all", "help"):
                    net_result[a] = f"unsupported network action: {a}"

            result[net] = net_result

        return result
