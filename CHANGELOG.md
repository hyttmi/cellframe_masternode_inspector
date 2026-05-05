# Changelog

## 1.51

### Added

- Introduced `exceptions.py` module with dedicated exception classes (`UnsupportedPlatformError`, `UnsupportedNodeVersionError`, `ConfigurationError`, `UpdateError`, `RequestError`)

### Changed

- Replaced all generic `Exception` raises with specific `CMIException` subclasses across `cellframe_masternode_inspector.py`, `utils.py`, and `updater.py`
- Removed non-Linux fallback in `utils.py`, now raises `UnsupportedPlatformError` instead
