#!/usr/bin/env python3
"""
Cleanup script for MCP Application Monitor Server
Recursively removes Python cache files and directories
"""
import os
import shutil
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


def find_pycache_dirs(root_path: Path) -> List[Path]:
    """Find all __pycache__ directories recursively"""
    pycache_dirs = []
    
    for root, dirs, files in os.walk(root_path):
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            pycache_dirs.append(pycache_path)
    
    return pycache_dirs


def find_pyc_files(root_path: Path) -> List[Path]:
    """Find all .pyc, .pyo, and .pyd files recursively"""
    pyc_files = []
    extensions = [".pyc", ".pyo", ".pyd"]
    
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                pyc_files.append(Path(root) / file)
    
    return pyc_files


def cleanup_pycache(root_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """
    Clean up __pycache__ directories and Python bytecode files
    
    Args:
        root_path: Root directory to start cleanup from
        dry_run: If True, only show what would be deleted without actually deleting
        
    Returns:
        Tuple of (directories_removed, files_removed)
    """
    dirs_removed = 0
    files_removed = 0
    
    print(f"Scanning for Python cache files in: {root_path}")
    print("=" * 60)
    
    # Find and remove __pycache__ directories
    pycache_dirs = find_pycache_dirs(root_path)
    
    if pycache_dirs:
        print(f"\nFound {len(pycache_dirs)} __pycache__ directories:")
        for pycache_dir in pycache_dirs:
            relative_path = pycache_dir.relative_to(root_path)
            if dry_run:
                print(f"  [DRY RUN] Would remove: {relative_path}")
            else:
                try:
                    shutil.rmtree(pycache_dir)
                    print(f"  ✓ Removed: {relative_path}")
                    dirs_removed += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove {relative_path}: {e}")
    else:
        print("\nNo __pycache__ directories found.")
    
    # Find and remove standalone .pyc files
    pyc_files = find_pyc_files(root_path)
    
    if pyc_files:
        print(f"\nFound {len(pyc_files)} Python bytecode files:")
        for pyc_file in pyc_files:
            relative_path = pyc_file.relative_to(root_path)
            if dry_run:
                print(f"  [DRY RUN] Would remove: {relative_path}")
            else:
                try:
                    pyc_file.unlink()
                    print(f"  ✓ Removed: {relative_path}")
                    files_removed += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove {relative_path}: {e}")
    else:
        print("\nNo standalone Python bytecode files found.")
    
    return dirs_removed, files_removed


def cleanup_logs(root_path: Path, dry_run: bool = False) -> int:
    """
    Clean up log files
    
    Args:
        root_path: Root directory to start cleanup from
        dry_run: If True, only show what would be deleted without actually deleting
        
    Returns:
        Number of log files removed
    """
    logs_dir = root_path / "logs"
    files_removed = 0
    
    if not logs_dir.exists():
        print("\nNo logs directory found.")
        return 0
    
    log_files = list(logs_dir.glob("*.log"))
    
    if log_files:
        print(f"\nFound {len(log_files)} log files:")
        for log_file in log_files:
            relative_path = log_file.relative_to(root_path)
            if dry_run:
                print(f"  [DRY RUN] Would remove: {relative_path}")
            else:
                try:
                    log_file.unlink()
                    print(f"  ✓ Removed: {relative_path}")
                    files_removed += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove {relative_path}: {e}")
    else:
        print("\nNo log files found.")
    
    return files_removed


def cleanup_temp_files(root_path: Path, dry_run: bool = False) -> int:
    """
    Clean up temporary files like .DS_Store, Thumbs.db, etc.
    
    Args:
        root_path: Root directory to start cleanup from
        dry_run: If True, only show what would be deleted without actually deleting
        
    Returns:
        Number of temp files removed
    """
    temp_patterns = [
        ".DS_Store",
        ".DS_Store?",
        "._*",
        ".Spotlight-V100",
        ".Trashes",
        "ehthumbs.db",
        "Thumbs.db",
        "*.tmp",
        "*.temp",
        "*~"
    ]
    
    files_removed = 0
    temp_files = []
    
    # Find temp files
    for pattern in temp_patterns:
        temp_files.extend(root_path.rglob(pattern))
    
    if temp_files:
        print(f"\nFound {len(temp_files)} temporary files:")
        for temp_file in temp_files:
            relative_path = temp_file.relative_to(root_path)
            if dry_run:
                print(f"  [DRY RUN] Would remove: {relative_path}")
            else:
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
                    print(f"  ✓ Removed: {relative_path}")
                    files_removed += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove {relative_path}: {e}")
    else:
        print("\nNo temporary files found.")
    
    return files_removed


def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(
        description="Clean up Python cache files and temporary files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup.py                    # Clean current directory
  python cleanup.py --dry-run          # Show what would be cleaned
  python cleanup.py --logs             # Also clean log files
  python cleanup.py --all              # Clean everything including temp files
  python cleanup.py /path/to/project   # Clean specific directory
        """
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to clean up (default: current directory)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Also clean log files"
    )
    
    parser.add_argument(
        "--temp",
        action="store_true",
        help="Also clean temporary files (.DS_Store, Thumbs.db, etc.)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean everything (cache, logs, and temp files)"
    )
    
    args = parser.parse_args()
    
    # Resolve the path
    cleanup_path = Path(args.path).resolve()
    
    if not cleanup_path.exists():
        print(f"Error: Path '{cleanup_path}' does not exist.")
        sys.exit(1)
    
    if not cleanup_path.is_dir():
        print(f"Error: Path '{cleanup_path}' is not a directory.")
        sys.exit(1)
    
    print("MCP Application Monitor Server - Cleanup Script")
    print("=" * 50)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will actually be deleted")
        print("=" * 50)
    
    total_dirs = 0
    total_files = 0
    
    # Clean Python cache files (always)
    dirs_removed, files_removed = cleanup_pycache(cleanup_path, args.dry_run)
    total_dirs += dirs_removed
    total_files += files_removed
    
    # Clean logs if requested
    if args.logs or args.all:
        log_files_removed = cleanup_logs(cleanup_path, args.dry_run)
        total_files += log_files_removed
    
    # Clean temp files if requested
    if args.temp or args.all:
        temp_files_removed = cleanup_temp_files(cleanup_path, args.dry_run)
        total_files += temp_files_removed
    
    # Summary
    print("\n" + "=" * 60)
    if args.dry_run:
        print("DRY RUN SUMMARY:")
        print(f"  Would remove {total_dirs} directories")
        print(f"  Would remove {total_files} files")
    else:
        print("CLEANUP SUMMARY:")
        print(f"  Removed {total_dirs} directories")
        print(f"  Removed {total_files} files")
    
    print("\nCleanup completed!")


if __name__ == "__main__":
    main()
