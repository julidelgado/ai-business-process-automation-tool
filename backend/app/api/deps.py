from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db


def require_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None) -> str:
    settings = get_settings()
    if not settings.api_key:
        return "anonymous"
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return "api-key-user"


def get_actor(
    _: Annotated[str, Depends(require_api_key)],
    x_actor: Annotated[str | None, Header(alias="X-Actor")] = None,
) -> str:
    return x_actor or "api-user"


DbSession = Annotated[Session, Depends(get_db)]
