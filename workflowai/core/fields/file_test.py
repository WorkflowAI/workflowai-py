import pytest
from pydantic import ValidationError

from workflowai.core.fields.file import File


class TestFile:
    def test_validate_data_or_url(self):
        with pytest.raises(ValidationError):
            File(data=None, url=None)

    def test_with_valid_data(self):
        file = File(data="data", content_type="image/png")
        assert file.data == "data"
        assert file.content_type == "image/png"
        assert file.url is None

    def test_with_valid_url(self):
        file = File(url="https://example.com/image.png")
        assert file.data is None
        assert file.content_type is None
