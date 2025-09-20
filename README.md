# Cellframe Masternode Inspector

**Cellframe Masternode Inspector** is a Python plugin for monitoring and managing your Cellframe masternode. It provides live system stats and cached network stats through an authenticated HTTP API. It supports multiple networks, caches data per network, offloads work to RPC nodes when possible (with automatic local fallback for wallet operations), and refreshes its cache only when the blockchain advances by a configurable number of new blocks.

---

## Features

- **Live System Stats**: Uptime, CPU/memory usage, IP, hostname, version, and more.
- **Cached Network Stats**: Block counts, chain size, block rewards, wallet balances, signing stats, token price, and more—on all supported networks.
- **Multi-Network Support**: Works with all Cellframe networks running on your node (e.g. `Backbone`, `KelVPN`, etc.).
- **Efficient Caching**: Per-network cache is refreshed only when N new blocks are detected (`block_count_threshold`), not on a timer.
- **RPC Node Offload**: Inspector fetches network data from RPC nodes for fast access. Wallet queries automatically fall back to the local node if no RPC node is available.
- **Easy Authentication**: All HTTP API requests require an access token.
- **Batch Actions**: Query multiple metrics at once.
- **Flexible Configuration**: Configure via node config or drop-in file.

---

## How It Works

- **System actions** always return live, up-to-date data directly from your node.
- **Network actions** (except `network_status` and `autocollect_status`) return cached data, which is refreshed after a configurable number of new blocks are detected (see `block_count_threshold`).
- **Wallet operations** use RPC nodes for speed, but will automatically use your local node if RPC nodes are unavailable.
- **`network_status` and `autocollect_status`** always provide live data.

---

## Installation

### 1. Find Your Plugin Directory

Typically:
```
/opt/cellframe-node/var/lib/plugins
```
Check your node config (`/opt/cellframe-node/etc/cellframe-node.cfg`):
```
[plugins]
enabled=true
py_load=true
py_path=../var/lib/plugins
```

### 2. Copy the Plugin

Clone and copy as root:
```bash
sudo cp -r cellframe-masternode-inspector /opt/cellframe-node/var/lib/plugins/
```
Or clone directly:
```bash
sudo git clone https://github.com/hyttmi/cellframe-masternode-inspector.git /opt/cellframe-node/var/lib/plugins/cellframe-masternode-inspector
```

### 3. Install Dependencies

Use the node's Python environment:
```bash
sudo /opt/cellframe-node/python/bin/pip3 install -r /opt/cellframe-node/var/lib/plugins/cellframe-masternode-inspector/requirements.txt
```

---

## Configuration

### How to Configure

You can configure via:

- **A. Main Config File**:
  Add a `[mninspector]` section to `/opt/cellframe-node/etc/cellframe-node.cfg`.

- **B. Drop-in Config File**:
  Create `/opt/cellframe-node/etc/cellframe-node.cfg.d/mninspector.cfg` with:
  ```
  [mninspector]
  key=value
  ```

### Supported Options

| Key                     | Default | Description                                                         |
|-------------------------|---------|---------------------------------------------------------------------|
| access_token_entropy    | 64      | Entropy (length) of generated access token                          |
| days_cutoff             | 90      | Number of days for daily block/reward stats                         |
| block_count_threshold   | 20      | Cache is refreshed after this many new blocks are detected          |
| gzip_responses          | false   | Enable gzip compression for HTTP responses                          |
| debug                   | false   | Enable debug logging                                                |
| plugin_url              | mninspector | URL endpoint for the plugin                                    |

**Example:**
```
[mninspector]
access_token_entropy=128
days_cutoff=30
block_count_threshold=10
gzip_responses=true
debug=true
plugin_url=mninspector
```

- **Note:**
  `days_cutoff` controls days shown in daily block/reward history actions (`_daily`, `_daily_amount`, `_daily_rewards`).
  `block_count_threshold` sets how often the cache is refreshed per network.

---

## Authentication

You must authenticate every request, either by:

- **Query parameter**:
  `?access_token=YOUR_API_TOKEN`
- **Header**:
  `X-API-Key: YOUR_API_TOKEN`

Find your token in `token.txt` (auto-generated on first launch).

---

## API Usage

### Endpoint

All requests go to `/mninspector` (or your custom `plugin_url`).

### System Actions

Return live system stats.

**Example:**
```bash
curl "http://localhost:8079/mninspector?action=node_uptime&access_token=YOUR_API_TOKEN"
curl -H "X-API-Key: YOUR_API_TOKEN" "http://localhost:8079/mninspector?action=node_uptime"
```

### Network Actions

**Network actions must use the `network_action` parameter.**

Query stats for a specific network:
```bash
curl "http://localhost:8079/mninspector?network_action=block_count&network=Backbone&access_token=YOUR_API_TOKEN"
curl "http://localhost:8079/mninspector?network_action=block_count&network=KelVPN&access_token=YOUR_API_TOKEN"
```

Multiple network actions (comma-separated):
```bash
curl "http://localhost:8079/mninspector?network_action=block_count,chain_size,network_status&network=Backbone&access_token=YOUR_API_TOKEN"
```

All supported networks (with per-network cache).

**Note:**
Most network actions return cached data, refreshed after `block_count_threshold` new blocks.
`network_status` and `autocollect_status` are always live.

### Batch Requests

Query multiple actions at once (comma-separated), or use `all` for all metrics.

**System Example:**
```bash
curl "http://localhost:8079/mninspector?action=node_uptime,node_cpu_usage,node_memory_usage&access_token=YOUR_API_TOKEN"
curl "http://localhost:8079/mninspector?action=all&access_token=YOUR_API_TOKEN"
```

**Network Example:**
```bash
curl "http://localhost:8079/mninspector?network_action=block_count,chain_size,network_status&network=Backbone&access_token=YOUR_API_TOKEN"
curl "http://localhost:8079/mninspector?network_action=all&network=Backbone&access_token=YOUR_API_TOKEN"
```

---

## Response Format

**System Actions Example:**
```json
{
  "request_timestamp": "2025-09-15T15:02:46.514775+00:00",
  "status": "ok",
  "data": {
    "current_node_version": "5.4.28",
    "external_ip": "195.181.202.122",
    "hostname": "zenbook",
    "latest_node_version": "5.4.28",
    "node_cpu_usage": 2.625,
    "node_memory_usage": 8959.84,
    "node_pid": 5766,
    "node_running_as_service": false,
    "node_uptime": 1243.094,
    "system_uptime": 2199.514
  }
}
```

---

## Supported Actions

### System Actions

| action                   | value/meaning                                              |
|--------------------------|-----------------------------------------------------------|
| `current_node_version`   | Current node software version                             |
| `external_ip`            | Public IP address of host                                 |
| `hostname`               | Hostname of the server                                    |
| `latest_node_version`    | Latest available Cellframe node version                   |
| `node_cpu_usage`         | Node process CPU usage (%)                                |
| `node_memory_usage`      | Node process memory usage (MB)                            |
| `node_pid`               | Node process ID                                           |
| `node_running_as_service`| Whether node is running as a system service (true/false)  |
| `node_uptime`            | Node process uptime (seconds)                             |
| `system_uptime`          | Total system uptime (seconds)                             |

### Network Actions (per network)

| network_action                       | value/meaning                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------|
| `autocollect_status`                  | **Live.** Status of autocollect (enabled/disable etc.)                         |
| `block_count`                         | **Cached.** Total number of blocks in network's blockchain                                        |
| `cache_last_updated`                  | **Cached.** ISO timestamp of last cache refresh for this network                                  |
| `chain_size`                          | **Cached.** Total chain data size (bytes/MB/GB) for this network                                 |
| `current_block_reward`                | **Cached.** Current block reward (tokens) on this network                                         |
| `first_signed_blocks_count`           | **Cached.** Number of blocks your node was the first to sign                                      |
| `first_signed_blocks_daily`           | **Cached.** List: daily counts of first-signed blocks for last N days                             |
| `first_signed_blocks_daily_amount`    | **Cached.** Sum of first-signed blocks over last N days                                           |
| `first_signed_blocks_earliest`        | **Cached.** Details (block number, timestamp) of earliest first-signed block                      |
| `first_signed_blocks_latest`          | **Cached.** Details (block number, timestamp) of latest first-signed block                        |
| `first_signed_blocks_today_amount`    | **Cached.** How many first-signed blocks today                                                    |
| `first_signed_blocks_today`           | **Cached.** List of today's first-signed blocks (numbers/timestamps)                              |
| `first_signed_blocks_yesterday_amount`| **Cached.** How many first-signed blocks yesterday                                                |
| `first_signed_blocks_yesterday`       | **Cached.** List of yesterday's first-signed blocks (numbers/timestamps)                          |
| `network_status`                      | **Live.** Current network sync status (e.g., synced, etc.)                          |
| `signed_blocks_count`                 | **Cached.** How many blocks your node signed on this network                                      |
| `signed_blocks_daily`                 | **Cached.** List: daily counts of signed blocks for last N days                                   |
| `signed_blocks_daily_amount`          | **Cached.** Sum of signed blocks over last N days                                                 |
| `signed_blocks_earliest`              | **Cached.** Details (block number, timestamp) of earliest signed block                            |
| `signed_blocks_latest`                | **Cached.** Details (block number, timestamp) of latest signed block                              |
| `signed_blocks_today_amount`          | **Cached.** How many blocks signed today                                                          |
| `signed_blocks_today`                 | **Cached.** List of today's signed blocks (numbers/timestamps)                                    |
| `signed_blocks_yesterday_amount`      | **Cached.** How many blocks signed yesterday                                                      |
| `signed_blocks_yesterday`             | **Cached.** List of yesterday's signed blocks (numbers/timestamps)                                |
| `sovereign_reward_wallet_address`     | **Cached.** Sovereign reward wallet address (from config)                                         |
| `sovereign_wallet_balance`            | **Cached.** Balance of sovereign wallet (tokens)                                                  |
| `sovereign_wallet_earliest_reward`    | **Cached.** Details about earliest reward received in the sovereign wallet                        |
| `sovereign_wallet_latest_reward`      | **Cached.** Details about latest reward received in the sovereign wallet                          |
| `sovereign_wallet_daily_rewards`      | **Cached.** List: daily sovereign wallet rewards for last N days                                  |
| `sovereign_wallet_biggest_reward`     | **Cached.** Largest reward received by sovereign wallet                                           |
| `sovereign_wallet_smallest_reward`    | **Cached.** Smallest reward received by sovereign wallet                                          |
| `reward_wallet_address`               | **Cached.** Standard reward wallet address (from config)                                          |
| `reward_wallet_balance`               | **Cached.** Balance of standard reward wallet (tokens)                                            |
| `reward_wallet_earliest_reward`       | **Cached.** Details about earliest reward received in the reward wallet                           |
| `reward_wallet_latest_reward`         | **Cached.** Details about latest reward received in the reward wallet                             |
| `reward_wallet_daily_rewards`         | **Cached.** List: daily rewards for standard reward wallet for last N days                        |
| `reward_wallet_biggest_reward`        | **Cached.** Largest reward received by reward wallet                                              |
| `reward_wallet_smallest_reward`       | **Cached.** Smallest reward received by reward wallet                                             |
| `token_price`                         | **Cached.** Current network token price (if available)                                            |

---

## License

This project is licensed under the GNU General Public License (GPL). See [LICENSE](LICENSE).

---

## Contributing

Pull requests and issues are welcome!