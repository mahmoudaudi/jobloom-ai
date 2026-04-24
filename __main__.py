from __future__ import annotations

import uvicorn

from jobloom_ai.settings import settings


def main() -> None:
    uvicorn.run(
        "jobloom_ai.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
