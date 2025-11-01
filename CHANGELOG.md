# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite for Evolution API MCP tool (tests/tools/test_evolution_api.py)


### Fixed
- **CRITICAL**: Spark `sync_workflow` now includes required `source_url` parameter
- Spark `list_remote_workflows` now accepts `simplified` parameter
- Spark `list_sources` now accepts `status` filter parameter
- MseeP.ai security badge repositioned to README footer

### Changed
- Spark MCP tool now achieves 100% API coverage (23/23 endpoints)
- Improved error handling and validation across all Spark tools
- Enhanced test coverage with comprehensive error path testing

## [0.9.7] - 2025-10-17

### Added
- Initial Spark MCP tool with 17/25 endpoints covered
- Complete Evolution API integration for WhatsApp automation
- Genie universal MCP orchestrator
- Automagik suite integration (Spark, Hive, Forge, Omni)
- Dynamic OpenAPI agent generation
- Multiple transport support (stdio, SSE, HTTP)
- Self-learning capabilities with memory
- Markdown output processing
- Plugin architecture with auto-discovery

### Documentation
- Comprehensive README with usage examples
- Tool creation guide
- Contributing guidelines
- MCP client configuration examples

## [0.9.6] - 2025-10-15

### Added
- Initial public release
- Core MCP framework
- Basic tool infrastructure

[Unreleased]: https://github.com/namastexlabs/automagik-tools/compare/v0.9.7...HEAD
[0.9.7]: https://github.com/namastexlabs/automagik-tools/compare/v0.9.6...v0.9.7
[0.9.6]: https://github.com/namastexlabs/automagik-tools/releases/tag/v0.9.6
