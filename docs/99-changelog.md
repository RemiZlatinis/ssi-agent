# Changelog

All notable changes to the SSI Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive documentation in `docs/` folder
- Service script block structure standardization
- Best practices guide for writing service scripts

### Changed

- Documentation structure reorganized

---

## [1.0.0] - Initial Release

### Added

- Agent daemon with WebSocket connection to backend
- CLI tool (`ssi`) for managing services
- Service script parsing and validation
- Systemd timer-based scheduling
- Installation script with uninstall support
- Registration flow with 6-digit code
- Log file watching and status reporting

### Features

- `ssi add` - Add new service scripts
- `ssi remove` - Remove services
- `ssi list` - List all services
- `ssi status` - View service status
- `ssi run` - Manually run a service
- `ssi register` - Register with backend
- `ssi unregister` - Unregister agent
- `ssi whoami` - Display agent info
- `ssi set-backend` - Configure backend URL

---

## Version History Format

When adding new versions, use this format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added

- New features

### Changed

- Changes to existing functionality

### Deprecated

- Features to be removed in future

### Removed

- Removed features

### Fixed

- Bug fixes

### Security

- Security-related changes
```
