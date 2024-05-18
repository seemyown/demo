from fastapi import Request, HTTPException

from config import settings


async def header_controller(request: Request):
    if settings.mode:
        return
    if request.headers.get("x-access-token", None) is None:
        raise HTTPException(status_code=401, detail="Missing x-access-token header")
    if request.headers["x-access-token"] != settings.X_ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Wrong x-access-token header")
