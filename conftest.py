import pytest
from freezegun import freeze_time


@pytest.fixture()
def frozen_time():
    with freeze_time("2024-01-01T00:00:00Z") as frozen_time:
        yield frozen_time
