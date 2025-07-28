# Cleanup Scripts

This directory contains scripts to clean up Python cache files and other temporary files from the MCP Application Monitor Server project.

## Scripts Available

### 1. `cleanup.py` - Main Python Cleanup Script

A comprehensive Python script that recursively removes:
- `__pycache__` directories
- Python bytecode files (`.pyc`, `.pyo`, `.pyd`)
- Log files (optional)
- Temporary files (optional)

#### Usage

```bash
# Basic cleanup (removes only Python cache files)
python scripts/cleanup.py

# Dry run to see what would be cleaned
python scripts/cleanup.py --dry-run

# Clean specific directory
python scripts/cleanup.py /path/to/directory

# Also clean log files
python scripts/cleanup.py --logs

# Also clean temporary files (.DS_Store, Thumbs.db, etc.)
python scripts/cleanup.py --temp

# Clean everything (cache + logs + temp files)
python scripts/cleanup.py --all

# Get help
python scripts/cleanup.py --help
```

### 2. `cleanup.bat` - Windows Batch Script

A simple Windows batch file wrapper around the Python script.

#### Usage

```cmd
# Double-click to run, or from command prompt:
scripts\cleanup.bat

# Pass arguments through to Python script:
scripts\cleanup.bat --dry-run
scripts\cleanup.bat --all
```

### 3. `cleanup.ps1` - PowerShell Script

A PowerShell wrapper with native PowerShell parameter handling.

#### Usage

```powershell
# Basic usage
.\scripts\cleanup.ps1

# With parameters
.\scripts\cleanup.ps1 -DryRun
.\scripts\cleanup.ps1 -All
.\scripts\cleanup.ps1 -Path "C:\MyProject"

# Get help
.\scripts\cleanup.ps1 -Help
```

## What Gets Cleaned

### Always Cleaned (Python Cache)
- `__pycache__/` directories and all contents
- Standalone `.pyc`, `.pyo`, `.pyd` files

### With `--logs` flag
- `*.log` files in the `logs/` directory

### With `--temp` flag
- `.DS_Store` (macOS)
- `Thumbs.db` (Windows)
- `._*` files (macOS resource forks)
- `.Spotlight-V100` (macOS)
- `.Trashes` (macOS)
- `*.tmp`, `*.temp` files
- Editor backup files (`*~`)

## Safety Features

- **Dry Run Mode**: Use `--dry-run` to see what would be deleted without actually deleting anything
- **Error Handling**: Script continues even if some files can't be deleted
- **Relative Paths**: Shows relative paths in output for clarity
- **Confirmation**: Batch script pauses to show results when double-clicked

## Examples

```bash
# Clean only Python cache from current directory
python scripts/cleanup.py

# See what would be cleaned in the entire project
python scripts/cleanup.py --dry-run --all

# Clean everything from a specific project
python scripts/cleanup.py --all /path/to/other/project

# Clean only logs
python scripts/cleanup.py --logs
```

## Integration with Development Workflow

You can add the cleanup script to your development workflow:

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/sh
python scripts/cleanup.py
```

### VS Code Task
Add to `.vscode/tasks.json`:
```json
{
    "label": "Clean Python Cache",
    "type": "shell",
    "command": "python",
    "args": ["scripts/cleanup.py"],
    "group": "build",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "panel": "new"
    }
}
```

### Make/Build Integration
Add to your build process to ensure clean builds:
```bash
clean:
    python scripts/cleanup.py --all
```

## Notes

- The script is safe to run multiple times
- It respects `.gitignore` patterns (won't recreate ignored files)
- Works on Windows, macOS, and Linux
- Requires Python 3.6+ (uses pathlib)
