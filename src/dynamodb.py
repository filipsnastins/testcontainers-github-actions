import os

import structlog
from aiobotocore.session import get_session
from structlog import get_logger
from types_aiobotocore_dynamodb import DynamoDBClient

logger: structlog.stdlib.BoundLogger = get_logger()


def get_table_name() -> str:
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise ValueError("DYNAMODB_TABLE_NAME environment variable is not set")
    return table_name


def get_dynamodb_client() -> DynamoDBClient:
    session = get_session()
    return session.create_client(
        "dynamodb",
        region_name=os.environ.get("AWS_REGION"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"),
    )


async def create_dynamodb_table() -> None:
    table_name = get_table_name()
    async with get_dynamodb_client() as client:
        try:
            await client.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {
                        "AttributeName": "PK",
                        "AttributeType": "S",
                    },
                ],
                KeySchema=[
                    {
                        "AttributeName": "PK",
                        "KeyType": "HASH",
                    },
                ],
                BillingMode="PAY_PER_REQUEST",
            )
        except client.exceptions.ResourceInUseException:
            logger.info("dynamodb_table_already_exists", table_name=table_name)
        else:
            logger.info("dynamodb_table_created", table_name=table_name)
