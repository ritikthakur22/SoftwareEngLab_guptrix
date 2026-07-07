import os
import tempfile

import pytest


@pytest.fixture
def temp_db_path():
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.close()
    try:
        yield handle.name
    finally:
        if os.path.exists(handle.name):
            os.remove(handle.name)
