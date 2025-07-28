# PowerShell cleanup script for MCP Application Monitor Server
# This is a PowerShell wrapper around the Python cleanup script

param(
    [string]$Path = ".",
    [switch]$DryRun,
    [switch]$Logs,
    [switch]$Temp,
    [switch]$All,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "MCP Application Monitor Server - PowerShell Cleanup Script"
    Write-Host "========================================================="
    Write-Host ""
    Write-Host "Usage: .\cleanup.ps1 [OPTIONS] [PATH]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Path <path>    Path to clean up (default: current directory)"
    Write-Host "  -DryRun         Show what would be deleted without actually deleting"
    Write-Host "  -Logs           Also clean log files"
    Write-Host "  -Temp           Also clean temporary files"
    Write-Host "  -All            Clean everything (cache, logs, and temp files)"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\cleanup.ps1                    # Clean current directory"
    Write-Host "  .\cleanup.ps1 -DryRun            # Show what would be cleaned"
    Write-Host "  .\cleanup.ps1 -Logs              # Also clean log files"
    Write-Host "  .\cleanup.ps1 -All               # Clean everything"
    Write-Host "  .\cleanup.ps1 -Path C:\MyProject # Clean specific directory"
    exit 0
}

Write-Host "MCP Application Monitor Server - PowerShell Cleanup Script"
Write-Host "==========================================================="

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Using: $pythonVersion"
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python or add it to your PATH" -ForegroundColor Red
    exit 1
}

# Build arguments for Python script
$args = @()
if ($DryRun) { $args += "--dry-run" }
if ($Logs) { $args += "--logs" }
if ($Temp) { $args += "--temp" }
if ($All) { $args += "--all" }
$args += $Path

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cleanupScript = Join-Path $scriptDir "cleanup.py"

# Run the Python cleanup script
Write-Host ""
try {
    python $cleanupScript @args
} catch {
    Write-Host "Error running cleanup script: $_" -ForegroundColor Red
    exit 1
}
