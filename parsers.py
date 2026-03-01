from collections import defaultdict
from logconfig import logger
from utils import utils
from datetime import datetime, timedelta

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
    def parse_blocks_data(blocks):
        try:
            if not blocks:
                logger.warning("No actual blocks found to parse")
                return {
                    "total": None,
                    "latest": None,
                    "earliest": None,
                    "today": None,
                    "today_amount": None,
                    "yesterday": None,
                    "yesterday_amount": None,
                    "daily": None,
                    "daily_amount": None,
                    "daily_sums": None,
                }

            now = datetime.now().astimezone()
            yesterday_date = (now - timedelta(days=1)).date()

            today_blocks = []
            yesterday_blocks = []
            daily_counts = defaultdict(int)

            for block in blocks:
                ts = datetime.fromisoformat(block['ts_create'])
                block_date = ts.date()
                date_key = block_date.isoformat()

                daily_counts[date_key] += 1

                if block_date == now.date():
                    today_blocks.append(block)
                elif block_date == yesterday_date:
                    yesterday_blocks.append(block)

            return {
                "total": len(blocks),
                "latest": blocks[0],
                "earliest": blocks[-1],
                "today": today_blocks,
                "today_amount": len(today_blocks),
                "yesterday": yesterday_blocks,
                "yesterday_amount": len(yesterday_blocks),
                "daily": blocks,
                "daily_amount": len(blocks),
                "daily_sums": [{"date": d, "block_count": v} for d, v in sorted(daily_counts.items())],
            }

        except Exception as e:
            logger.error(f"Error parsing blocks data: {e}", exc_info=True)
            return {
                "total": None,
                "latest": None,
                "earliest": None,
                "today": None,
                "today_amount": None,
                "yesterday": None,
                "yesterday_amount": None,
                "daily": None,
                "daily_amount": None,
                "daily_sums": None,
            }

    @staticmethod
    def parse_tx_data(tx_data):
        try:
            if not tx_data:
                logger.warning("No actual transactions found to parse")
                return {
                    "total_rewards": 0,
                    "latest_reward": None,
                    "earliest_reward": None,
                    "daily": [],
                    "biggest": None,
                    "smallest": None,
                    "daily_sums": [],
                    "today": 0,
                    "yesterday": 0,
                }

            reward_txs = []

            for tx in tx_data:
                if tx.get("service") == "block_reward":
                    sub_data = tx.get("data", [])
                    for entry in sub_data:
                        if entry.get("tx_type") == "recv":
                            reward_txs.append({
                                "tx_hash": tx.get("hash"),
                                "tx_created": tx.get("tx_created"),
                                "recv_coins": entry.get("recv_coins"),
                                "token": entry.get("token"),
                                "source_address": entry.get("source_address")
                            })

            now = datetime.now().astimezone()
            yesterday_date = (now - timedelta(days=1)).date()

            total_rewards = 0.0
            today_rewards = 0.0
            yesterday_rewards = 0.0
            daily_totals = defaultdict(float)
            biggest = None
            smallest = None

            for reward_tx in reward_txs:
                try:
                    reward_amount = float(reward_tx.get("recv_coins", 0))
                except (TypeError, ValueError):
                    continue

                total_rewards += reward_amount

                if biggest is None or reward_amount > float(biggest.get("recv_coins", 0)):
                    biggest = reward_tx
                if smallest is None or reward_amount < float(smallest.get("recv_coins", 0)):
                    smallest = reward_tx

                tx_created = reward_tx.get("tx_created")
                if not tx_created:
                    continue

                try:
                    tx_date = datetime.fromisoformat(tx_created).date()
                except Exception:
                    continue

                daily_totals[tx_date.isoformat()] += reward_amount
                if tx_date == now.date():
                    today_rewards += reward_amount
                elif tx_date == yesterday_date:
                    yesterday_rewards += reward_amount

            return {
                "total_rewards": total_rewards,
                "latest_reward": reward_txs[0] if reward_txs else None,
                "earliest_reward": reward_txs[-1] if reward_txs else None,
                "daily": reward_txs,
                "biggest": biggest,
                "smallest": smallest,
                "daily_sums": [{"date": d, "total_rewards": v} for d, v in sorted(daily_totals.items())],
                "today": today_rewards,
                "yesterday": yesterday_rewards,
            }

        except Exception as e:
            logger.error(f"Error parsing transaction data: {e}", exc_info=True)
            return {
                "total_rewards": 0,
                "latest_reward": None,
                "earliest_reward": None,
                "daily": [],
                "biggest": None,
                "smallest": None,
                "daily_sums": [],
                "today": 0,
                "yesterday": 0,
            }
