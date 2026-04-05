# Changelog

## 1.15

### Changed
- Block cache now fetches incrementally using `-from_date` instead of pulling entire chain history every cycle.
- New blocks are merged with existing cache and deduplicated by block hash.
- Added `orjson` as requirement. ~7.5x faster in parsing transaction data.