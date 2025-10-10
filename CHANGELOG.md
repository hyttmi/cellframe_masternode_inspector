# Changelog

## 1.05

### Added
- Changelog is now also passed to `updater` from Github.

### Fixed
- Allow HTTP server to send response when update is initiated by passing update process to a threadpool.

### Changed
- Node minimum version is now 5.5.1
- Sleeping between cache refresh cycles changed from 60 seconds to 10 seconds.