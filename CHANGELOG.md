# Changelog

## Unreleased

- **License.** The Outer-Void Proprietary License applies from 2026-10-25
  (Copyright (c) 2026 Outer-Void / Justadudeinspace (JADIS); contact outervoid.blux@gmail.com, fallback
  theoutervoid@outlook.com). Package metadata declares the matching `LicenseRef`. Copies and releases
  obtained before that date keep the MIT License.

## [2.0.0]

A rebuild: GOD is now the BLUX ecosystem's discovery layer. See docs/AUDIT-1.0.md.

### Added
- `capabilities` (capability.discover), `capability` (capability.describe), `project` (project.describe),
  `compat` (version compatibility lookup), `commands` (command.discover), `index` (local registry index),
  `check`, `version`; `--json` everywhere; exit codes 0-3.
- `.blux/` is read only through blux-sdk (Contract v1): malformed manifests become problem records with the
  SDK's error code, never crashes.
- Duplicate detection (project ids and capability ids across projects).
- Index cache with stat-signature invalidation and full rebuild on GOD/SDK version change.
- semver ranges and contract-version negotiation for compatibility lookup.
- BLUX adapter (`god blux-capability ID`, ADR-0009) and GOD's own `.blux/` (`role: integrated`).

### Removed
- `build`, `search`, `info`: they executed every program on PATH with help and version flags.
- `stats` and its name-list "risk levels"; `blux` soft routes (routing is BLUX's job); `completion`.
- typer, rich and click dependencies; `install_deps.sh` (piped from curl in the README), `activate_god.sh`,
  `scripts/publish.sh`, `requirements*.txt`, `MANIFEST.in`, the top-level `src/__init__.py`.

### Changed
- Python 3.11+. Runtime dependency: blux-sdk only.

## [1.0.0] - 2025-11-10

### Added
- Initial release of GOD CLI
- Global help indexing from PATH executables
- Risk assessment (LOW/MEDIUM/HIGH/CRITICAL)
- BLUX soft routes integration
- Multiple output formats: Markdown, JSON, HTML, Console
- Cross-platform support (Windows, macOS, Linux)
- Parallel processing with ThreadPoolExecutor
- Search & stats commands
- Shell completion support
- Comprehensive test suite

### Professional Improvements
- **Security**: Enhanced security audit with critical risk level
- **Performance**: Parallel command processing
- **Error Handling**: Comprehensive logging and graceful recovery
- **Windows Support**: Improved UTF-8 handling
- **Code Quality**: Professional structure with type hints
- **Testing**: Comprehensive test coverage with pytest
## [1.0.1] - 2025-11-10

### Fixed
- Makefile installation issues
- Test suite failures due to missing __main__.py
- Version import errors
- Package structure improvements

### Improved
- Development workflow with better Makefile targets
- Test reliability and error handling
- Documentation and project structure

## [1.0.1] - 2025-11-10

### Added
- One-line installers using curl and wget
- Improved installation documentation
- Better virtual environment handling

### Fixed
- Makefile installation issues
- Test suite failures due to missing __main__.py
- Version import errors
- Package structure improvements

### Improved
- Development workflow with better Makefile targets
- Test reliability and error handling
- Installation script robustness for remote execution
