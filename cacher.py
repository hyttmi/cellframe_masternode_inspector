from logconfig import logger
from masternode_helpers import masternode_helpers
from threadpool import run_on_cacherpool
from utils import utils
from config import Config
from parsers import Parsers as P
import time


class Cacher:
    def __init__(self):
        logger.debug("Initializing Cacher...")
        self.cache = {}
        for network in masternode_helpers._active_networks_config:
                old_cache = utils.load_json_from_file(f"{network}_cache.json")
                if old_cache:
                    self.cache[network] = old_cache
                    logger.info(f"Loaded old cache for {network} from disk")
                else:
                    logger.info(f"No old cache file found for {network}, starting fresh")

    def cache_everything(self):
        try:
            if not masternode_helpers._active_networks_config:
                logger.warning("No active networks configured, caching will not start")
                return
            while True:
                for network in masternode_helpers._active_networks_config:
                    start_time = time.time()

                    # Wait until node is synced, there's no point in caching if not synced
                    if not masternode_helpers.get_network_status(network).get("synced"):
                        logger.info(f"{network} not synced, skipping this cycle")
                        continue

                    current_blocks_on_network = masternode_helpers.get_block_count(network)
                    old_blocks_on_network = self.cache.get(network, {}).get("block_count", 0)

                    block_diff = current_blocks_on_network - old_blocks_on_network

                    if block_diff < Config.BLOCK_COUNT_THRESHOLD:
                        logger.info(
                            f"{network}: Block count only increased by {block_diff} "
                            f"(old={old_blocks_on_network}, new={current_blocks_on_network}), "
                            f"skipping this cycle"
                        )
                        continue

                    logger.info(f"Caching data for {network}...")

                    # Get sovereign address from config or fetch it
                    sovereign_addr = masternode_helpers._active_networks_config[network].get("sovereign_addr")
                    if not sovereign_addr:
                        sovereign_addr = masternode_helpers.get_sovereign_addr(network)

                    # Async fetch all data
                    futures = {
                        "block_count": run_on_cacherpool(masternode_helpers.get_block_count, network),
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
                    sovereign_tx_total_rewards = sovereign_tx_latest_reward = sovereign_tx_earliest_reward = sovereign_tx_daily_rewards = None
                    sovereign_tx_smallest_reward = sovereign_tx_biggest_reward = sovereign_tx_daily_sums = None

                    if tx_history:
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
                        "block_count": futures["block_count"].result(),
                        "chain_size": futures["chain_size"].result(),
                        "current_block_reward": futures["current_block_reward"].result(),
                        "first_signed_blocks_count": fsb_total,
                        "first_signed_blocks_daily_amount": fsb_daily_amount,
                        "first_signed_blocks_daily": fsb_daily,
                        "first_signed_blocks_daily_sums": fsb_daily_sums,
                        "first_signed_blocks_earliest": fsb_earliest,
                        "first_signed_blocks_full": first_signed_blocks,
                        "first_signed_blocks_latest": fsb_latest,
                        "first_signed_blocks_today_amount": fsb_today_amount,
                        "first_signed_blocks_today": fsb_today,
                        "first_signed_blocks_yesterday_amount": fsb_yesterday_amount,
                        "first_signed_blocks_yesterday": fsb_yesterday,
                        "signed_blocks_count": sb_total,
                        "signed_blocks_daily_amount": sb_daily_amount,
                        "signed_blocks_daily": sb_daily,
                        "signed_blocks_daily_sums": sb_daily_sums,
                        "signed_blocks_earliest": sb_earliest,
                        "signed_blocks_full": signed_blocks,
                        "signed_blocks_latest": sb_latest,
                        "signed_blocks_today_amount": sb_today_amount,
                        "signed_blocks_today": sb_today,
                        "signed_blocks_yesterday_amount": sb_yesterday_amount,
                        "signed_blocks_yesterday": sb_yesterday,
                        "token_price": futures["token_price"].result(),
                        "wallet_balance": futures["wallet_balance"].result(),
                        "wallet_biggest_reward": tx_biggest_reward,
                        "wallet_daily_rewards": tx_daily_rewards,
                        "wallet_daily_sums": tx_daily_sums,
                        "wallet_earliest_reward": tx_earliest_reward,
                        "wallet_latest_reward": tx_latest_reward,
                        "wallet_today_rewards": tx_today_rewards,
                        "wallet_yesterday_rewards": tx_yesterday_rewards,
                        "wallet_smallest_reward": tx_smallest_reward,
                        "wallet_total_rewards": tx_total_rewards,
                    }

                    if sovereign_tx_history:
                        new_data.update(
                            {
                                "sovereign_wallet_balance": futures["sovereign_wallet_balance"].result(),
                                "sovereign_wallet_biggest_reward": sovereign_tx_biggest_reward,
                                "sovereign_wallet_daily_rewards": sovereign_tx_daily_rewards,
                                "sovereign_wallet_daily_sums": sovereign_tx_daily_sums,
                                "sovereign_wallet_earliest_reward": sovereign_tx_earliest_reward,
                                "sovereign_wallet_latest_reward": sovereign_tx_latest_reward,
                                "sovereign_wallet_today_rewards": sovereign_tx_today_rewards,
                                "sovereign_wallet_yesterday_rewards": sovereign_tx_yesterday_rewards,
                                "sovereign_wallet_smallest_reward": sovereign_tx_smallest_reward,
                                "sovereign_wallet_total_rewards": sovereign_tx_total_rewards,
                            }
                        )

                    new_data["cache_last_updated"] = utils.now_iso()

                    self.cache[network] = new_data
                    utils.save_json_to_file(new_data, f"{network}_cache.json")

                    logger.debug(
                        f"Cached data for {network} in {time.time() - start_time:.2f} seconds "
                        f"(memory + disk updated)"
                    )
                time.sleep(60)
                # And boom! We have a cache!
        except Exception as e:
            logger.error(f"An error occurred in the caching loop: {e}", exc_info=True)

    def get_cache(self, network):
        return self.cache.get(network, {})


cacher = Cacher()
