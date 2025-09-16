from collections import defaultdict
from logconfig import logger
from utils import utils
from datetime import datetime, timedelta, timezone
from config import Config

class Parsers:
    @staticmethod
    def replace_timestamps(network_data, blocks=False):
        if not network_data or not isinstance(network_data, list):
            logger.warning("No network data provided to replace_timestamps")
            return []

        key = "ts_create" if blocks else "tx_created"
        result = []

        for item in network_data:
            if not blocks and item.get("status") != "ACCEPTED":
                continue

            if key in item and item[key]:
                try:
                    item[key] = utils.rfc2822_str_to_iso(item[key])
                except Exception as e:
                    logger.warning(f"Error converting {key} {item[key]} to ISO: {e}", exc_info=True)

            result.append(item)
        logger.debug(f"Pre-parsed {len(result)} {'blocks' if blocks else 'transactions'}")

        return result

    @staticmethod
    def parse_blocks_data(blocks, option="total", days=Config.DAYS_CUTOFF):
        try:
            if not blocks:
                logger.warning("No actual blocks found to parse")
                return (0, 0) if option in ["today", "yesterday", "daily"] else []

            if option == "total":
                return len(blocks)
            if option == "latest":
                return blocks[0]
            if option == "earliest":
                return blocks[-1]
            if option == "all":
                return blocks

            now = datetime.now(timezone.utc)
            filtered = []

            if option == "today":
                for block in blocks:
                    ts = datetime.fromisoformat(block['ts_create'])
                    if ts.date() == now.date():
                        filtered.append(block)
                return filtered, len(filtered)

            if option == "yesterday":
                yesterday_date = (now - timedelta(days=1)).date()
                for block in blocks:
                    ts = datetime.fromisoformat(block['ts_create'])
                    if ts.date() == yesterday_date:
                        filtered.append(block)
                return filtered, len(filtered)

            if option == "daily":
                cutoff = now - timedelta(days=days)
                for block in blocks:
                    ts = datetime.fromisoformat(block['ts_create'])
                    if ts >= cutoff:
                        filtered.append(block)
                return filtered, len(filtered)

            if option == "daily_sums":
                daily_counts = defaultdict(int)
                for block in blocks:
                    ts = datetime.fromisoformat(block['ts_create'])
                    date_key = ts.date().isoformat()
                    daily_counts[date_key] += 1
                return [{"date": d, "block_count": v} for d, v in sorted(daily_counts.items())]

            logger.warning(f"Unknown option {option} in parse_blocks_data")
            return None

        except Exception as e:
            logger.error(f"Error parsing blocks data: {e}", exc_info=True)
            return None

    @staticmethod
    def parse_tx_data(tx_data, option="count", days=Config.DAYS_CUTOFF):
        try:
            if not tx_data:
                logger.warning("No actual transactions found to parse")
                return []

            results = []

            for tx in tx_data:
                if tx.get("service") == "block_reward":
                    sub_data = tx.get("data", [])
                    for entry in sub_data:
                        if entry.get("tx_type") == "recv":
                            results.append({
                                "tx_hash": tx.get("hash"),
                                "tx_created": tx.get("tx_created"),
                                "recv_coins": entry.get("recv_coins"),
                                "token": entry.get("token"),
                                "source_address": entry.get("source_address")
                            })

            tx_data = results

            filtered = []
            now = datetime.now(timezone.utc)

            # OK, now we have the reward transactions only
            if option == "total_rewards":
                return sum(float(tx['recv_coins']) for tx in tx_data if 'recv_coins' in tx)
            if option == "latest_reward":
                return tx_data[0]
            if option == "earliest_reward":
                return tx_data[-1]
            if option == "daily":
                cutoff = now - timedelta(days=days)
                for tx in tx_data:
                    ts = datetime.fromisoformat(tx['tx_created'])
                    if ts >= cutoff:
                        filtered.append(tx)
                return filtered
            if option == "biggest":
                return max(
                    (tx for tx in tx_data if 'recv_coins' in tx),
                    key=lambda tx: float(tx['recv_coins'])
                )
            if option == "smallest":
                return min(
                    (tx for tx in tx_data if 'recv_coins' in tx),
                    key=lambda tx: float(tx['recv_coins'])
                )
            if option == "daily_sums":
                daily_totals = defaultdict(float)
                for tx in tx_data:
                    ts = datetime.fromisoformat(tx['tx_created'])
                    date_key = ts.date().isoformat()
                    daily_totals[date_key] += float(tx['recv_coins'])
                return [{"date": d, "total_rewards": v} for d, v in sorted(daily_totals.items())]

        except Exception as e:
            logger.error(f"Error parsing transaction data: {e}", exc_info=True)
            return []
