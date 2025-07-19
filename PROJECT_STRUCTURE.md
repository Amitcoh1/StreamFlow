# StreamFlow Project Structure

## 🚀 New PyPI Package Structure

After reorganization for PyPI publication, the project now has both the **original development structure** and the **new package structure**:

```
📦 StreamFlow Root Directory
├── 🎯 streamflow/                    # NEW: Main Python package for PyPI
│   ├── __init__.py                   # Package exports and metadata
│   ├── cli.py                        # Command-line interface
│   ├── shared/                       # Shared utilities and models
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration management
│   │   ├── database.py               # Database utilities
│   │   ├── messaging.py              # Message broker utilities
│   │   └── models.py                 # Data models (Event, AlertRule, etc.)
│   └── services/                     # Microservices modules
│       ├── __init__.py
│       ├── alerting/                 # Alert management service
│       │   ├── __init__.py
│       │   └── main.py
│       ├── analytics/                # Analytics processing service
│       │   ├── __init__.py
│       │   └── main.py
│       ├── dashboard/                # Dashboard API service
│       │   ├── __init__.py
│       │   └── main.py
│       ├── ingestion/                # Data ingestion service
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── main_refactored.py
│       └── storage/                  # Data storage service
│           ├── __init__.py
│           └── main.py
├── 📦 dist/                          # Built packages for PyPI
│   ├── streamflow-1.0.0-py3-none-any.whl    # Wheel distribution
│   └── streamflow-1.0.0.tar.gz              # Source distribution
├── 📋 Configuration Files
│   ├── pyproject.toml                # Modern Python project config
│   ├── setup.py                      # Legacy setup file
│   ├── requirements.txt              # Dependencies
│   └── MANIFEST.in                   # Package manifest
├── 📚 Documentation
│   ├── README.md                     # Main project documentation
│   ├── PYPI_PUBLISHING_GUIDE.md     # NEW: PyPI publishing guide
│   ├── GETTING_STARTED.md           # Getting started guide
│   ├── CHANGELOG.md                 # Version history
│   ├── CONTRIBUTING.md              # Contribution guidelines
│   ├── PROJECT_SUMMARY.md           # Project overview
│   └── docs/
│       └── API.md                    # API documentation
├── 🚀 Deployment & Scripts
│   ├── publish_to_pypi.sh           # NEW: Automated PyPI publishing
│   ├── start.sh                     # Application startup script
│   └── scripts/
│       ├── quickstart.sh            # Quick deployment script
│       └── prepare-package.sh       # Package preparation
├── 🐳 Docker Configuration
│   ├── docker-compose.yml           # Multi-service orchestration
│   ├── docker-compose-temp.yml      # Temporary configuration
│   └── docker/                      # Service-specific Dockerfiles
│       ├── alerting/
│       ├── analytics/
│       ├── dashboard/
│       ├── ingestion/
│       ├── storage/
│       ├── nginx/
│       └── prometheus/
├── 🌐 Web UI (React Dashboard)
│   ├── web-ui/
│   │   ├── package.json
│   │   ├── public/
│   │   └── src/
│   │       ├── components/
│   │       └── pages/
├── 🧪 Testing
│   └── tests/
│       ├── test_comprehensive.py
│       └── test_ingestion.py
├── 📋 Original Development Structure (preserved)
│   ├── services/                     # Original services directory
│   ├── shared/                       # Original shared directory
│   ├── cli.py                        # Original CLI (root level)
│   └── examples/
└── 🔧 Development Files
    ├── .env.example                  # Environment variables template
    ├── .gitignore                    # Git ignore rules
    └── integration_example.py        # Integration examples
```

## 🔄 Key Changes Made for PyPI

### ✅ Package Structure Transformation

| **Before (Development)** | **After (PyPI Package)** |
|--------------------------|---------------------------|
| `services/` (root level) | `streamflow/services/` |
| `shared/` (root level) | `streamflow/shared/` |
| `cli.py` (root level) | `streamflow/cli.py` |
| No package `__init__.py` | `streamflow/__init__.py` with exports |

### ✅ Import Path Updates

**Before:**
```python
from shared.config import get_settings
from shared.messaging import get_message_broker
```

**After:**
```python
from .shared.config import get_settings
from .shared.messaging import get_message_broker
```

### ✅ New Package Entry Points

The package now provides:

1. **Python Package**: `import streamflow`
2. **CLI Tool**: `streamflow` command
3. **Direct Access**: 
   ```python
   from streamflow import Event, AlertRule, Settings
   ```

## 📦 Package Contents

### Core Exports (`streamflow/__init__.py`)
```python
from .shared.models import Event, AlertRule, MetricData
from .shared.config import Settings  
from .shared.messaging import MessageBroker
from .shared.database import DatabaseManager
```

### Command Line Interface
```bash
streamflow --help                    # Show help
streamflow start ingestion          # Start ingestion service
streamflow start analytics          # Start analytics service
streamflow dashboard               # Launch dashboard
```

## 🚀 Distribution Files

Ready for PyPI upload:
- **Wheel**: `streamflow-1.0.0-py3-none-any.whl` (50KB)
- **Source**: `streamflow-1.0.0.tar.gz` (143KB)

## 📋 Installation After Publishing

Users can install with:
```bash
pip install streamflow
```

And import/use:
```python
import streamflow
from streamflow import Event, AlertRule

# Or use the CLI
streamflow --help
```

## 🔧 Development vs Production

- **Development**: Use the original structure in `services/` and `shared/`
- **Package**: Use the new `streamflow/` package structure
- **Both preserved**: Original structure maintained for development workflow

This dual structure allows for continued development while providing a clean, installable Python package for end users! 🎉