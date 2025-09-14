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
        "hostname": lambda: system_requests._hostname, # make callable
        "latest_node_version": lambda: run_on_threadpool(utils.get_latest_node_version),
        "node_cpu_usage": lambda: run_on_threadpool(system_requests.get_node_cpu_usage),
        "node_memory_usage": lambda: run_on_threadpool(system_requests.get_node_memory_usage),
        "node_pid": lambda: system_requests._node_pid, # make also callable
        "node_running_as_service": lambda: system_requests._is_running_as_service, # make also callable
        "node_uptime": lambda: run_on_threadpool(system_requests.get_node_uptime),
        "system_uptime": lambda: run_on_threadpool(system_requests.get_system_uptime),
    }

    # -------------------------
    # Network actions
    # -------------------------
    NETWORK_ACTIONS = {
        "autocollect_status": lambda network: masternode_helpers.get_autocollect_status(network),
        "block_count": lambda network: get_cache_for_network(network).get("block_count"),
        "cache_last_updated": lambda network: get_cache_for_network(network).get("cache_last_updated"),
        "chain_size": lambda network: get_cache_for_network(network).get("chain_size"),
        "current_block_reward": lambda network: get_cache_for_network(network).get("current_block_reward"),
        "first_signed_blocks_count": lambda network: get_cache_for_network(network).get("first_signed_blocks_count"),
        "first_signed_blocks_daily": lambda network: get_cache_for_network(network).get("first_signed_blocks_daily"),
        "first_signed_blocks_earliest": lambda network: get_cache_for_network(network).get("first_signed_blocks_earliest"),
        "first_signed_blocks_latest": lambda network: get_cache_for_network(network).get("first_signed_blocks_latest"),
        "first_signed_blocks_today_amount": lambda network: get_cache_for_network(network).get("first_signed_blocks_today_amount"),
        "first_signed_blocks_today": lambda network: get_cache_for_network(network).get("first_signed_blocks_today"),
        "first_signed_blocks_yesterday_amount": lambda network: get_cache_for_network(network).get("first_signed_blocks_yesterday_amount"),
        "first_signed_blocks_yesterday": lambda network: get_cache_for_network(network).get("first_signed_blocks_yesterday"),
        "network_status": lambda network: masternode_helpers.get_network_status(network), # fetch this live, it's useful to know if node is synced
        "signed_blocks_count": lambda network: get_cache_for_network(network).get("signed_blocks_count"),
        "signed_blocks_daily": lambda network: get_cache_for_network(network).get("signed_blocks_daily"),
        "signed_blocks_earliest": lambda network: get_cache_for_network(network).get("signed_blocks_earliest"),
        "signed_blocks_latest": lambda network: get_cache_for_network(network).get("signed_blocks_latest"),
        "signed_blocks_today_amount": lambda network: get_cache_for_network(network).get("signed_blocks_today_amount"),
        "signed_blocks_today": lambda network: get_cache_for_network(network).get("signed_blocks_today"),
        "signed_blocks_yesterday_amount": lambda network: get_cache_for_network(network).get("signed_blocks_yesterday_amount"),
        "signed_blocks_yesterday": lambda network: get_cache_for_network(network).get("signed_blocks_yesterday"),
        "sovereign_reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network].get('sovereign_addr'),
        "sovereign_wallet_balance": lambda network: get_cache_for_network(network).get("sovereign_wallet_balance"),
        "sovereign_wallet_earliest_reward": lambda network: get_cache_for_network(network).get("sovereign_wallet_earliest_reward"),
        "sovereign_wallet_latest_reward": lambda network: get_cache_for_network(network).get("sovereign_wallet_latest_reward"),
        "sovereign_wallet_daily_rewards": lambda network: get_cache_for_network(network).get("sovereign_wallet_daily_rewards"),
        "sovereign_wallet_biggest_reward": lambda network: get_cache_for_network(network).get("sovereign_wallet_biggest_reward"),
        "sovereign_wallet_smallest_reward": lambda network: get_cache_for_network(network).get("sovereign_wallet_smallest_reward"),
        "reward_wallet_address": lambda network: masternode_helpers._active_networks_config[network]['wallet'],
        "reward_wallet_balance": lambda network: get_cache_for_network(network).get("wallet_balance"),
        "reward_wallet_earliest_reward": lambda network: get_cache_for_network(network).get("wallet_earliest_reward"),
        "reward_wallet_latest_reward": lambda network: get_cache_for_network(network).get("wallet_latest_reward"),
        "reward_wallet_daily_rewards": lambda network: get_cache_for_network(network).get("wallet_daily_rewards"),
        "reward_wallet_biggest_reward": lambda network: get_cache_for_network(network).get("wallet_biggest_reward"),
        "reward_wallet_smallest_reward": lambda network: get_cache_for_network(network).get("wallet_smallest_reward"),
        "token_price": lambda network: get_cache_for_network(network).get("token_price"),
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
        result = {}

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
