import logging
import time
import uuid
from functools import wraps

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)
sys_logger = logging.getLogger('sys_logger')

STATUS_MAP = {
    "AlreadyExistsError": 409,
    "WrongArgumentsError": 400,
    "NotFountError": 404,
    "InvalidTokenError": 498,
    "AccessDenied": 403,
    "NotAuthorized": 401,
}


def router_decorator(request: Request):
    """
    Декоратор для обработки запросов

    :param request: Данные запроса

    Фиксируем время обработки запроса и присваиваем ему id для отслеживания.
    Имеет встроенные обработчик ошибок.
    """
    def decorator(coro):
        @wraps(coro)
        async def wrapper(*args, **kwargs):
            tm_start = time.time()
            request_id = str(uuid.uuid4())
            logger.info(
                f"Start handling request [{request.method}] - {request.url}. Assigned ID: {request_id}"
            )
            logger.debug(
                f"RequestID: {request_id} - request: {str(request.headers)}; "
                f"Query: {str(request.query_params)}; Body: {str(request.body)}"
            )
            try:
                return await coro(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                status_code = STATUS_MAP.get(type(e).__name__, None)
                if status_code is None:
                    status_code = 500
                logger.error(
                    f"Exception occurred while handling request [{request.method}] - {request.url}; "
                    f"RequestID: {request_id} "
                    f"Error: {type(e).__name__}-{str(e)}"
                )
                raise HTTPException(
                    status_code=status_code,
                    detail={
                        "statusCode": status_code,
                        "message": str(e),
                        "requestId": request_id
                    }
                )
            finally:
                tm_end = time.time()
                logger.info(
                    f"Finish handling request [{request.method}] - {request.url} RequestID: {request_id}"
                )
                sys_logger.info(
                    f"Handling request {request_id} took {tm_end - tm_start:.2f}s; "
                )
        return wrapper
    return decorator



