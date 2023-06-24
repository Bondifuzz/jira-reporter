from contextlib import suppress
import logging
from logging.config import dictConfig
import yaml

from .app.server import run
from .app.settings import load_app_settings

# fmt: off
with suppress(ModuleNotFoundError):
    import uvloop; uvloop.install()
# fmt: on

if __name__ == "__main__":

    # Configure logging
    with open("logging.yaml") as f:
        dictConfig(yaml.safe_load(f))

    fmt = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
    logging.basicConfig(format=fmt, level=logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    settings = load_app_settings()
    run(settings)