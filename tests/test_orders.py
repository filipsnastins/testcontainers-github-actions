import re
from datetime import datetime
from typing import Any

import httpx
import pytest
from busypie import wait_at_most
from tomodachi.envelope.json_base import JsonBase
from tomodachi_testcontainers.clients import snssqs_client
from tomodachi_testcontainers.pytest.assertions import UUID4_PATTERN, assert_datetime_within_range
from types_aiobotocore_sqs import SQSClient


@pytest.mark.asyncio()
async def test_order_not_found(http_client: httpx.AsyncClient) -> None:
    response = await http_client.get("/order/foo")

    assert response.status_code == 404
    assert response.json() == {
        "error": "Order not found",
        "_links": {
            "self": {"href": "/order/foo"},
        },
    }


@pytest.mark.asyncio()
async def test_create_order(http_client: httpx.AsyncClient, moto_sqs_client: SQSClient) -> None:
    customer_id = "4752ce1f-d2a8-4bf1-88e7-ca05b9b3d756"
    products: list[str] = ["MINIMALIST-SPOON", "RETRO-LAMPSHADE"]

    response = await http_client.post("/orders", json={"customer_id": customer_id, "products": products})
    body = response.json()
    order_id = body["order_id"]
    get_order_link = body["_links"]["self"]["href"]

    assert response.status_code == 200
    assert re.match(UUID4_PATTERN, order_id)
    assert body == {
        "order_id": order_id,
        "_links": {
            "self": {"href": f"/order/{order_id}"},
        },
    }

    response = await http_client.get(get_order_link)
    body = response.json()

    assert response.status_code == 200
    assert_datetime_within_range(datetime.fromisoformat(body["created_at"]))
    assert body == {
        "order_id": order_id,
        "customer_id": customer_id,
        "products": products,
        "created_at": body["created_at"],
        "_links": {
            "self": {"href": f"/order/{order_id}"},
        },
    }

    async def _order_created_event_emitted() -> None:
        [event] = await snssqs_client.receive(moto_sqs_client, "order--created", JsonBase, dict[str, Any])

        assert_datetime_within_range(datetime.fromisoformat(event["created_at"]))
        assert event == {
            "event_id": event["event_id"],
            "order_id": order_id,
            "customer_id": customer_id,
            "products": products,
            "created_at": event["created_at"],
        }

    await wait_at_most(5).until_asserted_async(_order_created_event_emitted)
