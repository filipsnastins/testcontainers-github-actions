import asyncio
import contextlib
from typing import AsyncGenerator, Generator, Iterator, cast

import httpx
import pytest
import pytest_asyncio
from docker.models.images import Image
from tomodachi_testcontainers import MotoContainer, TomodachiContainer
from tomodachi_testcontainers.clients import SNSSQSTestClient
from tomodachi_testcontainers.utils import get_available_port
from types_aiobotocore_sns import SNSClient
from types_aiobotocore_sqs import SQSClient


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    with contextlib.closing(asyncio.new_event_loop()) as loop:
        yield loop


@pytest.fixture(scope="session")
def snssqs_tc(moto_sns_client: SNSClient, moto_sqs_client: SQSClient) -> SNSSQSTestClient:
    return SNSSQSTestClient.create(moto_sns_client, moto_sqs_client)


@pytest_asyncio.fixture(scope="session")
async def _create_topics_and_queues(snssqs_tc: SNSSQSTestClient) -> None:
    await snssqs_tc.subscribe_to(
        topic="order--created",
        queue="order--created",
    )


@pytest.fixture(scope="session")
def tomodachi_container(
    testcontainers_docker_image: Image, moto_container: MotoContainer, _create_topics_and_queues: None
) -> Generator[TomodachiContainer, None, None]:
    with (
        TomodachiContainer(image=str(testcontainers_docker_image.id), edge_port=get_available_port())
        .with_env("AWS_REGION", "us-east-1")
        .with_env("AWS_ACCESS_KEY_ID", "testing")
        .with_env("AWS_SECRET_ACCESS_KEY", "testing")
        .with_env("AWS_SNS_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("AWS_SQS_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("AWS_DYNAMODB_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("DYNAMODB_TABLE_NAME", "orders")
    ) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture(scope="session")
async def http_client(tomodachi_container: TomodachiContainer) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=tomodachi_container.get_external_url()) as client:
        yield client
