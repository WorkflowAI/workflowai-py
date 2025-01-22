import os

import pytest
from dotenv import load_dotenv

from workflowai.core.client.client import WorkflowAI

load_dotenv()


@pytest.fixture(scope="session")
def wai() -> WorkflowAI:
    return WorkflowAI(
        endpoint=os.environ["WORKFLOWAI_TEST_API_URL"],
        api_key=os.environ["WORKFLOWAI_TEST_API_KEY"],
    )
