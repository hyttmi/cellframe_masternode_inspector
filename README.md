# Cellframe Masternode Inspector

Cellframe Masternode Inspector is a Python-based plugin for retrieving and displaying detailed statistics about your Cellframe node and all supported networks. It provides both **system-level** and **network-level** insights via a simple HTTP API using GET requests, authenticated with an access token.

---

## Features

- **System Stats**: Node uptime, version, CPU/memory usage, hostname, service status, and more (always live data).
- **Network Stats**: Block counts, chain size, rewards, wallet balances, signing stats, and more (cached for fast access).
- **Multi-Network Support**: Inspector gathers and caches stats for all networks running on your node (e.g. `Backbone`, `KelVPN`, and others).
- **Batch Actions**: Request multiple stats at once via a single query.
- **Easy Authentication**: Uses an auto-generated access token (saved in `token.txt`).
- **Flexible Output**: Query specific metrics or use `all` to get everything.
- **Customizable Configuration**: Configure via `cellframe-node.cfg` or drop-in config files.

---

## How It Works

- **System Actions:**
  Always return live data directly from your node.

- **Network Actions:**
  All network data (except for `autocollect_status` and `network_status`) is served from a per-network cache for fast access.
  - The inspector maintains a separate cache for each network supported by your node.
  - The actions `autocollect_status` and `network_status` always fetch live data.
  - All other network actions (e.g. block counts, rewards, daily stats) are served from cached values, which are refreshed at the interval specified in the config.
  - The cacher offloads most work to fast RPC nodes when available. For wallet operations, if RPC nodes are unavailable, it will automatically fall back to using your local node socket for these operations only.

---

## Installation

### 1. Locate Node Plugin Directory

Your node's plugin directory is typically:

```
/opt/cellframe-node/var/lib/plugins
```

You can confirm this path in your node configuration file (`/opt/cellframe-node/etc/cellframe-node.cfg`):

```
[plugins]
enabled=true
py_load=true
py_path=../var/lib/plugins
```

### 2. Copy the Plugin

**Note:** You usually need root access to write to the plugins directory.

Clone or download the `cellframe-masternode-inspector` repository, then copy it as root:

```bash
sudo cp -r cellframe-masternode-inspector /opt/cellframe-node/var/lib/plugins/
```

Or, if cloning directly to the plugins directory:

```bash
sudo git clone https://github.com/hyttmi/cellframe-masternode-inspector.git /opt/cellframe-node/var/lib/plugins/cellframe-masternode-inspector
```

### 3. Install Dependencies

**Important:**
Install dependencies using the node's own Python environment:

```bash
sudo /opt/cellframe-node/python/bin/pip3 install -r /opt/cellframe-node/var/lib/plugins/cellframe-masternode-inspector/requirements.txt
```

---

## Configuration

### Where to Configure

You can configure the inspector in **two ways**:

- **A. Main Config File:**
  Edit `/opt/cellframe-node/etc/cellframe-node.cfg` and add a `[mninspector]` section.

- **B. Drop-in Config File:**
  Create a config file (e.g. `mninspector.cfg`) in `/opt/cellframe-node/etc/cellframe-node.cfg.d/` with the following format:

  ```
  [mninspector]
  key=value
  ```

### Available Configuration Options

| Key                    | Default         | Description                                  |
|------------------------|----------------|----------------------------------------------|
| access_token_entropy   | 64             | Entropy (length) of generated access token   |
| days_cutoff            | 90             | Number of days for daily blocks and rewards history |
| cache_refresh_interval | 10             | Cache refresh interval in minutes            |
| gzip_responses         | False          | Enable gzip compression for HTTP responses   |
| debug                  | False          | Enable debug logging                         |
| plugin_url             | mninspector    | URL endpoint for the plugin                  |

**Example:**
```
[mninspector]
access_token_entropy=128
days_cutoff=30
cache_refresh_interval=5
gzip_responses=True
debug=True
plugin_url=mninspector
```

- **Note:**
  The `days_cutoff` option controls how many days of daily block and reward history are shown in actions with the `_daily`, `_daily_amount`, or `_daily_rewards` suffixes, and the total amount for these periods.

---

## Authentication

Every GET request to the Inspector API must be authenticated.
You have two options:

- **As a Query Parameter:**
  Add `access_token` to your GET request:
  ```
  ?access_token=YOUR_API_TOKEN
  ```

- **As a Header:**
  Add the header:
  ```
  X-API-Key: YOUR_API_TOKEN
  ```

The value of `YOUR_API_TOKEN` is the string found in `token.txt` (auto-generated on first launch).

---

## API Usage

### Endpoint

All requests are made to the `/mninspector` endpoint on your running instance (e.g. `http://localhost:8079/mninspector`).
If you changed the `plugin_url` config value, use that instead.

### System Actions

Query system-specific information about your node.

**Example:**

```bash
curl "http://localhost:8079/mninspector?action=node_uptime&access_token=YOUR_API_TOKEN"
```

or

```bash
curl -H "X-API-Key: YOUR_API_TOKEN" "http://localhost:8079/mninspector?action=node_uptime"
```

### Network Actions

Query network-specific information by specifying the `network` parameter.
The value for `network` should be the name of the network as configured in your node, for example:

- `Backbone`
- `KelVPN`
- (or any other network your node is supporting)

The inspector supports querying all networks that your node is running, and maintains a separate cache for each network.

**Example:**

```bash
curl "http://localhost:8079/mninspector?action=block_count&network=Backbone&access_token=YOUR_API_TOKEN"
curl "http://localhost:8079/mninspector?action=block_count&network=KelVPN&access_token=YOUR_API_TOKEN"
```

**Note:**
All network actions except `autocollect_status` and `network_status` are served from a per-network cache for fast access.
`autocollect_status` and `network_status` are always live.

The cacher offloads most network data fetching to fast RPC nodes, but for wallet operations will automatically fall back to using your local node socket if no RPC nodes are available.

### Batch Requests

You can request multiple actions at once by separating them with commas, or use `all` to fetch all available metrics.

**System Example:**

```bash
curl "http://localhost:8079/mninspector?action=node_uptime,node_cpu_usage,node_memory_usage&access_token=YOUR_API_TOKEN"
```

or fetch all system actions:

```bash
curl "http://localhost:8079/mninspector?action=all&access_token=YOUR_API_TOKEN"
```

**Network Example:**

```bash
curl "http://localhost:8079/mninspector?action=block_count,chain_size,network_status&network=Backbone&access_token=YOUR_API_TOKEN"
```

or fetch all network actions:

```bash
curl "http://localhost:8079/mninspector?action=all&network=Backbone&access_token=YOUR_API_TOKEN"
```

---

## Request and Response Format

### System Actions Example

**Request:**
```
GET http://localhost:8079/mninspector?action=all&access_token=YOUR_API_TOKEN
```

**Response:**
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
    "node_uptime": 1243.09466385841,
    "system_uptime": 2199.51475572586
  }
}
```

---

## Supported Actions

### System Actions List

- `current_node_version` — Current node software version.
- `external_ip` — Public IP address of the host.
- `hostname` — Hostname of the server.
- `latest_node_version` — Latest available Cellframe node version.
- `node_cpu_usage` — CPU usage of the node process.
- `node_memory_usage` — Memory usage of the node process.
- `node_pid` — Process ID of the node (if running).
- `node_running_as_service` — Whether node runs as a service.
- `node_uptime` — Node process uptime (seconds).
- `system_uptime` — Total system uptime (seconds).

### Network Actions List

- `autocollect_status` — Status of autocollect for the network (live).
- `block_count` — Number of blocks in the chain (cached, per-network).
- `cache_last_updated` — When network cache was last updated (cached, per-network).
- `chain_size` — Chain size (storage, cached, per-network).
- `current_block_reward` — Current reward per block (cached, per-network).
- `first_signed_blocks_count` — Count of first signed blocks (cached, per-network).
- `first_signed_blocks_daily` — Daily stats of first signed blocks (last N days, where N = `days_cutoff`, cached, per-network).
- `first_signed_blocks_daily_amount` — Total number of first signed blocks for the cutoff period (cached, per-network).
- `first_signed_blocks_earliest` — Earliest first signed block (cached, per-network).
- `first_signed_blocks_latest` — Latest first signed block (cached, per-network).
- `first_signed_blocks_today_amount` — Amount of first signed blocks today (cached, per-network).
- `first_signed_blocks_today` — First signed blocks today (cached, per-network).
- `first_signed_blocks_yesterday_amount` — Amount of first signed blocks yesterday (cached, per-network).
- `first_signed_blocks_yesterday` — First signed blocks yesterday (cached, per-network).
- `network_status` — Live network sync status (live).
- `signed_blocks_count` — Total signed blocks (cached, per-network).
- `signed_blocks_daily` — Daily signed block stats (last N days, where N = `days_cutoff`, cached, per-network).
- `signed_blocks_daily_amount` — Total number of signed blocks for the cutoff period (cached, per-network).
- `signed_blocks_earliest` — Earliest signed block (cached, per-network).
- `signed_blocks_latest` — Latest signed block (cached, per-network).
- `signed_blocks_today_amount` — Amount of signed blocks today (cached, per-network).
- `signed_blocks_today` — Signed blocks today (cached, per-network).
- `signed_blocks_yesterday_amount` — Amount of signed blocks yesterday (cached, per-network).
- `signed_blocks_yesterday` — Signed blocks yesterday (cached, per-network).
- `sovereign_reward_wallet_address` — Sovereign reward wallet address (cached, per-network).
- `sovereign_wallet_balance` — Sovereign wallet balance (cached, per-network).
- `sovereign_wallet_earliest_reward` — Earliest reward to sovereign wallet (cached, per-network).
- `sovereign_wallet_latest_reward` — Latest reward to sovereign wallet (cached, per-network).
- `sovereign_wallet_daily_rewards` — Daily sovereign rewards (last N days, where N = `days_cutoff`, cached, per-network).
- `sovereign_wallet_biggest_reward` — Biggest reward to sovereign wallet (cached, per-network).
- `sovereign_wallet_smallest_reward` — Smallest reward to sovereign wallet (cached, per-network).
- `reward_wallet_address` — Reward wallet address (cached, per-network).
- `reward_wallet_balance` — Reward wallet balance (cached, per-network).
- `reward_wallet_earliest_reward` — Earliest reward to reward wallet (cached, per-network).
- `reward_wallet_latest_reward` — Latest reward to reward wallet (cached, per-network).
- `reward_wallet_daily_rewards` — Daily rewards (last N days, where N = `days_cutoff`, cached, per-network).
- `reward_wallet_biggest_reward` — Biggest reward to reward wallet (cached, per-network).
- `reward_wallet_smallest_reward` — Smallest reward to reward wallet (cached, per-network).
- `token_price` — Current network token price (cached, per-network).

---

## License

This project is licensed under the GNU General Public License (GPL). See the [LICENSE](LICENSE) file for details.

---

## Contributing

Feel free to submit issues or pull requests!