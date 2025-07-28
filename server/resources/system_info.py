from config.settings import config

def get_system_info():
    return {
        "server_version": "1.0.0",
        "database_status": "online",
        "max_query_results": config.MAX_QUERY_RESULTS
    }
