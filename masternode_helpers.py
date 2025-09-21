from logconfig import logger
from pycfhelpers.node.net import CFNet, NetFee
from utils import utils
import re, requests, os

class MasternodeHelpers:
    def __init__(self):
        logger.debug("Initializing MasternodeRequests...")
        self._node_address = None
        self._active_networks_config = {}
        self._get_active_networks()
        logger.debug(f"Active networks (masternode only): {self._active_networks_config}")
        logger.debug(f"Node address: {self._node_address}")
        logger.debug("MasternodeRequests initialized.")

    def _get_active_networks(self):
        try:
            for net in CFNet.active_nets():
                network_name = str(net.name)
                self._node_address = str(net.node_address) # This is the same for all networks so don't write it to network config
                net_config = self.get_network_config(network_name)
                if net_config:
                    self._active_networks_config[network_name] = net_config
                    self._active_networks_config[network_name]['native_ticker'] = str(NetFee(net).native_ticker)

        except Exception as e:
            logger.error(f"Error fetching active networks: {e}")

    def get_network_config(self, network):
        network_config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"

        net_config = {}
        master_role_found = False

        try:
            with open(network_config_file, "r") as file:
                for line in file:
                    line = line.strip()
                    cert_match = re.search(r"^blocks-sign-cert=(.+)", line)
                    wallet_match = re.search(r"^fee_addr=(.{104})", line)

                    if line == "node-role=master":
                        master_role_found = True

                    if cert_match:
                        logger.debug(f"Found cert name: {cert_match.group(1)}")
                        net_config['blocks_sign_cert'] = cert_match.group(1).strip()

                    if wallet_match:
                        logger.debug(f"Found wallet address: {wallet_match.group(1)}")
                        wallet_address = wallet_match.group(1).strip()
                        net_config['wallet'] = wallet_address

            if not master_role_found:
                logger.info(f"Node is (probably) not a masternode for {network}")
                return None

            if "blocks_sign_cert" in net_config and "wallet" in net_config:
                logger.debug(f"Fetching public key hash for cert {net_config['blocks_sign_cert']}...")
                cert_pkey_hash = utils.cli_command(f"cert pkey show {net_config['blocks_sign_cert']}", is_tool_command=True)

                if cert_pkey_hash:
                    net_config['cert_pkey_hash'] = cert_pkey_hash.strip()
                logger.debug(f"Valid masternode config for {network}")
                return net_config

            logger.warning(f"Incomplete config for {network} in {network_config_file}")
            return None
        except Exception as e:
            logger.error(f"Error reading config file {network_config_file}: {e}")
            return None

    def get_autocollect_status(self, network):
        try:
            autocollect_status = {}
            autocollect_cmd = utils.cli_command(f"block autocollect status -net {network}", timeout=3)

            amounts = re.findall(r"profit is ([\d.]+)", autocollect_cmd)
            autocollect_status['rewards'] = sum(float(amount) for amount in amounts) if amounts else 0

            autocollect_status['active'] = True if "is active" in autocollect_cmd else False

            return autocollect_status
        except Exception as e:
            logger.error(f"Error fetching autocollect status for {network}: {e}", exc_info=True)
            return None

    def get_current_block_reward(self, network):
        try:
            block_reward_cmd = utils.cli_command(f"block reward show -net {network}", timeout=3)
            if block_reward_cmd:
                match = re.search(r"([\d.]+)", block_reward_cmd)
                return float(match.group(1)) if match else None
            return None
        except Exception as e:
            logger.error(f"Error fetching block reward for {network}: {e}", exc_info=True)
            return None

    def get_block_count(self, network):
        logger.debug(f"Fetching block count for {network}")
        try:
            response = utils.send_request(
                "block",
                "count",
                arguments= {
                    "net": network,
                    "chain": "main"
                    },
                use_unix=True
                )

            if response:
                count = response['result'][0]
                block_count = next(iter(count.values()))
                logger.debug(f"Fetched block count of {block_count} for {network}")
                return block_count
            return 0
        except Exception as e:
            logger.error(f"An error occurred while fetching block count for {network}: {e}", exc_info=True)
            return 0

    def get_blocks_on_network_today(self, network):
        logger.debug(f"Fetching blocks from today for {network}")
        try:
            today_str = utils.current_time_in_format("%y%m%d")
            response = utils.send_request(
                "block",
                "list",
                arguments= {
                    "net": network,
                    "chain": "main",
                    "from_date": today_str
                    },
                use_unix=True
                )

            if not response or "result" not in response or not response['result']:
                logger.warning(f"No blocks found for {network} today")
                return 0

            if response and "result" in response and response['result']:
                blocks = response['result'][0][:-1]
                return len(blocks) # Might be 0, but at least it's a number
            logger.warning(f"No blocks found for {network} today")
            return 0
        except Exception as e:
            logger.error(f"An error occurred while fetching signed blocks for {network}: {e}", exc_info=True)
            return 0

    def get_signed_blocks(self, network, first_signed=False):
        logger.debug(f"Fetching {'first signed' if first_signed else 'signed'} blocks for {network}")
        try:
            pkey_hash = self._active_networks_config[network]['cert_pkey_hash']
            args = {
                "net": network,
                "chain": "main",
            }
            if pkey_hash:
                args["pkey_hash"] = pkey_hash
            else:
                args["cert"] = self._active_networks_config[network]['blocks_sign_cert']
            response = utils.send_request(
                "block",
                f"list {'first_signed' if first_signed else 'signed'}",
                arguments=args,
                use_unix=True
                )

            if not response or "result" not in response or not response['result']:
                return []

            if response:
                blocks = response['result'][0][:-1] # remove limit entry
                logger.debug(f"Fetched {len(blocks)} {'first signed' if first_signed else 'signed'} blocks for {network}")
                return blocks if blocks else []

            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching signed blocks for {network}: {e}", exc_info=True)
            return None

    def get_tx_history(self, network, address):
        logger.debug(f"Fetching tx history for {network} with address {address}")
        try:
            response = utils.send_request(
                "tx_history",
                subcommand=None,
                arguments={
                    "net": network,
                    "addr": address,
                    "limit": None
                    }
                )

            if not response or "result" not in response or not response['result']:
                return []

            if response:
                tx_history = response['result'][0]
                logger.debug(f"Fetched tx history for {address} on {network}, total records: {len(tx_history)}")
                return tx_history if tx_history else []

            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching rewards collected for {network}: {e}", exc_info=True)
            return None

    def get_network_status(self, network):
        try:
            response = utils.send_request("net", "get status", {"net": network}, use_unix=True)
            if not response or "result" not in response or not response['result']:
                return None

            status = response['result'][0].get("status", {})
            processed = status.get("processed", {})
            states = status.get("states", {})
            current_state = states.get("current", "N/A")
            target_state = states.get("target", "N/A")

            zero = processed.get("zerochain", {})
            main = processed.get("main", {})

            zero_current = int(zero.get("current", 0)) if str(zero.get("current", "0")).isdigit() else 0
            zero_in_network = int(zero.get("in network", 0)) if str(zero.get("in network", "0")).isdigit() else 0
            main_current = int(main.get("current", 0)) if str(main.get("current", "0")).isdigit() else 0
            main_in_network = int(main.get("in network", 0)) if str(main.get("in network", "0")).isdigit() else 0

            logger.debug(
                f"Sync check for {network}: "
                f"zerochain {zero_current}/{zero_in_network}, "
                f"main {main_current}/{main_in_network}"
            )

            network_status = {
                "synced": (
                    zero_current >= zero_in_network and
                    main_current >= main_in_network and
                    zero_in_network > 0 and
                    main_in_network > 0
                ),
                "node_address": self._node_address,
                "current_state": current_state,
                "target_state": target_state
            }
            return network_status
        except Exception as e:
            logger.error(f"An error occurred while checking sync status for {network}: {e}", exc_info=True)
            return None

    def get_sovereign_addr(self, network):
        try:
            response = utils.send_request("srv_stake", "list keys", {"net": network}, use_unix=True)
            sovereign_addr = None
            if response and "result" in response and response['result']:
                entries = response['result'][0]
                for entry in entries:
                    if entry.get("node_addr") == self._node_address:
                        addr = entry.get("sovereign_addr")
                        logger.debug(f"Got addr: {addr}")
                        if addr and addr != "null":
                            sovereign_addr = addr
                            logger.debug(f"Sovereign address for {network}: {sovereign_addr}")
                            break
            masternode_helpers._active_networks_config[network]['sovereign_addr'] = sovereign_addr
            return sovereign_addr
        except Exception as e:
            logger.error(f"An error occurred while fetching sovereign address for {network}: {e}", exc_info=True)

    def get_wallet_balance(self, network, address):
        try:
            response = utils.send_request(
                "wallet",
                "info",
                arguments={
                    "net": network,
                    "addr": address
                },
                use_unix=True
            )
            if not response or "result" not in response or not response['result']:
                return {}

            tokens = response['result'][0][0].get("tokens", [])
            balances = {
                t["token"]["ticker"]: float(t["coins"])
                for t in tokens
                if "token" in t and "coins" in t
            }

            logger.debug(balances)
            return balances
        except Exception as e:
            logger.error(f"Failed to get wallet balance for {network}: {e}", exc_info=True)
            return {}

    def get_chain_size(self, network):
        try:
            network_mapping = {
                'Backbone': 'scorpion',
                'KelVPN': 'kelvpn'
            }
            if network not in network_mapping:
                logger.debug(f"Unknown network: {network}. Can't fetch chain size...")
                return None
            dir = network_mapping[network]
            chain_path = f"/opt/cellframe-node/var/lib/network/{dir}/main/0.dchaincell"
            logger.debug(f"Checking chain size for {chain_path}...")
            if not os.path.exists(chain_path):
                logger.error(f"Chaincell file not found for {network}")
                return None
            logger.debug(f"Chain path for {network} exists!")
            size = os.path.getsize(chain_path)
            return size # in bytes
        except Exception as e:
            logger.error(f"An error occurred while fetching chain size for {network}: {e}", exc_info=True)
            return None

    def get_token_price(self, network):
        try:
            logger.debug("Fetching token price...")
            network_urls = {
                "backbone": "https://coinmarketcap.com/currencies/cellframe/",
                "kelvpn": "https://kelvpn.com/about-token"
            }
            url = network_urls.get(network.lower())
            if not url:
                logger("e", f"Unsupported network {network}")
                return None
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                regex_patterns = {
                    "backbone": r"price today is \$([\d.]+)",
                    "kelvpn": r"\$([\d.]+)"
                }
                regex_match = re.search(regex_patterns[network.lower()], response.text)
                if regex_match:
                    token_price = float(regex_match.group(1))
                    logger.debug(f"Token price for {network} is {token_price}")
                    return token_price
                logger.warning(f"Price not found in {url}")
                return None
            logger.error("e", f"Failed to fetch token price from {url}. Status code was {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching token price: {e}", exc_info=True)
            return None

masternode_helpers = MasternodeHelpers()