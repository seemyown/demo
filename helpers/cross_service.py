import logging

import httpx

from config import settings
from endpoints.dto import UserCreateModel
from helpers.cloud_storage import CloudMediaStorageAdapter


logger = logging.getLogger(__name__)


class CrossService:
    __community_service = settings.COMMUNITY_SERVICE_URL
    __community_service_token = settings.COMMUNITY_SERVICE_TOKEN

    @classmethod
    async def add_user(cls, _id, user: UserCreateModel):
        payload = {
            "id": _id,
            "username": user.username,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "mediaUrl": CloudMediaStorageAdapter.get_default_avatar(),
            "isPrime": False
        }
        headers = {
            "cross-service-token": cls.__community_service_token,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls.__community_service}/register",
                json=payload,
                headers=headers
            )
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response text: {response.text}")
            if response.status_code == 500:
                logger.error("Error while adding user to community service")
                await cls.add_user(_id, user)
