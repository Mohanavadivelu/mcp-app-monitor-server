# MCP Application Monitor Server

Enhanced MCP server for tracking application usage data with modular architecture, security features, and comprehensive tooling.

## 🚀 Features

- ✅ **Modular Architecture**: Clean separation of concerns with dedicated modules
- ✅ **SQLite Database**: Robust schema with constraints and indexing
- ✅ **Security First**: Rate limiting, input validation, and audit logging
- ✅ **Automatic Backups**: Configurable database backup system
- ✅ **Health Monitoring**: Comprehensive logging and error handling
- ✅ **Development Tools**: Cleanup scripts and utilities
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux

## 📁 Project Structure

```
mcp-app-monitor-server/
├── main.py                        # New entry point (start_mcp_server)
├── app_monitor_server.py           # Original monolithic file (kept for reference)
├── requirements.txt               # Dependencies
├── .env.template                  # Environment configuration template
├── .gitignore                     # Git ignore rules
├── README.md                      # This documentation
│
├── config/                        # Configuration management
│   ├── __init__.py
│   └── settings.py               # Config class and environment variables
│
├── database/                      # Database layer
│   ├── __init__.py
│   └── connection.py             # Database connection, initialization, backup
│
├── server/                        # MCP Server components
│   ├── __init__.py
│   ├── mcp_server.py            # FastMCP server setup and tools registration
│   └── decorators.py            # Security decorators (rate limiting, audit, validation)
│
├── utils/                         # Utilities
│   ├── __init__.py
│   └── logging_utils.py         # Logging setup and configuration
│
├── scripts/                       # Utility scripts
│   ├── cleanup.py                # Python cleanup script (removes __pycache__, etc.)
│   ├── cleanup.bat               # Windows batch wrapper
│   ├── cleanup.ps1               # PowerShell wrapper
│   └── README.md                 # Scripts documentation
│
├── data/                          # Database files
│   ├── app_monitor.db           # Main database (created at runtime)
│   └── backups/                 # Database backups
│       └── .gitkeep
│
└── logs/                          # Log files
    ├── mcp_server.log           # Server logs (created when audit logging enabled)
    └── .gitkeep
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+ 
- FastMCP: `pip install fastmcp`

### Installation & Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd mcp-app-monitor-server
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.template .env
   # Edit .env with your preferred settings
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```

4. **With custom settings**:
   ```bash
   # Debug mode
   python main.py --log-level DEBUG
   
   # Custom limits
   python main.py --max-records 500
   ```

## 🛠️ Available MCP Tools

The server provides the following MCP tools for application monitoring:

### Core Data Operations
- **`insert_app_usage_record()`** - Add new application usage data
- **`delete_app_usage_record(id)`** - Remove records by ID
- **`get_all_app_usage_records(limit)`** - Retrieve all records with pagination
- **`get_app_usage_by_user(user, limit)`** - Filter records by username
- **`get_database_stats()`** - Get comprehensive usage statistics

### Example Usage
```python
# Insert a new record
insert_app_usage_record(
    monitor_app_version="1.0.0",
    platform="Windows",
    user="john_doe",
    application_name="VS Code",
    application_version="1.85.0",
    log_date="2025-01-15T10:30:00Z",
    legacy_app=False,
    duration_seconds=3600
)

# Get user-specific data
get_app_usage_by_user("john_doe", limit=50)

# Get system statistics
get_database_stats()
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from the template and customize:

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
ENABLE_AUDIT_LOG=true             # Enable detailed audit logging

# Database Configuration  
DB_BACKUP_ENABLED=true            # Enable automatic backups
DB_BACKUP_INTERVAL=3600           # Backup interval in seconds (1 hour)

# Security Configuration
RATE_LIMIT_REQUESTS=100           # Max requests per window
RATE_LIMIT_WINDOW=60              # Rate limit window in seconds
MAX_QUERY_RESULTS=1000            # Maximum records per query
ADMIN_USER=admin                  # Admin username

# Optional Features
DB_ENCRYPTION_KEY=                # Database encryption (future feature)
```

### Command Line Options

```bash
python main.py --help

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}  Set logging level
  --max-records MAX_RECORDS               Maximum records per query  
  --timeout TIMEOUT                       Server timeout in seconds
```

## 🧹 Development Tools

### Cleanup Scripts

The project includes comprehensive cleanup utilities in the `scripts/` directory:

#### Basic Usage
```bash
# Clean Python cache files (__pycache__, .pyc)
python scripts/cleanup.py

# Preview what would be cleaned (safe)
python scripts/cleanup.py --dry-run

# Clean everything (cache + logs + temp files)
python scripts/cleanup.py --all
```

#### Platform-Specific Scripts
```bash
# Windows Batch
scripts\cleanup.bat --dry-run

# PowerShell
.\scripts\cleanup.ps1 -DryRun -All
```

#### What Gets Cleaned

**Always Cleaned (Python Cache)**:
- `__pycache__/` directories and contents
- `.pyc`, `.pyo`, `.pyd` files

**Optional with `--logs`**:
- `*.log` files in the `logs/` directory

**Optional with `--temp`**:
- `.DS_Store` (macOS), `Thumbs.db` (Windows)
- Editor backup files (`*~`)
- System temp files (`*.tmp`, `*.temp`)

#### Development Workflow Integration

**VS Code Task** (add to `.vscode/tasks.json`):
```json
{
    "label": "Clean Python Cache",
    "type": "shell", 
    "command": "python",
    "args": ["scripts/cleanup.py"],
    "group": "build"
}
```

**Pre-commit Hook** (add to `.git/hooks/pre-commit`):
```bash
#!/bin/sh
python scripts/cleanup.py
```

## 🏗️ Architecture & Design

### Key Architectural Benefits

✅ **Separation of Concerns**: Each module has a single responsibility  
✅ **Maintainability**: Small, focused files instead of monolithic code  
✅ **Testability**: Modules can be tested independently  
✅ **Security**: Isolated security features (rate limiting, validation, audit)  
✅ **Scalability**: Easy to add new features without affecting existing code  
✅ **Configuration Management**: Centralized settings with environment support  

### Module Responsibilities

- **`config/`**: Application configuration and environment management
- **`database/`**: Database connections, schema, and backup operations  
- **`server/`**: MCP server setup, tools registration, and security decorators
- **`utils/`**: Common utilities like logging and helper functions
- **`scripts/`**: Development and maintenance utilities

### Security Features

- **Rate Limiting**: Configurable request limits per time window
- **Input Validation**: Automatic sanitization and length checks
- **Audit Logging**: Detailed operation logging for compliance
- **Secure Database**: Connection timeouts and pragma settings
- **Error Handling**: Graceful error handling without information leakage

## 🔄 Migration from Monolithic Design

The project was successfully refactored from a single-file monolithic design to a modular architecture while maintaining:

- **Full Backward Compatibility**: All MCP tools work exactly the same
- **Preserved Functionality**: Every feature from the original design
- **Enhanced Security**: All security features maintained and improved
- **Better Performance**: Optimized database operations and connections

The original `app_monitor_server.py` is preserved for reference.

## 📊 Database Schema

```sql
-- Main application usage table
CREATE TABLE app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_app_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    user TEXT NOT NULL,
    application_name TEXT NOT NULL, 
    application_version TEXT NOT NULL,
    log_date TEXT NOT NULL,
    legacy_app BOOLEAN NOT NULL,
    duration_seconds INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table (if enabled)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);
```

## 🚀 Future Enhancements

The modular foundation enables easy addition of:

1. **Unit Testing**: Comprehensive test suite for each module
2. **Service Layer**: Business logic services for complex operations  
3. **API Documentation**: Auto-generated docs from MCP tool definitions
4. **Health Monitoring**: Endpoint health checks and metrics collection
5. **CI/CD Pipeline**: Automated testing and deployment workflows
6. **Database Migrations**: Schema version management
7. **Performance Metrics**: Query optimization and monitoring
8. **Authentication**: User authentication and authorization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Run cleanup before committing: `python scripts/cleanup.py`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛠️ Troubleshooting

### Common Issues

**Server won't start**:
- Check Python version (3.7+ required)
- Verify FastMCP installation: `pip install fastmcp`
- Check log files in `logs/` directory

**Database errors**:
- Ensure `data/` directory has write permissions
- Check disk space for database and backups
- Review database logs in audit log table

**Rate limiting issues**:
- Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` in `.env`
- Check current rate limit status in `get_database_stats()`

### Debugging

Enable debug logging for detailed troubleshooting:
```bash
python main.py --log-level DEBUG
```

Or set in environment:
```bash
export LOG_LEVEL=DEBUG
python main.py
```