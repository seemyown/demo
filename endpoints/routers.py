import asyncio
import logging
import random
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError as Error
from fastapi import APIRouter, HTTPException, Depends, File, BackgroundTasks, Body, Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache

from cross_sec import header_controller
from database.interface import DatabaseInterface
from endpoints.dto import UserCreateModel, UserView, UpdateUsersView, TokenData, EmailSenderData, \
    FirebaseToken, AppendDevice, UpdateAvatar
from helpers.cloud_storage import AvatarsUploader, BackPadsUploader
from helpers.cross_service import CrossService
from helpers.decorators import router_decorator
from helpers.publisher import publish_message
from helpers.security import Authenticator
from messages.notifications import DropUser

profile = APIRouter(prefix="/profile", dependencies=[Depends(header_controller)])
logger = logging.getLogger(__name__)


@profile.get("/{username}")
async def check_available_username(request: Request, username: str):
    """Проверка доступности имени пользователя"""
    @router_decorator(request)
    async def _check_available_username(_username: str):
        is_available = await DatabaseInterface.check_username(username)
        return JSONResponse(
            {
                "statusCode": 200,
                "isAvailable": is_available
            },
            200
        )

    return await _check_available_username(username)


@profile.post("/", status_code=201)
async def create_user(request: Request, body: UserCreateModel, bg_tasks: BackgroundTasks):
    """Создание пользователя"""
    async def send_email(data: EmailSenderData):
        await publish_message(data, "email")

    async def add_token(data: FirebaseToken):
        await publish_message(data, "notification")

    async def send_request_to_community(_id: str, user: UserCreateModel):
        await CrossService.add_user(_id, user)

    async def background_tasks(
            _email_data: EmailSenderData, _token_data: FirebaseToken,
            _id: str, user: UserCreateModel
    ):
        await asyncio.gather(
            send_email(_email_data), add_token(_token_data),
            send_request_to_community(_id, user)
        )

    @router_decorator(request)
    async def _create_user():
        user_id, link = await DatabaseInterface.create_user(body)
        verification_code = random.randint(10000, 100000)
        email_data = EmailSenderData(
            email=body.email,
            target="verification",
            verification_code=str(verification_code)
        )
        token_data = FirebaseToken(
            target="token",
            firebaseToken=body.firebaseToken,
            username=body.username,
            userId=str(user_id),
            mediaUrl=link
        )
        bg_tasks.add_task(background_tasks, email_data, token_data,
                          str(user_id), body)
        if isinstance(user_id, UUID):
            return JSONResponse(
                content={
                    "statusCode": 201,
                    "status": "created",
                    "id": str(user_id),
                    "confirmCode": verification_code,
                    "dropLink": " "
                },
                status_code=201
            )

    return await _create_user()


@profile.get("/", response_model=UserView)
@cache(expire=30)
async def get_user_profile(
        request: Request,
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Получение информации о пользователе"""
    @router_decorator(request)
    async def _get_user_profile(_user):
        _id = _user.id
        _user = await DatabaseInterface.get_user_by_id(_id)
        return UserView.model_validate(_user)

    return await _get_user_profile(user)


@profile.patch("/")
async def update_user_profile(
        update_profile: UpdateUsersView,
        request: Request,
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Обновление данных пользователя"""
    @router_decorator(request)
    async def _update_user_profile():
        flag = False
        _id = user.id
        if update_profile.city:
            flag = True
        values_to_update = update_profile.model_dump(exclude_none=True)
        await DatabaseInterface.update_user_profile(
            _id, values_to_update, flag
        )
        return JSONResponse(
            status_code=201,
            content={
                "statusCode": 201,
                "status": "updated"
            }
        )
    return await _update_user_profile()


@profile.delete("/", status_code=200)
async def delete_user_profile(
        bg_tasks: BackgroundTasks,
        request: Request,
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Удаление пользователя"""
    _id = user.id

    @router_decorator(request)
    async def _delete_user_profile():
        await DatabaseInterface.delete_user(_id)
        data = DropUser(
            userId=_id
        )
        bg_tasks.add_task(publish_message, data, "notification")
        return JSONResponse(
            {
                "statusCode": 200,
                "status": "deleted"
            },
            200
        )


@profile.post("/avatar")
async def add_users_avatars(
        bg_tasks: BackgroundTasks,
        request: Request,
        avatar: bytes = File(...),
        user: TokenData = Depends(get_user_profile)
):
    """Добавление аватара пользователя"""
    _id = user.id

    @router_decorator(request)
    async def _add_users_avatars():
        file_name = f"{_id}-avatar-{random.randint(10000, 999999)}.png"
        AvatarsUploader.upload_avatar(avatar, file_name)
        link = await DatabaseInterface.add_new_avatar(file_name, _id)
        data = UpdateAvatar(
            target="avatar",
            userId=str(_id),
            newMediaUrl=link
        )
        bg_tasks.add_task(publish_message, data, "notification")
        return JSONResponse(
            status_code=200,
            content={
                "statusCode": 200,
                "status": "success",
                "link": link
            }
        )

    return await _add_users_avatars()


@profile.delete("/avatar/{avatar_id}")
async def delete_avatar(
        bg_task: BackgroundTasks, avatar_id: int, request: Request,
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Удаление аватара пользователя"""
    @router_decorator(request)
    async def _delete_avatar():
        _id = user.id

        async def delete_process(_avatar_id, org_id):
            prev_avatar = await DatabaseInterface.delete_avatar(_avatar_id, org_id)
            data = UpdateAvatar(
                target="avatar",
                userId=str(_id),
                newMediaUrl=prev_avatar
            )
            await publish_message(data, "notification")

        bg_task.add_task(delete_process, avatar_id, _id)
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "status": "deleted"
            }
        )

    return await _delete_avatar()


@profile.post("/back_pad")
async def add_users_back_pad(
        bg_tasks: BackgroundTasks,
        request: Request,
        back_pad: bytes = File(...),
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Замена подложки профиля"""
    @router_decorator(request)
    async def _add_users_back_pad():
        _id = user.id
        file_name = f"{_id}-back_pad.png"
        BackPadsUploader.upload_back_pads(back_pad, file_name)
        link = await DatabaseInterface.update_back_pad(file_name, _id)
        return JSONResponse(
            status_code=200,
            content={
                "statusCode": 200,
                "status": "success",
                "link": link
            }
        )

    return await _add_users_back_pad()


@profile.delete("/drop/{_id}", status_code=200)
async def drop_unverified_user(_id, request: Request, bg_tasks: BackgroundTasks):
    """Удаление неподтвержденного пользователя"""

    @router_decorator(request)
    async def _delete_unverified_user():
        await DatabaseInterface.drop_user(_id)
        data = DropUser(
            userId=_id
        )
        bg_tasks.add_task(publish_message, data)

    return await _delete_unverified_user()


@profile.post("/append/device")
async def add_fire_base_token(
        token: AppendDevice,
        request: Request,
        bg_task: BackgroundTasks,
        user: TokenData = Depends(Authenticator.get_user_by_token)
):
    """Firebase token для пользователя"""
    @router_decorator(request)
    async def _add_fire_base_token():
        _id = user.id
        data = FirebaseToken(
            target="token",
            userId=str(user.id),
            username=user.username,
            firebaseToken=token.token
        )
        bg_task.add_task(publish_message, data, "notification")
        return JSONResponse(
            {
                "statusCode": 200,
                "status": "success"
            }
        )

    return await _add_fire_base_token()


# Сервисные эндпоинты для других сервисов
service = APIRouter(prefix="/profile", dependencies=[Depends(header_controller)])


@service.get("/{_id}", response_model=UserView)
@cache(expire=30)
async def user_profile(
        _id: str,
        request: Request,
):
    """Получение информации о пользователе"""
    @router_decorator(request)
    async def _user_profile():
        user = await DatabaseInterface.get_user_by_id(_id)
        return UserView.model_validate(user)

    return await _user_profile()


@service.patch("/", status_code=202)
async def update_statistic(user_id: str, field: str, request: Request, increase: bool = True):
    """Обновление статистики пользователя"""
    @router_decorator(request)
    async def _update_statistic():
        await DatabaseInterface.update_statistic(user_id, field, increase)

    return await _update_statistic()
