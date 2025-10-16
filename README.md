<div align="center">
  <img src="logo.svg" alt="Cellframe Masternode Inspector Logo" width="120" height="120">
  <h1>Cellframe Masternode Inspector</h1>
  <p>A Python plugin for Cellframe Node that provides a comprehensive HTTP API for monitoring and managing your masternode. Retrieve real-time system statistics, multi-network blockchain data, rewards tracking, and performance metrics through a simple authenticated REST API.</p>

  <p>
    <img src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" alt="License">
    <img src="https://img.shields.io/badge/version-1.09-green.svg" alt="Version">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/platform-Linux-lightgrey.svg" alt="Platform">
  </p>
</div>

## Features

### System Monitoring
- **Real-time CPU and Memory Usage** - Monitor node resource consumption
- **System and Node Uptime** - Track how long your node has been running
- **Version Information** - Current and latest node/plugin versions
- **Network Configuration** - Active networks and node configuration
- **External IP and Hostname** - Node identification and accessibility

### Multi-Network Support
- **Network-Specific Data** - Independent monitoring for each active network
- **Per-Network Caching** - Optimized performance with intelligent caching
- **RPC Offloading** - Delegates to RPC nodes where possible (with local fallback)
- **Network State Tracking** - Monitor sync status and network connectivity

### Blockchain Analytics
- **Block Rewards Tracking** - Daily, weekly, and historical reward data
- **Signed Blocks Statistics** - First signed and all signed blocks monitoring
- **Validator Metrics** - Fee tracking (min/avg/max), stake values, and weights
- **Historical Data** - Configurable days cutoff for historical analytics

### Wallet Management
- **Reward Wallet Monitoring** - Balance, addresses, and transaction tracking
- **Sovereign Wallet Support** - Dedicated sovereign network wallet tracking
- **Transaction Details** - Biggest/smallest rewards, latest transactions
- **Daily Summaries** - Rewards received today, yesterday, and historical

### Performance & Caching
- **Intelligent Caching** - Network data cached per-network for speed
- **Automatic Updates** - Background cache refresh on configurable intervals
- **Gzip Compression** - Reduced bandwidth with optional response compression
- **Concurrent Requests** - Thread pool for handling multiple simultaneous requests

### Security
- **Token Authentication** - Secure X-API-Key header or query parameter authentication
- **Auto-generated Tokens** - Cryptographically secure tokens (16-64 bytes entropy)
- **CORS Support** - Configurable cross-origin resource sharing
- **Access Logging** - Detailed request/response logging for auditing

## Requirements

### Cellframe Node
- **Minimum Version**: 5.5.0 or higher
- **Platform**: Linux only
- **Active Masternode**: At least one active network with masternode configuration

### Python Dependencies
- `command_runner>=1.7.4` - System command execution
- `requests>=2.32.5` - HTTP client for RPC communication
- `requests_unixsocket>=0.4.1` - Unix socket support
- `psutil>=7.0.0` - System resource monitoring
- `packaging>=25.0` - Version comparison utilities

## Installation

### Quick Install

1. **Clone the repository**
   ```bash
   git clone https://github.com/hyttmi/cellframe_masternode_inspector.git
   cd cellframe_masternode_inspector
   ```

2. **Run the installer**
   ```bash
   sudo python3 install.py
   ```

3. **Restart Cellframe Node**
   ```bash
   sudo systemctl restart cellframe-node
   ```

4. **Verify installation**
   ```bash
   cat /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/mninspector.log
   ```

## Configuration

Configuration is managed via `/opt/cellframe-node/etc/cellframe-node.cfg.d/mninspector.cfg`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `autoupdate` | boolean | `true` | Automatically update the plugin **RESTARTS NODE AUTOMATICALLY** |
| `plugin_url` | string | `mninspector` | URL path for the API endpoint |
| `days_cutoff` | integer | `20` | Number of days of historical data to cache |
| `block_count_threshold` | integer | `30` | Minimum blocks before caching network data |
| `access_token_entropy` | integer | `64` | Token entropy in bytes (16-64) |
| `compress_responses` | boolean | `true` | Enable gzip compression for responses |
| `debug` | boolean | `false` | Enable debug logging |

### Finding Your Node's HTTP Port

The HTTP port is configured in your Cellframe node configuration file under the `[server]` section. Look for the `listen_address` line:
```bash
grep -A 10 "\[server\]" /opt/cellframe-node/etc/cellframe-node.cfg | grep "listen_address"
```

Example output: `listen_address=[0.0.0.0:51412]` - the port here is `51412`.

### Example Configuration

```ini
[mninspector]
autoupdate=true
plugin_url=mninspector
days_cutoff=60
block_count_threshold=50
access_token_entropy=64
compress_responses=true
debug=false
```

## API Usage

### Base URL Format

```
http://localhost:<NODE_PORT>/<plugin_url>
```

Where:
- `<NODE_PORT>` is your Cellframe node's HTTP port (check your node configuration)
- `<plugin_url>` is the value from `plugin_url` config (default: `mninspector`)

Example: `http://localhost:8079/mninspector`

### Authentication

All requests require authentication via `X-API-Key` header or `access_token` query parameter:

**Header authentication (recommended):**
```bash
curl -H "X-API-Key: YOUR_TOKEN_HERE" "http://localhost:<NODE_PORT>/mninspector?action=help"
```

**Query parameter authentication:**
```bash
curl "http://localhost:<NODE_PORT>/mninspector?action=help&access_token=YOUR_TOKEN_HERE"
```

### System Actions

**Get all system data:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" "http://localhost:<NODE_PORT>/mninspector?action=all"
```

**Get specific system data:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" "http://localhost:<NODE_PORT>/mninspector?action=node_cpu_usage,node_memory_usage,system_uptime"
```

**Available system actions:**
- `all` - Get all system data at once
- `help` - List all available system actions
- `active_networks` - List of active masternode networks
- `current_node_version` - Installed Cellframe node version
- `current_plugin_version` - Installed plugin version
- `external_ip` - Node external IP address
- `hostname` - System hostname
- `latest_node_version` - Latest available node version
- `latest_plugin_version` - Latest available plugin version
- `node_cpu_usage` - Node CPU usage percentage
- `node_memory_usage` - Node memory usage in MB
- `node_pid` - Node process ID
- `node_running_as_service` - Whether node runs as systemd service
- `node_uptime` - Node process uptime in seconds
- `plugin_update_available` - Plugin update available
- `system_uptime` - System uptime in seconds
- `update_plugin` - Will update the plugin if update is available

### Network Actions

**Get all network data:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" "http://localhost:<NODE_PORT>/mninspector?network=Backbone&network_action=all"
```

**Get specific network data:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" "http://localhost:<NODE_PORT>/mninspector?network=Backbone&network_action=network_status,reward_wallet_balance,autocollect_status"
```

**Multiple networks:**
```bash
curl -H "X-API-Key: YOUR_TOKEN" "http://localhost:<NODE_PORT>/mninspector?network=Backbone,mileena&network_action=all"
```

**Available network actions:**
- `all` - Get all network data at once
- `help` - List all available network actions
- `autocollect_status` - Autocollect status and pending rewards
- `block_count` - Total network block count
- `block_count_today` - Blocks signed today
- `cache_last_updated` - Last cache update timestamp
- `chain_size` - Blockchain size in bytes
- `current_block_reward` - Current block reward amount
- `days_cutoff` - Days of historical data available
- `effective_value` - Effective stake value
- `first_signed_blocks_all_sums_daily` - Sum of first signed blocks per day
- `first_signed_blocks_count` - Total first signed blocks count
- `first_signed_blocks_daily` - Daily first signed blocks data
- `first_signed_blocks_daily_amount` - Number of daily first signed block records
- `first_signed_blocks_earliest` - Earliest first signed block
- `first_signed_blocks_latest` - Latest first signed block
- `first_signed_blocks_today` - Today's first signed blocks
- `first_signed_blocks_today_amount` - First blocks signed today count
- `first_signed_blocks_yesterday` - Yesterday's first signed blocks
- `first_signed_blocks_yesterday_amount` - Yesterday's first signed blocks count
- `native_ticker` - Network's native token ticker
- `network_status` - Sync status, node address, network state
- `relative_weight` - Validator weight percentage
- `reward_wallet_address` - Reward wallet address
- `reward_wallet_all_sums_daily` - Sum of rewards per day
- `reward_wallet_balance` - Current wallet balance
- `reward_wallet_biggest_reward` - Biggest reward received
- `reward_wallet_daily_rewards` - Daily rewards data
- `reward_wallet_earliest_reward` - Earliest reward received
- `reward_wallet_latest_reward` - Latest reward received
- `reward_wallet_smallest_reward` - Smallest reward received
- `reward_wallet_today_rewards` - Today's rewards
- `reward_wallet_total_rewards` - Total rewards received
- `reward_wallet_yesterday_rewards` - Yesterday's rewards
- `signed_blocks_all_sums_daily` - Sum of signed blocks per day
- `signed_blocks_count` - Total signed blocks count
- `signed_blocks_daily` - Daily signed blocks data
- `signed_blocks_daily_amount` - Number of daily signed block records
- `signed_blocks_earliest` - Earliest signed block
- `signed_blocks_latest` - Latest signed block
- `signed_blocks_today` - Today's signed blocks
- `signed_blocks_today_amount` - Blocks signed today count
- `signed_blocks_yesterday` - Yesterday's signed blocks
- `signed_blocks_yesterday_amount` - Yesterday's signed blocks count
- `sovereign_addr` - Sovereign address (if applicable)
- `sovereign_reward_wallet_address` - Sovereign wallet address (if applicable)
- `sovereign_tax` - Sovereign tax rate (if applicable)
- `sovereign_wallet_all_sums_daily` - Sum of sovereign rewards per day
- `sovereign_wallet_balance` - Sovereign wallet balance
- `sovereign_wallet_biggest_reward` - Biggest sovereign reward received
- `sovereign_wallet_daily_rewards` - Daily sovereign rewards data
- `sovereign_wallet_earliest_reward` - Earliest sovereign reward received
- `sovereign_wallet_latest_reward` - Latest sovereign reward received
- `sovereign_wallet_smallest_reward` - Smallest sovereign reward received
- `sovereign_wallet_today_rewards` - Today's sovereign rewards
- `sovereign_wallet_total_rewards` - Total sovereign rewards received
- `sovereign_wallet_yesterday_rewards` - Yesterday's sovereign rewards
- `stake_value` - Validator stake amount
- `token_price` - Current token price
- `tx_hash` - Staking transaction hash

### Response Format

All responses follow this structure:

**Success:**
```json
{
  "request_timestamp": "2025-10-05T14:30:00.123456+00:00",
  "status": "ok",
  "data": {
    "action_name": "value",
    ...
  }
}
```

**Error:**
```json
{
  "request_timestamp": "2025-10-05T14:30:00.123456+00:00",
  "status": "error",
  "message": "Error description"
}
```

### Example Responses

**System data:**
```json
{
  "request_timestamp": "2025-10-05T14:30:00.123456+00:00",
  "status": "ok",
  "data": {
    "active_networks": ["Backbone"],
    "current_node_version": "5.5.0",
    "node_cpu_usage": 1.25,
    "node_memory_usage": 6144.33,
    "system_uptime": 1565680.06
  }
}
```

**Network data:**
```json
{
  "request_timestamp": "2025-10-05T14:30:00.123456+00:00",
  "status": "ok",
  "data": {
    "Backbone": {
      "network_status": {
        "synced": true,
        "current_state": "NET_STATE_ONLINE"
      },
      "reward_wallet_balance": 1234.56,
      "autocollect_status": {
        "active": true,
        "rewards": 10.5
      }
    }
  }
}
```

## File Structure

```
cellframe_masternode_inspector/
├── cellframe_masternode_inspector.py  # Main plugin entry point
├── manifest.json                      # Plugin metadata
├── requirements.txt                   # Python dependencies
├── install.py                         # Automated installer script
├── LICENSE                            # GPL-3.0 license
├── README.md                          # This file
│
├── config.py                          # Configuration loader
├── handlers.py                        # HTTP request handlers
├── actions.py                         # System and network action dispatcher
├── response_helpers.py                # HTTP response builders
│
├── system_requests.py                 # System information collector
├── masternode_helpers.py              # Masternode data retrieval
├── cacher.py                          # Network data caching system
├── updater.py                         # Background cache updater
│
├── utils.py                           # Utility functions
├── parsers.py                         # Data parsers
├── threadpool.py                      # Thread pool manager
└── logconfig.py                       # Logging configuration
```

## Web UI Integration

For a modern web-based dashboard interface, check out the companion project:

**Cellframe Masternode Inspector UI**
- **Free Web Interface**: https://cellframemasternodeinspector.pqcc.fi (Use it to monitor your own nodes for free)
- Repository: https://github.com/hyttmi/cellframe-masternode-inspector-ui
- Features: Multi-node management, real-time monitoring, interactive charts
- Self-hosting: Simple static HTML/JS/CSS - no build required

## Development

### Testing the API

**Quick test:**
```bash
# Get your token
TOKEN=$(cat /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/token.txt)

# Find your node's HTTP port (from [server] section)
PORT=$(grep -A 10 "\[server\]" /opt/cellframe-node/etc/cellframe-node.cfg | grep "listen_address" | grep -oP ':\K\d+')

# Test system endpoint
curl -H "X-API-Key: $TOKEN" "http://localhost:$PORT/mninspector?action=help"

# Test network endpoint
curl -H "X-API-Key: $TOKEN" "http://localhost:$PORT/mninspector?network=Backbone&network_action=help"
```

### Debugging

Enable debug logging in configuration:
```ini
[mninspector]
debug=true
```

View logs:
```bash
tail -f /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/mninspector.log
```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

## Troubleshooting

### Plugin not loading

**Check minimum node version:**
```bash
cellframe-node-cli version
```
Ensure version is 5.5.0 or higher.

**Check logs:**
```bash
tail -100 /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/mninspector.log
```

**Verify masternode configuration:**
Ensure at least one network is configured as a masternode in your Cellframe node configuration.

### API not responding

**Verify plugin is running:**
```bash
tail -50 /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/mninspector.log
```

**Check plugin URL:**
Verify the `plugin_url` in your configuration matches the URL you're accessing.

**Find your node's HTTP port:**
```bash
grep -A 10 "\[server\]" /opt/cellframe-node/etc/cellframe-node.cfg | grep "listen_address"
```

**Test locally:**
```bash
curl -v http://localhost:<NODE_PORT>/mninspector?action=help
```

### Authentication errors

**Verify token:**
```bash
cat /opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector/token.txt
```

**Check token in request:**
Ensure you're using the exact token from the file, with no extra whitespace.

### Cache not updating

**Check block count threshold:**
If your network has fewer blocks than `block_count_threshold`, caching won't start.

**Cache refresh timing:**
The cache automatically refreshes when there are enough new blocks since the last update. If the cache isn't updating, check that enough new blocks have been created (based on `block_count_threshold` setting).

## Performance Tuning

### Cache Settings

**Increase historical data:**
```ini
days_cutoff=90  # Store 90 days instead of 20
```

**Reduce cache frequency** (for slower nodes):
```ini
block_count_threshold=50  # Wait for more blocks before caching
```

### Response Compression

**Disable compression** (if bandwidth is not an issue):
```ini
compress_responses=false
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues, feature requests, or questions:
- Open an issue on [GitHub Issues](https://github.com/hyttmi/cellframe_masternode_inspector/issues)
- Msg me on Telegram @CELLgainz

## Acknowledgments

- Built for the Cellframe Network community
- Powered by [Cellframe](https://cellframe.net/)
- Uses [pycfhelpers](https://gitlab.demlabs.net/cellframe/python-cellframe-modules/pycfhelpers)

---

**Current Version**: 1.03
**Last Updated**: October 6, 2025
**Author**: Mika Hyttinen (@CELLgainz)
**Repository**: https://github.com/hyttmi/cellframe_masternode_inspector
