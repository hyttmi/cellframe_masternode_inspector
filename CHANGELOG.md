# Changelog

## 1.12

### Changed
- Now adds all signed blocks, first signed blocks and all reward transactions to cache.
- Timeout for fetching changelog (10 seconds).
- Cache files are now written in compact JSON format to reduce disk usage.
- Simplified block parsing to a single-pass parser call per block dataset in cacher.
- Simplified reward transaction parsing to a single-pass parser call per transaction dataset in cacher.