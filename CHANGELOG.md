# Changelog

## 1.05

### Fixed
- Allow HTTP server to send response when update is initiated by passing update process to a threapool.

## 1.04

### Added
- Option to update the plugin via GET request (`update_plugin`) if update is available.

### Removed
- `sovereign_address` from network actions if node is not a sovereign one.

### Changed
- `AUTOUPDATE` is now off by default.
- Improved and simplified network action handling a lot.
