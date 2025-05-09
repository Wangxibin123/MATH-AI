import logging
import sys
from apps.gateway.settings import settings # Import your settings

def setup_logging():
    log_level = settings.LOG_LEVEL.upper()
    json_log = settings.JSON_LOG

    # Basic configuration for now
    # You can integrate Loguru here if preferred, based on JSON_LOG
    if json_log:
        # Placeholder for JSON logging with Loguru or similar
        # For now, just use basic logging but indicate JSON was intended
        print("JSON logging intended but using basic config for now.")
        logging.basicConfig(
            level=log_level,
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
            stream=sys.stdout,
        )
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            stream=sys.stdout,
        )
    
    # Example: Quieting very verbose loggers if necessary
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.LOG_LEVEL == "DEBUG" else logging.WARNING)

    print(f"Logging setup complete. Level: {log_level}, JSON: {json_log}") 