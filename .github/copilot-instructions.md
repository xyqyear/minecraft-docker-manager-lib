# Minecraft Docker Manager Library - Development Instructions

## Project Overview

This project is a Python library for managing Minecraft servers using Docker containers. It provides tools to:
- Start, stop, and monitor Minecraft server containers
- Manage Docker Compose configurations for Minecraft servers
- Monitor server status, health, and resource usage (memory, CPU, I/O, network)
- Handle server lifecycle management with various statuses (REMOVED, EXISTS, CREATED, STARTING, HEALTHY)
- Comprehensive monitoring for container resource tracking

## Technologies and Libraries

### Core Technologies
- **Python**: ^3.12 (primary language)
- **Docker**: Container management via Docker Compose
- **Async/Await**: Heavy use of asyncio for async operations
- **Poetry**: Dependency management and packaging

### Key Dependencies
- **aiofiles** (^24.1.0): Async file operations
- **pydantic** (^2.11.7): Data validation and settings management
- **pydantic-settings** (^2.10.1): Configuration management
- **pyyaml** (^6.0.2): YAML parsing for Docker Compose files
- **psutil** (^7.0.0): System and process monitoring
- **asyncer** (^0.0.8): Async utilities

### Development Dependencies
- **pytest** (^8.3.3): Testing framework
- **pytest-asyncio** (^0.24.0): Async test support
- **pytest-cov** (^5.0.0): Coverage reporting
- **coverage** (^7.6.3): Code coverage analysis
- **datamodel-code-generator**: Code generation from schemas

## Project Structure

```
minecraft_docker_manager_lib/           # Main library package
├── __init__.py                        # Public API exports
├── manager.py                         # DockerMCManager main class
├── instance.py                        # MCInstance for individual servers
├── mc_compose_file.py                 # Minecraft-specific compose file handling
├── utils.py                          # Utility functions
└── docker/                           # Docker-specific modules
    ├── manager.py                    # Docker and Compose management
    ├── compose_file.py               # Generic compose file models
    ├── cgroup.py                     # Container resource monitoring
    └── network.py                    # Network statistics

tests/                                # Test suite
├── test_*.py                         # Unit tests
├── test_monitoring.py                # Comprehensive monitoring tests
├── test_integration.py               # Integration tests (DO NOT RUN)
└── test_utils.py                     # Test utilities

example_server_dir/                   # Example server configurations
```

## Build and Development Commands

### Environment Setup
1. **Always ensure Poetry is installed** and run these commands in order:
```bash
poetry install                        # Install dependencies
poetry shell                          # Activate virtual environment
```

### Testing
```bash
# Run all tests with coverage (excludes slow integration tests)
poetry run pytest

# Run specific test files
poetry run pytest tests/test_instance.py
poetry run pytest tests/test_compose_file.py

# Generate coverage reports
poetry run pytest --cov=minecraft_docker_manager_lib --cov-report=html:cov_html --cov-report=xml:cov.xml
```

**IMPORTANT**: Do NOT run these slow tests during development:
- `test_integration` in `test_integration.py` 
- `test_server_status_lifecycle` in `test_instance.py`

For monitoring tests:
- `test_monitoring.py` (takes ~1.3 minutes for full suite with session-scoped fixture)
- Uses session-scoped fixture to create Minecraft server only once, significantly reducing test time

### Quick Testing
For rapid development, run individual monitoring tests:
```bash
# Test specific monitoring APIs individually
poetry run pytest tests/test_monitoring.py::test_get_container_id -v
poetry run pytest tests/test_monitoring.py::test_get_memory_usage -v
```

## Architecture and Key Components

### Main Classes
- **DockerMCManager**: Main entry point for managing multiple Minecraft servers
- **MCInstance**: Represents a single Minecraft server instance
- **MCComposeFile**: Strongly-typed wrapper for Minecraft Docker Compose configurations
- **ComposeManager**: Handles Docker Compose operations
- **DockerManager**: Low-level Docker container operations

### Server Status Lifecycle
Servers follow this status progression:
1. **REMOVED**: Server doesn't exist
2. **EXISTS**: Server directory exists, no container
3. **CREATED**: Container created but not running
4. **STARTING**: Container running but not healthy
5. **HEALTHY**: Container running and healthy
And this special case:
6. **RUNNING**: Container is operational but in unknown state.

### Resource Monitoring
The library includes comprehensive monitoring for:
- **Memory usage**: via cgroup v2 statistics
- **CPU percentage**: Calculated from cgroup v2 CPU usage over time
- **I/O statistics**: Block device read/write metrics  
- **Network statistics**: Container network traffic
- **Container health**: Docker health checks

### Monitoring APIs
MCInstance provides these monitoring methods:
- `get_container_id()`: Get full Docker container ID
- `get_pid()`: Get container main process ID
- `get_memory_usage()`: Get current memory usage in bytes
- `get_cpu_percentage()`: Get CPU usage percentage (requires two calls over time)
- `get_disk_io()`: Get disk I/O read/write statistics
- `get_network_io()`: Get network I/O receive/transmit statistics

### Async Patterns
- All I/O operations are async (file operations, shell commands, Docker operations)
- Uses `asyncio.gather()` for concurrent operations
- Extensive use of `async`/`await` throughout the codebase

## Development Guidelines

### File Operations
- Use `aiofiles` for all file I/O operations
- Path handling with `pathlib.Path`
- Async context managers for file operations

### Docker Integration
- Docker Compose files in YAML format (`docker-compose.yml` or `docker-compose.yaml`)
- Container names follow pattern: `mc-{server_name}`
- Uses `itzg/minecraft-server` Docker image

### Error Handling
- Proper exception handling for Docker operations
- File not found errors for missing compose files
- Shell command execution with error capture

### Testing Patterns
- Async test functions with `@pytest.mark.asyncio`
- Teardown fixtures for cleaning up test containers
- Session-scoped fixtures for expensive operations (creating Minecraft servers)
- Mock Docker operations for unit tests
- Integration tests for full Docker workflow (avoid during development)
- Comprehensive monitoring test suite with real Minecraft servers

## External Documentation

For external library documentation, always use the Context7 tool to get up-to-date documentation and examples.

## Important Notes

### Performance Considerations
- The `test_server_status_lifecycle` test in `test_instance.py` is comprehensive but slow
- The `test_integration` test in `test_integration.py` requires full Docker setup
- The `test_monitoring.py` uses session-scoped fixtures for efficiency (~1.3 minutes)
- Skip slow tests during rapid development cycles

### Docker Requirements
- Requires Docker and Docker Compose to be installed
- Tests create and destroy actual Docker containers
- Uses `/tmp/test_temp_dir` for test server directories

## Instruction File Maintenance

**CRITICAL**: When you add new technologies, libraries, or significantly change the project structure, update this instruction file to keep future sessions informed. This includes:
- New dependencies in `pyproject.toml`
- New architectural components or modules
- Changes to testing patterns or build processes
- New external integrations or APIs
- Modified development workflows

Always use the Context7 tool for external library documentation to ensure accuracy and up-to-date information.
