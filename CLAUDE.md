# Minecraft Docker Manager Library - Development Guide

## What This Library Is

Python library (v0.3.1) for managing Minecraft servers using Docker containers. Provides comprehensive server lifecycle management, Docker Compose configuration handling, and real-time resource monitoring via cgroup v2 interfaces.

## Core Functionality

- **Server Lifecycle Management**: Complete status tracking from REMOVED → EXISTS → CREATED → STARTING → HEALTHY
- **Docker Integration**: Docker Compose orchestration for Minecraft server containers
- **Resource Monitoring**: Real-time CPU, memory, disk I/O, and network monitoring via cgroup v2
- **Configuration Management**: Strongly-typed Minecraft Docker Compose file handling with Pydantic validation
- **Async Operations**: Full async/await patterns for all I/O operations and Docker commands

## Tech Stack

- **Language**: Python 3.12+ with Poetry dependency management
- **Container Platform**: Docker Engine + Docker Compose integration
- **Async Framework**: asyncio with comprehensive async/await patterns throughout codebase
- **File Operations**: aiofiles v24.1.0 for async file I/O operations
- **Data Validation**: Pydantic v2.11.7 + pydantic-settings v2.10.1 for configuration management
- **YAML Processing**: PyYAML v6.0.2 for Docker Compose file parsing and generation
- **System Monitoring**: psutil v7.0.0 for system and process metrics
- **Utilities**: asyncer v0.0.8 for additional async helper functions
- **Testing**: pytest v8.3.3 + pytest-asyncio v0.24.0 + pytest-cov v5.0.0 for comprehensive async testing

## Development Commands

### Environment Setup
```bash
poetry install     # Install dependencies and create virtual environment
poetry run {command} # run command in venv
```

### Testing Strategy
```bash
# Run specific test modules for faster iteration
poetry run pytest tests/test_instance.py
poetry run pytest tests/test_compose_file.py
poetry run pytest tests/test_monitoring.py
...
# or test with specific test functions

# Generate comprehensive coverage reports  
poetry run pytest
```

### Important Testing Guidelines

**AVOID These Slow Tests During Development:**
- `test_integration` in `test_integration.py` (full Docker workflow - very slow)
- `test_server_status_lifecycle` in `test_instance.py` (creates real containers - slow)

**Monitoring Tests (Controlled Timing):**
- `test_monitoring.py` takes ~1.3 minutes with session-scoped fixture
- Creates one Minecraft server per test session, reused across all monitoring tests
- Includes comprehensive real container resource monitoring validation

**Quick Development Testing:**
```bash
# Test specific monitoring APIs individually for rapid feedback
poetry run pytest tests/test_monitoring.py::test_get_container_id -v
poetry run pytest tests/test_monitoring.py::test_get_memory_usage -v
```

## Architecture Overview

### Core Classes

**DockerMCManager**: 
- Main entry point for managing multiple Minecraft servers
- Handles server discovery and batch operations across server directory

**MCInstance**:
- Represents individual Minecraft server with complete lifecycle management
- Provides comprehensive monitoring APIs for resource usage
- Manages Docker Compose operations for single server

**MCComposeFile**: 
- Strongly-typed wrapper for Minecraft-specific Docker Compose configurations
- Extends generic ComposeFile with Minecraft server validation
- Provides Pydantic-based configuration validation and defaults

**ComposeManager**: 
- Handles Docker Compose operations (up, down, build, logs, status)
- Manages container lifecycle and dependency resolution

**DockerManager**: 
- Low-level Docker container operations and introspection
- Provides direct container management capabilities

### Server Status Lifecycle

```
REMOVED → EXISTS → CREATED → STARTING → HEALTHY
                                     ↗ RUNNING (fallback)
```

**Status Definitions:**
1. **REMOVED**: Server directory/configuration doesn't exist
2. **EXISTS**: Server directory exists, no Docker container created  
3. **CREATED**: Docker container created but not running
4. **STARTING**: Container running but not yet healthy (health checks failing)
5. **HEALTHY**: Container running and passing all health checks
6. **RUNNING**: Container operational but health status unknown (fallback state)

### Comprehensive Resource Monitoring

**Available Monitoring APIs** (via MCInstance):
- `get_container_id()`: Full Docker container ID for direct Docker API access
- `get_pid()`: Container main process ID for system-level monitoring  
- `get_memory_usage()`: Current memory usage in bytes (via cgroup v2)
- `get_cpu_percentage()`: CPU usage percentage (requires two calls over time interval)
- `get_disk_io()`: Disk I/O read/write statistics from block devices
- `get_network_io()`: Network I/O receive/transmit statistics from container interfaces

**Monitoring Implementation:**
- Uses cgroup v2 interfaces for accurate container-level metrics
- Handles both rootful and rootless Docker configurations
- Provides real-time metrics without container inspection overhead
- Error handling for missing cgroup interfaces or permissions

## Development Patterns

### Async/Await Conventions
```python
# All public APIs are async - no sync alternatives
async def get_server_status(self) -> MCServerStatus:
    # File operations use aiofiles
    async with aiofiles.open(self.compose_file_path) as f:
        content = await f.read()
    
    # Shell commands use async subprocess
    result = await asyncio.subprocess.run([...])
    
    # Use asyncio.gather for concurrent operations
    statuses = await asyncio.gather(*[
        server.get_status() for server in servers
    ])
```

### File Operations Patterns
```python
# Always use aiofiles for file I/O
import aiofiles
from pathlib import Path

async def read_compose_file(self) -> str:
    async with aiofiles.open(self.compose_file_path, 'r') as f:
        return await f.read()

# Use pathlib.Path for path handling
compose_path = Path(server_dir) / "docker-compose.yml"
if await aiofiles.ospath.exists(compose_path):
    # Handle file exists
```

### Docker Integration Patterns
```python
# Container naming convention
container_name = f"mc-{server_name}"

# Docker Compose file expectations
# - docker-compose.yml or docker-compose.yaml
# - Uses itzg/minecraft-server image by default
# - Container healthcheck required for HEALTHY status

# Error handling for Docker operations
try:
    await self.compose_manager.up()
except ComposeError as e:
    logger.error(f"Failed to start server: {e}")
    raise
```

## Project Structure

```
minecraft_docker_manager_lib/
├── __init__.py              # Public API exports with __all__
├── manager.py               # DockerMCManager main class  
├── instance.py              # MCInstance + MCServerStatus/Info enums
├── mc_compose_file.py       # Minecraft-specific compose file handling
├── utils.py                 # Utility functions and helpers
└── docker/                  # Docker-specific implementation modules
    ├── manager.py           # ComposeManager + DockerManager classes
    ├── compose_file.py      # Generic ComposeFile Pydantic models
    ├── cgroup.py            # Container resource monitoring via cgroup v2
    └── network.py           # Network statistics collection

tests/                       # Comprehensive test suite
├── test_instance.py         # MCInstance functionality (includes slow lifecycle test)
├── test_compose_file.py     # Compose file parsing and validation
├── test_monitoring.py       # Resource monitoring with real containers (~1.3min)
├── test_integration.py      # Full integration tests (AVOID - very slow)
└── test_utils.py            # Utility function tests
```

## Configuration and Integration

### Docker Requirements
- Docker Engine (rootful or rootless)
- Docker Compose v2 (docker-compose or docker compose)
- Proper permissions for Docker socket access
- cgroup v2 enabled for resource monitoring

### Server Directory Structure
```
server_name/
├── docker-compose.yml       # Required: Docker Compose configuration
├── data/                    # Minecraft server data volume
├── config/                  # Server configuration files
└── logs/                    # Server log files
```

### Example Integration (from MC Admin Backend)
```python
from minecraft_docker_manager_lib import DockerMCManager, MCInstance

# Initialize manager with servers directory
manager = DockerMCManager("/path/to/minecraft/servers")

# Get all server instances
servers = await manager.get_all_server_names()

# Work with individual server
instance = manager.get_instance("my_server")
status = await instance.get_status()
memory_usage = await instance.get_memory_usage()
```

## Testing Architecture

### Test Categories
1. **Unit Tests**: Fast tests for individual components (majority of test suite)
2. **Integration Tests**: Full Docker workflow tests (marked for exclusion during development)
3. **Monitoring Tests**: Real container tests with session-scoped fixtures for efficiency

### Session-Scoped Test Fixtures
```python
# tests/test_monitoring.py uses session scope for expensive setup
@pytest.fixture(scope="session")
async def minecraft_server_instance():
    # Creates one Minecraft server container for entire test session
    # Reused across all monitoring tests to minimize overhead
    # Automatically cleaned up after all tests complete
```

### Mock Testing Patterns
- Unit tests mock Docker operations for speed and isolation
- Integration tests use real Docker containers for validation
- Monitoring tests use real containers but share instances for efficiency

## External Documentation

**IMPORTANT**: Always use Context7 for external library documentation to ensure accuracy and current information.

**Key External Dependencies:**
- **Docker SDK for Python**: Container management and API access
- **Pydantic**: Data validation and settings management patterns
- **AsyncIO**: Advanced async/await patterns and best practices
- **pytest-asyncio**: Async testing patterns and fixtures
- **psutil**: System monitoring and process management

Use `mcp__context7__resolve-library-id` followed by `mcp__context7__get-library-docs` for up-to-date documentation.

## Performance Considerations

- **Monitoring Tests**: Session-scoped fixtures reduce test time from ~10min to ~1.3min
- **Integration Tests**: Full Docker lifecycle tests are comprehensive but time-consuming
- **Resource Monitoring**: cgroup v2 interfaces provide efficient real-time metrics
- **Async Operations**: Concurrent operations using asyncio.gather for batch processing
- **Container Cleanup**: Proper cleanup ensures no resource leaks during testing

## Update Instructions

**CRITICAL**: When adding new functionality, dependencies, or changing architecture:

1. **New Dependencies**: Update `pyproject.toml` and document integration patterns here
2. **New Monitoring APIs**: Add to MCInstance class and document resource interfaces  
3. **Docker Changes**: Update container management patterns and requirements
4. **Testing Changes**: Document new test categories and performance considerations
5. **API Changes**: Update public exports in `__init__.py` and maintain backward compatibility
6. **Configuration Changes**: Update MCComposeFile validation and default handling

**Examples Requiring Updates:**
- New Docker Compose features or schema changes
- Additional resource monitoring capabilities  
- New container lifecycle states or management patterns
- Changes to async/await patterns or error handling
- New external library integrations

This CLAUDE.md file helps future sessions understand the library's architecture, testing strategy, and integration patterns. Keep it updated with significant changes to maintain development efficiency.