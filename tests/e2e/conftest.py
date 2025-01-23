import os

import pytest
from dotenv import load_dotenv

import workflowai

load_dotenv(override=True)


@pytest.fixture(scope="session", autouse=True)
def wai():
    workflowai.init(
        api_key=os.environ["WORKFLOWAI_TEST_API_KEY"],
        url=os.environ["WORKFLOWAI_TEST_API_URL"],
    )
    return workflowai.shared_client
