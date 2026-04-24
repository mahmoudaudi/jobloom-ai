from __future__ import annotations

import uvicorn

from api_server.settings import settings


def main() -> None:
    uvicorn.run(
        "api_server.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
