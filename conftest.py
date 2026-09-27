import pytest
from dotenv import load_dotenv

from src.config.config_loader import get_config

# Load .env before any fixture reads a credential. override=False: a variable already set (a CI
# secret, a one-off shell export) always wins over the file.
load_dotenv(override=False)


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", help="Environment from config/config.yaml")


@pytest.fixture(scope="session")
def config(request):
    return get_config(request.config.getoption("--env"))
