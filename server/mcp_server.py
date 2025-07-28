"""
MCP Server setup and tools registration
"""
from mcp.server.fastmcp import FastMCP
from server.tools.registry import register_all_tools
from server.prompts.analysis_prompts import APP_USAGE_SUMMARY_PROMPT
from server.resources.system_info import get_system_info
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with tools"""
    mcp = FastMCP("Application Monitor Server")
    register_all_tools(mcp)

    @mcp.prompt("app_usage_summary")
    def app_usage_summary_prompt():
        return APP_USAGE_SUMMARY_PROMPT

    # Comment out resource temporarily to fix server startup
    # @mcp.resource("system://info")
    # def system_info_resource():
    #     return get_system_info()

    return mcp
