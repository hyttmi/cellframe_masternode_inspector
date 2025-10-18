from logconfig import logger
from masternode_helpers import masternode_helpers
from threadpool import run_on_cacherpool
from utils import utils
from config import Config
from parsers import Parsers as P
from datetime import datetime
import time

class Cacher:
    def __init__(self):
        logger.debug("Initializing Cacher...")
        self.cache = {}
        for network in masternode_helpers._active_networks_config:
                old_cache = utils.load_json_from_file(f".{network}_cache.json") # Hidden file
                if old_cache:
                    self.cache[network] = old_cache
                    logger.info(f"Loaded old cache for {network} from disk")
                else:
                    logger.info(f"No old cache file found for {network}, starting fresh")
        self.rewards = {}
        self.sovereign_rewards = {}

    def cache_everything(self):
        try:
            if not masternode_helpers._active_networks_config:
                logger.warning("No active networks configured, caching will not start")
                return
            while True:
                for network in masternode_helpers._active_networks_config:
                    start_time = time.time()

                    # Wait until node is synced, there's no point in caching if node is not synced
                    if not masternode_helpers.get_network_status(network).get("synced"):
                        logger.info(f"{network} not synced, skipping this cycle")
                        continue

                    current_blocks_on_network = masternode_helpers.get_block_count(network)
                    old_blocks_on_network = self.cache.get(network, {}).get("block_count", 0)

                    block_diff = current_blocks_on_network - old_blocks_on_network

                    last_updated_iso = self.cache.get(network, {}).get("cache_last_updated", None)
                    force_refresh = False

                    if last_updated_iso:
                        try:
                            last_updated_dt = datetime.fromisoformat(last_updated_iso)
                            elapsed = time.time() - last_updated_dt.timestamp()
                            if elapsed >= Config.FORCE_CACHE_REFRESH_INTERVAL:
                                force_refresh = True
                        except Exception:
                            pass

                    if block_diff < Config.BLOCK_COUNT_THRESHOLD and not force_refresh:
                        logger.info(
                            f"{network}: Block count diff {block_diff} < {Config.BLOCK_COUNT_THRESHOLD} "
                            f"and last cache update {elapsed:.0f}s ago < {Config.FORCE_CACHE_REFRESH_INTERVAL}s — skipping this cycle."
                        )
                        continue

                    if force_refresh:
                        if block_diff <= 0:
                            logger.info(f"Force refresh was triggered, but block diff between cache "
                                        f"and network is {block_diff}, skipping cache refresh.")
                            continue
                        else:
                            logger.info(
                                f"{network}: Forcing cache refresh (last updated {elapsed:.0f}s ago, "
                                f"interval {Config.FORCE_CACHE_REFRESH_INTERVAL}s)"
                            )


                    logger.info(f"Caching data for {network}...")

                    node_info = masternode_helpers.get_node_info(network) or {}
                    sovereign_addr = node_info.get("sovereign_reward_wallet_address", None)

                    # Async fetch all raw data first
                    futures = {
                        "block_count_today": run_on_cacherpool(masternode_helpers.get_blocks_on_network_today, network),
                        "first_signed_blocks_raw": run_on_cacherpool(masternode_helpers.get_signed_blocks, network, first_signed=True),
                        "signed_blocks_raw": run_on_cacherpool(masternode_helpers.get_signed_blocks, network),
                        "tx_history_raw": run_on_cacherpool(
                            masternode_helpers.get_tx_history,
                            network,
                            masternode_helpers._active_networks_config[network]["wallet"],
                        ),
                        "current_block_reward": run_on_cacherpool(masternode_helpers.get_current_block_reward, network),
                        "chain_size": run_on_cacherpool(masternode_helpers.get_chain_size, network),
                        "token_price": run_on_cacherpool(masternode_helpers.get_token_price, network),
                        "wallet_balance": run_on_cacherpool(masternode_helpers.get_wallet_balance, network, masternode_helpers._active_networks_config[network]["wallet"]),
                    }

                    if sovereign_addr:
                        futures["sovereign_tx_history_raw"] = run_on_cacherpool(
                            masternode_helpers.get_tx_history, network, sovereign_addr
                        )
                        futures["sovereign_wallet_balance"] = run_on_cacherpool(
                            masternode_helpers.get_wallet_balance, network, sovereign_addr
                        )

                    # ----------------------------------------------------------------
                    # Pre-parse only if we have data
                    # ----------------------------------------------------------------
                    first_signed_blocks = []
                    signed_blocks = []
                    tx_history = []
                    sovereign_tx_history = None

                    raw_fsb = futures["first_signed_blocks_raw"].result() if futures["first_signed_blocks_raw"] else None
                    if raw_fsb:
                        first_signed_blocks = P.replace_timestamps(raw_fsb, blocks=True)

                    raw_sb = futures["signed_blocks_raw"].result() if futures["signed_blocks_raw"] else None
                    if raw_sb:
                        signed_blocks = P.replace_timestamps(raw_sb, blocks=True)

                    raw_tx = futures["tx_history_raw"].result() if futures["tx_history_raw"] else None
                    if raw_tx:
                        tx_history = P.replace_timestamps(raw_tx)

                    if "sovereign_tx_history_raw" in futures:
                        raw_sovereign_tx = futures["sovereign_tx_history_raw"].result()
                        if raw_sovereign_tx:
                            sovereign_tx_history = P.replace_timestamps(raw_sovereign_tx)

                    # ----------------------------------------------------------------
                    # Blocks
                    # ----------------------------------------------------------------
                    fsb_total = fsb_latest = fsb_earliest = None
                    fsb_today = fsb_today_amount = None
                    fsb_yesterday = fsb_yesterday_amount = None
                    fsb_daily = fsb_daily_amount = None
                    fsb_daily_sums = None

                    if first_signed_blocks:
                        fsb_total = run_on_cacherpool(P.parse_blocks_data, first_signed_blocks, option="total").result()
                        fsb_latest = run_on_cacherpool(P.parse_blocks_data, first_signed_blocks, option="latest").result()
                        fsb_earliest = run_on_cacherpool(P.parse_blocks_data, first_signed_blocks, option="earliest").result()
                        fsb_today, fsb_today_amount = run_on_cacherpool(
                            P.parse_blocks_data, first_signed_blocks, option="today"
                        ).result()
                        fsb_yesterday, fsb_yesterday_amount = run_on_cacherpool(
                            P.parse_blocks_data, first_signed_blocks, option="yesterday"
                        ).result()
                        fsb_daily, fsb_daily_amount = run_on_cacherpool(
                            P.parse_blocks_data, first_signed_blocks, option="daily"
                        ).result()
                        fsb_daily_sums = run_on_cacherpool(
                            P.parse_blocks_data, first_signed_blocks, option="daily_sums"
                        ).result()

                    sb_total = sb_latest = sb_earliest = None
                    sb_today = sb_today_amount = None
                    sb_yesterday = sb_yesterday_amount = None
                    sb_daily = sb_daily_amount = None
                    sb_daily_sums = None

                    if signed_blocks:
                        sb_total = run_on_cacherpool(P.parse_blocks_data, signed_blocks, option="total").result()
                        sb_latest = run_on_cacherpool(P.parse_blocks_data, signed_blocks, option="latest").result()
                        sb_earliest = run_on_cacherpool(P.parse_blocks_data, signed_blocks, option="earliest").result()
                        sb_today, sb_today_amount = run_on_cacherpool(
                            P.parse_blocks_data, signed_blocks, option="today"
                        ).result()
                        sb_yesterday, sb_yesterday_amount = run_on_cacherpool(
                            P.parse_blocks_data, signed_blocks, option="yesterday"
                        ).result()
                        sb_daily, sb_daily_amount = run_on_cacherpool(
                            P.parse_blocks_data, signed_blocks, option="daily"
                        ).result()
                        sb_daily_sums = run_on_cacherpool(
                            P.parse_blocks_data, signed_blocks, option="daily_sums"
                        ).result()

                    # ----------------------------------------------------------------
                    # Rewards
                    # ----------------------------------------------------------------
                    tx_total_rewards = tx_latest_reward = tx_earliest_reward = None
                    tx_daily_rewards = tx_smallest_reward = tx_biggest_reward = tx_daily_sums = None
                    tx_today_rewards = tx_yesterday_rewards = None
                    sovereign_tx_total_rewards = sovereign_tx_latest_reward = sovereign_tx_earliest_reward = sovereign_tx_daily_rewards = None
                    sovereign_tx_smallest_reward = sovereign_tx_biggest_reward = sovereign_tx_daily_sums = None
                    sovereign_tx_today_rewards = sovereign_tx_yesterday_rewards = None

                    if tx_history:
                        self.rewards[network] = tx_history
                        tx_total_rewards = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="total_rewards"
                        ).result()
                        tx_latest_reward = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="latest_reward"
                        ).result()
                        tx_earliest_reward = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="earliest_reward"
                        ).result()
                        tx_daily_rewards = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="daily"
                        ).result()
                        tx_biggest_reward = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="biggest"
                        ).result()
                        tx_smallest_reward = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="smallest"
                        ).result()
                        tx_daily_sums = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="daily_sums"
                        ).result()
                        tx_today_rewards = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="today"
                        ).result()
                        tx_yesterday_rewards = run_on_cacherpool(
                            P.parse_tx_data, tx_history, option="yesterday"
                        ).result()

                    if sovereign_tx_history:
                        self.sovereign_rewards[network] = sovereign_tx_history
                        sovereign_tx_total_rewards = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="total_rewards"
                        ).result()
                        sovereign_tx_latest_reward = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="latest_reward"
                        ).result()
                        sovereign_tx_earliest_reward = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="earliest_reward"
                        ).result()
                        sovereign_tx_daily_rewards = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="daily"
                        ).result()
                        sovereign_tx_smallest_reward = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="smallest"
                        ).result()
                        sovereign_tx_biggest_reward = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="biggest"
                        ).result()
                        sovereign_tx_daily_sums = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="daily_sums"
                        ).result()
                        sovereign_tx_today_rewards = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="today"
                        ).result()
                        sovereign_tx_yesterday_rewards = run_on_cacherpool(
                            P.parse_tx_data, sovereign_tx_history, option="yesterday"
                        ).result()

                    # ----------------------------------------------------------------
                    # Build cache
                    # ----------------------------------------------------------------
                    new_data = {
                        "block_count_today": futures["block_count_today"].result(),
                        "block_count": current_blocks_on_network,
                        "chain_size": futures["chain_size"].result(),
                        "current_block_reward": futures["current_block_reward"].result(),
                        "days_cutoff": Config.DAYS_CUTOFF, # We need to know this later
                        "first_signed_blocks_count": fsb_total,
                        "first_signed_blocks_daily_amount": fsb_daily_amount,
                        "first_signed_blocks_daily": fsb_daily,
                        "first_signed_blocks_all_sums_daily": fsb_daily_sums,
                        "first_signed_blocks_earliest": fsb_earliest,
                        "first_signed_blocks_latest": fsb_latest,
                        "first_signed_blocks_today_amount": fsb_today_amount,
                        "first_signed_blocks_today": fsb_today,
                        "first_signed_blocks_yesterday_amount": fsb_yesterday_amount,
                        "first_signed_blocks_yesterday": fsb_yesterday,
                        "native_ticker": masternode_helpers._active_networks_config[network].get('native_ticker'),
                        "signed_blocks_count": sb_total,
                        "signed_blocks_daily_amount": sb_daily_amount,
                        "signed_blocks_daily": sb_daily,
                        "signed_blocks_all_sums_daily": sb_daily_sums,
                        "signed_blocks_earliest": sb_earliest,
                        "signed_blocks_latest": sb_latest,
                        "signed_blocks_today_amount": sb_today_amount,
                        "signed_blocks_today": sb_today,
                        "signed_blocks_yesterday_amount": sb_yesterday_amount,
                        "signed_blocks_yesterday": sb_yesterday,
                        "token_price": futures["token_price"].result(),
                        "reward_wallet_balance": futures["wallet_balance"].result(),
                        "reward_wallet_biggest_reward": tx_biggest_reward,
                        "reward_wallet_daily_rewards": tx_daily_rewards,
                        "reward_wallet_all_sums_daily": tx_daily_sums,
                        "reward_wallet_earliest_reward": tx_earliest_reward,
                        "reward_wallet_latest_reward": tx_latest_reward,
                        "reward_wallet_today_rewards": tx_today_rewards,
                        "reward_wallet_yesterday_rewards": tx_yesterday_rewards,
                        "reward_wallet_smallest_reward": tx_smallest_reward,
                        "reward_wallet_total_rewards": tx_total_rewards,
                    }

                    if sovereign_tx_history:
                        new_data.update(
                            {
                                "sovereign_wallet_balance": futures["sovereign_wallet_balance"].result(),
                                "sovereign_wallet_biggest_reward": sovereign_tx_biggest_reward,
                                "sovereign_wallet_daily_rewards": sovereign_tx_daily_rewards,
                                "sovereign_wallet_all_sums_daily": sovereign_tx_daily_sums,
                                "sovereign_wallet_earliest_reward": sovereign_tx_earliest_reward,
                                "sovereign_wallet_latest_reward": sovereign_tx_latest_reward,
                                "sovereign_wallet_today_rewards": sovereign_tx_today_rewards,
                                "sovereign_wallet_yesterday_rewards": sovereign_tx_yesterday_rewards,
                                "sovereign_wallet_smallest_reward": sovereign_tx_smallest_reward,
                                "sovereign_wallet_total_rewards": sovereign_tx_total_rewards,
                            }
                        )

                    new_data["cache_last_updated"] = utils.now_iso()

                    if node_info:
                        new_data.update(node_info)
                    self.cache[network] = new_data
                    utils.save_json_to_file(new_data, f".{network}_cache.json") # Hidden file

                    logger.info(
                        f"Cached data for {network} in {time.time() - start_time:.2f} seconds "
                        f"(memory + disk updated)"
                    )
                time.sleep(10) # Magic number 10 might be just enough
                # And boom! We have a cache!
        except Exception as e:
            logger.error(f"An error occurred in the caching loop: {e}", exc_info=True)

    def get_cache(self, network):
        return self.cache.get(network, {})

cacher = Cacher()
