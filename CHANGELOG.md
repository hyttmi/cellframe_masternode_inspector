# Changelog

## 1.10

### Changed
- The cacher now forces a refresh if more than 3600 seconds has passed since the last successful update, even when the block difference threshold is not met, however if block difference is 0, cacher will skip the current network.
- Sleep time between caching was changed from 10s to 60s.