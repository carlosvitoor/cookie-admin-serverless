import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Handler principal da Lambda.
    """
    logger.info(f"Evento recebido: {json.dumps(event)}")

    env_type = os.environ.get('ENV_TYPE', 'unknown')

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Hello from Cookie Admin!",
            "environment": env_type,
            "status": "Operational"
        })
    }