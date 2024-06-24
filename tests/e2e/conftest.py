import os

import pytest
from dotenv import load_dotenv

from workflowai import Client, start

load_dotenv()


@pytest.fixture(scope="session")
def wai() -> Client:
    return start(
        url=os.environ["WORKFLOWAI_TEST_API_URL"],
        api_key=os.environ["WORKFLOWAI_TEST_API_KEY"],
    )
