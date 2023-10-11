from typing import AsyncGenerator, Generator, cast

import httpx
import pytest
import pytest_asyncio
from docker.models.images import Image as DockerImage
from tomodachi_testcontainers import MotoContainer, TomodachiContainer
from tomodachi_testcontainers.clients import SNSSQSTestClient
from tomodachi_testcontainers.utils import get_available_port


@pytest_asyncio.fixture()
async def _create_topics_and_queues(moto_snssqs_tc: SNSSQSTestClient) -> None:
    await moto_snssqs_tc.subscribe_to(
        topic="order--created",
        queue="order--created",
    )


@pytest.fixture()
def tomodachi_container(
    tomodachi_image: DockerImage,
    moto_container: MotoContainer,
    _create_topics_and_queues: None,
    _reset_moto_container_on_teardown: None,
) -> Generator[TomodachiContainer, None, None]:
    with (
        TomodachiContainer(image=str(tomodachi_image.id), edge_port=get_available_port())
        .with_env("AWS_REGION", "us-east-1")
        .with_env("AWS_ACCESS_KEY_ID", "testing")
        .with_env("AWS_SECRET_ACCESS_KEY", "testing")
        .with_env("AWS_SNS_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("AWS_SQS_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("AWS_DYNAMODB_ENDPOINT_URL", moto_container.get_internal_url())
        .with_env("DYNAMODB_TABLE_NAME", "orders")
    ) as container:
        yield cast(TomodachiContainer, container)


@pytest_asyncio.fixture()
async def http_client(tomodachi_container: TomodachiContainer) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=tomodachi_container.get_external_url()) as client:
        yield client
