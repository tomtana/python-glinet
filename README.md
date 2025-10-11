# python-glinet

A Python 3 client for interacting with the GL.iNet router's LuCI API, providing seamless access to router functionalities.

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/tomtana/python-glinet/Python%20package)](https://github.com/tomtana/python-glinet/actions/workflows/python-package.yml)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/tomtana/python-glinet/Deploy%20static%20content%20to%20Pages?label=docs)](https://tomtana.github.io/python-glinet/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-glinet)](https://pypi.org/project/python-glinet)
[![PyPI](https://img.shields.io/pypi/v/python-glinet)](https://pypi.org/project/python-glinet)
[![Code Coverage](https://codecov.io/gh/tomtana/python-glinet/branch/main/graph/badge.svg?token=976L8ESH8K)](https://codecov.io/gh/tomtana/python-glinet)

## Summary

`python-glinet` is a Python 3 client designed to interact with the GL.iNet router's LuCI API (firmware version 4.x). It offers dynamic method creation based on the API's online documentation, intuitive object-based response handling, and a configurable background thread to maintain active connections. The library is ideal for developers seeking programmatic control over GL.iNet routers, with features like cached API descriptions and secure login persistence. For optimal exploration, use an IPython shell to leverage code completion and docstrings.

## Features

- **Full API Access**: Provides complete access to the GL.iNet LuCI API (firmware 4.x).
- **Dynamic Method Creation**: Automatically generates API methods with docstrings derived from official documentation.
- **Object-Oriented Responses**: API responses are converted into objects for intuitive attribute access via dot notation.
- **Connection Management**: Includes a background thread to keep sessions alive and cached login credentials for efficiency.
- **IPython Integration**: Optimized for interactive exploration in IPython shells with code completion support.

**Note**: 
- Only firmware versions 4.x are supported due to GL.iNet's shift from REST to JSON-RPC.
- Official API documentation is no longer available; this library uses a snapshot from the [Internet Archive](https://web.archive.org/web/20230909030858/https://dev.gl-inet.com/router-4.x-api/).

## Installation

### Using pip

Install the package via pip (recommended within a virtual environment):

```bash
pip install python-glinet
```

### From Source

Clone the repository and install locally:

```bash
git clone https://github.com/tomtana/python-glinet.git
cd python-glinet
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

For more on Python virtual environments, see the [official documentation](https://docs.python.org/3/tutorial/venv.html).

## Getting Started

The core of `python-glinet` is the `GlInet` class, which handles authentication, session management, and API communication. If your router's default settings (e.g., IP address or username) have been modified, pass them as parameters to the `GlInet` constructor. Refer to the [GlInet class documentation](https://tomtana.github.io/python-glinet/glinet.html) for details.

### Basic Usage

```python
from pyglinet import GlInet

# Initialize the client
glinet = GlInet()

# Log in (prompts for credentials if not persisted)
glinet.login()
```

**Security Note**: Avoid passing passwords directly in the constructor. The `login()` method will attempt to load credentials from persistence or prompt for them securely.

### Exploring the API

Use an IPython shell for the best experience, leveraging code completion and dynamic docstrings.

1. **Generate the API Client**:
   ```python
   api_client = glinet.get_api_client()
   ```

2. **List Functional Groups**:
   ```python
   api_client
   ```
   Displays available groups, e.g., `wg_client`, `firewall`, `system`.

3. **Explore Methods**:
   ```python
   api_client.wg_client
   ```
   Lists methods like `get_config_list`, `set_config`, etc.

4. **View Method Parameters**:
   ```python
   api_client.wg_client.set_config
   ```
   Shows required and optional parameters with descriptions.

5. **Access Docstrings**:
   ```python
   api_client.wg_client.set_config?
   ```
   Provides detailed parameter information and example requests/responses.

6. **Make API Calls**:
   ```python
   api_client.wg_client.get_all_config_list()
   ```
   Returns structured, object-oriented responses accessible via dot notation.

### Direct API Requests

Bypass the dynamic client to make raw API calls:

```python
glinet.request("call", ["adguardhome", "get_config"])
```

This is equivalent to `api_client.adguardhome.get_config()` but includes the full response body.

## Roadmap

### Version 1.0.0
- [x] Dynamic docstrings for API calls
- [x] Pip-compliant package creation
- [x] Publish to PyPI
- [x] Add unit tests
- [x] Enhance documentation
- [x] Increase test coverage
- [x] Replace `crypt` dependency for Windows compatibility
- [ ] Add terminal wrapper for execution

### Version 2.0.0
- [ ] Add asyncio support
- [ ] Additional features (TBD)

## Contributing

Contributions are welcome! Please submit issues or pull requests on the [GitHub repository](https://github.com/tomtana/python-glinet). Ensure changes are tested and align with the project's roadmap.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/tomtana/python-glinet/blob/main/LICENSE) file for details.