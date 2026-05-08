from __future__ import annotations

import uvicorn

from src.app import app
from src.core.config_loader import get_config


def main() -> None:
    config = get_config()
    uvicorn.run(
        "src.main:app",
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers,
    )


if __name__ == "__main__":
    main()
