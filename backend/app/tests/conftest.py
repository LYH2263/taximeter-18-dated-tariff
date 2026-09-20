import os
import tempfile

# Must run before any import of app.config / app.db (DB_PATH is computed at import).
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="taxi-test-")

import pytest

from app import seed
from app.db import DB_PATH


@pytest.fixture(autouse=True)
def fresh_db():
    for p in DB_PATH.parent.glob("app.db*"):
        p.unlink()
    seed.init_db()
    yield
