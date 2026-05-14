# Changelog

## 1.51

### Added

- Introduced `exceptions.py` module with dedicated exception classes (`UnsupportedPlatformError`, `UnsupportedNodeVersionError`, `ConfigurationError`, `UpdateError`, `RequestError`)
- Added `plugin_logs` system action to fetch the last 5000 log lines from an in-memory debug ring buffer via GET request.

### Changed

- Replaced all generic `Exception` raises with specific `CMIException` subclasses across `cellframe_masternode_inspector.py`, `utils.py`, and `updater.py`
- Removed non-Linux fallback in `utils.py`, now raises `UnsupportedPlatformError` instead
