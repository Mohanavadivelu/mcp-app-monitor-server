from mcp.server.fastmcp import FastMCP
from server.tools.app_usage import register_app_usage_tools
from server.tools.database_stats import register_database_stats_tool

def register_all_tools(mcp: FastMCP):
    """
    Registers all tools with the MCP server.
    """
    register_app_usage_tools(mcp)
    register_database_stats_tool(mcp)
