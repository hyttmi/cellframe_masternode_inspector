from logconfig import logger
from masternode_helpers import masternode_helpers
from threadpool import run_on_threadpool
from utils import utils
from config import Config
from parsers import Parsers as P
from pycfhelpers.node.gdb import CFGDBGroup
from datetime import datetime
import jsonlib
import time

GDB_GROUP = "local.mninspectorcache"

class Cacher:
    def __init__(self):
        logger.debug("Initializing Cacher...")
        self.cache = {}
        self._gdb = CFGDBGroup(GDB_GROUP)
        for network in masternode_helpers._active_networks_config:
                old_cache = self._gdb_load(network)
                if old_cache:
                    self.cache[network] = old_cache
                    logger.info(f"Loaded cache for {network} from GDB")
                    logger.info(f"Cache was updated at {old_cache.get('cache_last_updated', 'unknown time')}")
                else:
                    logger.info(f"No cache found for {network} in GDB, starting fresh")
        self.rewards = {}
        self.sovereign_rewards = {}

    def _gdb_save(self, network, data):
        try:
            self._gdb[network] = jsonlib.dumps_bytes(data)
        except Exception as e:
            logger.error(f"Failed to save cache to GDB for {network}: {e}", exc_info=True)

    def _gdb_load(self, network):
        try:
            raw = self._gdb.get(network)
            if raw:
                return jsonlib.loads(raw)
        except Exception as e:
            logger.error(f"Failed to load cache from GDB for {network}: {e}", exc_info=True)
        return None

    def _get_incremental_date(self, network, cache_key):
        blocks = self.cache.get(network, {}).get(cache_key)
        if blocks and len(blocks) > 0:
            latest_ts = blocks[0].get("ts_create")
            if latest_ts:
                logger.debug(f"Latest timestamp for {cache_key} on {network} is {latest_ts}")
                try:
                    return datetime.fromisoformat(latest_ts).strftime("%y%m%d")
                except Exception:
                    pass
        logger.debug(f"No valid latest timestamp found for {cache_key} on {network}, returning None for incremental date")
        return None

    @staticmethod
    def _merge_blocks(existing, new_blocks):
        if not existing or not isinstance(existing, list):
            return new_blocks
        seen = {b["hash"] for b in existing if isinstance(b, dict) and "hash" in b}
        if not seen:
            return new_blocks
        merged = list(existing)
        added = 0
        for b in new_blocks:
            h = b.get("hash")
            if h and h not in seen:
                merged.append(b)
                seen.add(h)
                added += 1
        if added:
            merged.sort(key=lambda b: b.get("ts_create", ""), reverse=True)
            logger.info(f"Merged {added} new blocks with {len(existing)} cached blocks")
        return merged

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
                                f"interval {Config.FORCE_CACHE_REFRESH_INTERVAL}s, block diff is {block_diff})"
                            )


                    logger.info(f"Caching data for {network}...")

                    node_info = masternode_helpers.get_node_info(network) or {}
                    sovereign_addr = node_info.get("sovereign_reward_wallet_address", None)

                    signed_from_date = self._get_incremental_date(network, "signed_blocks_daily")
                    fsb_from_date = self._get_incremental_date(network, "first_signed_blocks_daily")

                    # Async fetch all raw data first
                    futures = {
                        "block_count_today": run_on_threadpool(masternode_helpers.get_blocks_on_network_today, network),
                        "first_signed_blocks_raw": run_on_threadpool(masternode_helpers.get_signed_blocks, network, first_signed=True, from_date=fsb_from_date),
                        "signed_blocks_raw": run_on_threadpool(masternode_helpers.get_signed_blocks, network, from_date=signed_from_date),
                        "tx_history_raw": run_on_threadpool(
                            masternode_helpers.get_tx_history,
                            network,
                            masternode_helpers._active_networks_config[network]["wallet"],
                        ),
                        "current_block_reward": run_on_threadpool(masternode_helpers.get_current_block_reward, network),
                        "chain_size": run_on_threadpool(masternode_helpers.get_chain_size, network),
                    }

                    if sovereign_addr:
                        futures["sovereign_tx_history_raw"] = run_on_threadpool(
                            masternode_helpers.get_tx_history, network, sovereign_addr
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
                        new_fsb = P.replace_timestamps(raw_fsb, blocks=True)
                        existing_fsb = self.cache.get(network, {}).get("first_signed_blocks_daily") or []
                        first_signed_blocks = self._merge_blocks(existing_fsb, new_fsb) if fsb_from_date else new_fsb

                    raw_sb = futures["signed_blocks_raw"].result() if futures["signed_blocks_raw"] else None
                    if raw_sb:
                        new_sb = P.replace_timestamps(raw_sb, blocks=True)
                        existing_sb = self.cache.get(network, {}).get("signed_blocks_daily") or []
                        signed_blocks = self._merge_blocks(existing_sb, new_sb) if signed_from_date else new_sb

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
                        fsb_snapshot = run_on_threadpool(P.parse_blocks_data, first_signed_blocks).result()
                        fsb_total = fsb_snapshot.get("total")
                        fsb_latest = fsb_snapshot.get("latest")
                        fsb_earliest = fsb_snapshot.get("earliest")
                        fsb_today = fsb_snapshot.get("today")
                        fsb_today_amount = fsb_snapshot.get("today_amount")
                        fsb_yesterday = fsb_snapshot.get("yesterday")
                        fsb_yesterday_amount = fsb_snapshot.get("yesterday_amount")
                        fsb_daily = fsb_snapshot.get("daily")
                        fsb_daily_amount = fsb_snapshot.get("daily_amount")
                        fsb_daily_sums = fsb_snapshot.get("daily_sums")

                    sb_total = sb_latest = sb_earliest = None
                    sb_today = sb_today_amount = None
                    sb_yesterday = sb_yesterday_amount = None
                    sb_daily = sb_daily_amount = None
                    sb_daily_sums = None

                    if signed_blocks:
                        sb_snapshot = run_on_threadpool(P.parse_blocks_data, signed_blocks).result()
                        sb_total = sb_snapshot.get("total")
                        sb_latest = sb_snapshot.get("latest")
                        sb_earliest = sb_snapshot.get("earliest")
                        sb_today = sb_snapshot.get("today")
                        sb_today_amount = sb_snapshot.get("today_amount")
                        sb_yesterday = sb_snapshot.get("yesterday")
                        sb_yesterday_amount = sb_snapshot.get("yesterday_amount")
                        sb_daily = sb_snapshot.get("daily")
                        sb_daily_amount = sb_snapshot.get("daily_amount")
                        sb_daily_sums = sb_snapshot.get("daily_sums")

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
                        tx_snapshot = run_on_threadpool(P.parse_tx_data, tx_history).result()
                        tx_total_rewards = tx_snapshot.get("total_rewards")
                        tx_latest_reward = tx_snapshot.get("latest_reward")
                        tx_earliest_reward = tx_snapshot.get("earliest_reward")
                        tx_daily_rewards = tx_snapshot.get("daily")
                        tx_biggest_reward = tx_snapshot.get("biggest")
                        tx_smallest_reward = tx_snapshot.get("smallest")
                        tx_daily_sums = tx_snapshot.get("daily_sums")
                        tx_today_rewards = tx_snapshot.get("today")
                        tx_yesterday_rewards = tx_snapshot.get("yesterday")

                    if sovereign_tx_history:
                        self.sovereign_rewards[network] = sovereign_tx_history
                        sovereign_tx_snapshot = run_on_threadpool(P.parse_tx_data, sovereign_tx_history).result()
                        sovereign_tx_total_rewards = sovereign_tx_snapshot.get("total_rewards")
                        sovereign_tx_latest_reward = sovereign_tx_snapshot.get("latest_reward")
                        sovereign_tx_earliest_reward = sovereign_tx_snapshot.get("earliest_reward")
                        sovereign_tx_daily_rewards = sovereign_tx_snapshot.get("daily")
                        sovereign_tx_smallest_reward = sovereign_tx_snapshot.get("smallest")
                        sovereign_tx_biggest_reward = sovereign_tx_snapshot.get("biggest")
                        sovereign_tx_daily_sums = sovereign_tx_snapshot.get("daily_sums")
                        sovereign_tx_today_rewards = sovereign_tx_snapshot.get("today")
                        sovereign_tx_yesterday_rewards = sovereign_tx_snapshot.get("yesterday")

                    # ----------------------------------------------------------------
                    # Build cache
                    # ----------------------------------------------------------------
                    new_data = {
                        "block_count_today": futures["block_count_today"].result(),
                        "block_count": current_blocks_on_network,
                        "chain_size": futures["chain_size"].result(),
                        "current_block_reward": futures["current_block_reward"].result(),
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
                    self._gdb_save(network, new_data)

                    logger.info(
                        f"Cached data for {network} in {time.time() - start_time:.2f} seconds "
                        f"(memory + GDB updated)"
                    )
                time.sleep(60) # Magic number 60 might be just enough
                # And boom! We have a cache!
        except Exception as e:
            logger.error(f"An error occurred in the caching loop: {e}", exc_info=True)

    def get_cache(self, network):
        return self.cache.get(network, {})

cacher = Cacher()
