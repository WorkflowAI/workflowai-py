import os

import pytest
from dotenv import load_dotenv

from workflowai import Client
from workflowai.core.client.client import WorkflowAIClient

load_dotenv()


@pytest.fixture(scope="session")
def wai() -> Client:
    return WorkflowAIClient(
        endpoint=os.environ["WORKFLOWAI_TEST_API_URL"],
        api_key=os.environ["WORKFLOWAI_TEST_API_KEY"],
    )
