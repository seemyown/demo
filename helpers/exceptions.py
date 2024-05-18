from fastapi import HTTPException
from pydantic import BaseModel


class UserNotFoundDBException(Exception):
    msg: str = "User not found"
    reason: str = "Token has invalid credentials(user_id/username)"


def raiser_routing_exception(e: Exception, code=400):
    err_msg = str(e)
    err_reason = str(e.__class__.__name__)
    raise HTTPException(
        status_code=code,
        detail={
            "statusCode": code,
            "status": "error",
            "reason": err_reason,
            "message": err_msg
        }
    )