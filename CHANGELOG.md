# Changelog

## 1.15

### Changed
- Block cache now fetches incrementally using `-from_date` instead of pulling entire chain history every cycle.
- New blocks are merged with existing cache and deduplicated by block hash.
- Token price and wallet balances are now fetched live per request with a 5-minute TTL cache instead of being tied to the block-dependent cache cycle.
- All JSON serialization now uses `orjson` with fallback to stdlib `json` via centralized `jsonlib` module.
- Updater now checks if the node version is compatible with the plugin.