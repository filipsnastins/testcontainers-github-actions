import os
import uuid
from datetime import datetime, timezone

import structlog
import tomodachi
from aiohttp import web
from tomodachi.envelope.json_base import JsonBase

import dynamodb
from logger import configure_logger
from orders import Order, OrderCreatedEvent

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class TomodachiServiceOrders(tomodachi.Service):
    name = "service-orders"

    options = tomodachi.Options(
        aws_endpoint_urls=tomodachi.Options.AWSEndpointURLs(
            sns=os.environ.get("AWS_SNS_ENDPOINT_URL"),
            sqs=os.environ.get("AWS_SQS_ENDPOINT_URL"),
        ),
        aws_sns_sqs=tomodachi.Options.AWSSNSSQS(
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            topic_prefix=os.environ.get("AWS_SNS_TOPIC_PREFIX", ""),
            queue_name_prefix=os.environ.get("AWS_SQS_QUEUE_NAME_PREFIX", ""),
        ),
    )

    async def _start_service(self) -> None:
        configure_logger()
        await dynamodb.create_dynamodb_table()

    @tomodachi.http("POST", r"/orders")
    async def create_order(self, request: web.Request) -> web.Response:
        body = await request.json()
        customer_id: str = body["customer_id"]
        products: list[str] = body["products"]

        order = Order(
            order_id=str(uuid.uuid4()),
            customer_id=customer_id,
            products=products,
            created_at=datetime.utcnow().replace(tzinfo=timezone.utc),
        )
        event = OrderCreatedEvent(
            event_id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_id=order.order_id,
            products=order.products,
            created_at=order.created_at,
        )

        async with dynamodb.get_dynamodb_client() as dynamodb_client:
            await dynamodb_client.put_item(
                TableName=dynamodb.get_table_name(),
                Item={
                    "PK": {"S": f"ORDER#{order.order_id}"},
                    "OrderId": {"S": order.order_id},
                    "CustomerId": {"S": order.customer_id},
                    "Products": {"SS": order.products},
                    "CreatedAt": {"S": order.created_at.isoformat()},
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
        await tomodachi.aws_sns_sqs_publish(
            service=self,
            data=event.to_json_dict(),
            topic="order--created",
            message_envelope=JsonBase,
        )

        logger.info(
            "order_created",
            order_id=order.order_id,
            customer_id=customer_id,
            event_id=event.event_id,
        )
        return web.json_response(
            data={
                "order_id": event.order_id,
                "_links": {
                    "self": {"href": f"/order/{order.order_id}"},
                },
            }
        )

    @tomodachi.http("GET", r"/order/(?P<order_id>[^/]+?)/?")
    async def get_order(self, request: web.Request, order_id: str) -> web.Response:
        links = {
            "_links": {
                "self": {"href": f"/order/{order_id}"},
            },
        }
        async with dynamodb.get_dynamodb_client() as dynamodb_client:
            response = await dynamodb_client.get_item(
                TableName=dynamodb.get_table_name(),
                Key={"PK": {"S": f"ORDER#{order_id}"}},
            )
            if "Item" not in response:
                logger.error("order_not_found", order_id=order_id)
                return web.json_response({"error": "Order not found", **links}, status=404)

            item = response["Item"]
            order = Order(
                order_id=item["OrderId"]["S"],
                customer_id=item["CustomerId"]["S"],
                products=list(item["Products"]["SS"]),
                created_at=datetime.fromisoformat(item["CreatedAt"]["S"]),
            )

        return web.json_response({**order.to_json_dict(), **links})
