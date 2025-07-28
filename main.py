#!/usr/bin/env python3
"""
MCP Application Monitor Server - Main Entry Point
Built with FastMCP with modular architecture and security improvements
"""
import argparse
import sys
from database.connection import init_database, db_manager
from server.mcp_server import create_mcp_server
from utils.logging_utils import setup_logging, get_logger
from config.settings import config


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Application Monitor Server")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--max-records", type=int, default=10000, help="Maximum records per query")
    parser.add_argument("--timeout", type=int, default=30, help="Server timeout in seconds")
    return parser.parse_args()


def start_mcp_server():
    """Main function to start the MCP server with enhanced error handling and monitoring"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging
        logger = setup_logging()
        
        # Update logging level if specified
        if args.log_level:
            import logging
            logging.getLogger().setLevel(getattr(logging, args.log_level))
        
        logger.info("Starting MCP Application Monitor Server")
        logger.info(f"Configuration: Max records={config.MAX_QUERY_RESULTS}, Rate limit={config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}s")
        
        # Initialize the database
        logger.info("Initializing database...")
        init_database()
        
        # Create and configure the MCP server
        logger.info("Creating MCP server...")
        mcp = create_mcp_server()
        
        # Start the server
        logger.info("Server starting...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
    finally:
        logger.info("Closing database connections...")
        db_manager.close_all()
        sys.exit(1)


if __name__ == "__main__":
    start_mcp_server()
