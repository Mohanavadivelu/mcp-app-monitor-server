# MCP Application Monitor Server

Enhanced MCP server for tracking application usage data with security and stability features.

## Features
- ✅ SQLite database with your exact schema
- ✅ Rate limiting and input validation
- ✅ Automatic backups every hour
- ✅ Audit logging for security compliance
- ✅ Auto-reload on code changes
- ✅ Health monitoring and auto-restart

## Quick Start
1. Install: `pip install fastmcp`
2. Open project in VS Code
3. Server starts automatically via MCP

## Available Tools
- `insert_app_usage_record()` - Add new usage data
- `delete_app_usage_record(id)` - Remove records by ID
- `get_all_app_usage_records()` - Retrieve all records
- `get_app_usage_by_user(user)` - Filter by username
- `get_database_stats()` - Get usage statistics

## Configuration
Edit `.env.mcp` to customize settings like rate limits, backup intervals, and logging levels.