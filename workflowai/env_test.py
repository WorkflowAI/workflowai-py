from typing import Optional
from unittest.mock import patch

import pytest

from .env import _default_api_url  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize(
    ("api_url", "expected"),
    [
        ("https://run.workflowai.com", "https://workflowai.com"),
        ("https://api.workflowai.com", "https://workflowai.com"),
        ("https://workflowai.com", "https://workflowai.com"),
        (None, "https://workflowai.com"),
    ],
)
def test_default_api_url(api_url: Optional[str], expected: str):
    with patch("workflowai.env.WORKFLOWAI_API_URL", api_url):
        assert _default_api_url() == expected
