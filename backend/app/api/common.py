import hashlib
import json
import secrets
from typing import NoReturn

from fastapi import Header, HTTPException
from fastapi.responses import JSONResponse, Response

from app.core.config import get_settings


def fail(status: int, code: str, message: str, *, retryable: bool = False) -> NoReturn:
    raise HTTPException(
        status_code=status,
        detail={"code": code, "message": message, "retryable": retryable},
    )


async def require_client_token(x_client_token: str | None = Header(default=None)) -> None:
    expected = get_settings().client_token
    if not x_client_token or not secrets.compare_digest(x_client_token, expected):
        fail(401, "UNAUTHORIZED", "客户端凭据无效")


def cached_json(payload: dict[str, object], if_none_match: str | None) -> Response:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    etag = '"' + hashlib.sha256(body.encode("utf-8")).hexdigest() + '"'
    headers = {"ETag": etag, "Cache-Control": "private, max-age=300"}
    if if_none_match == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(payload, headers=headers)
