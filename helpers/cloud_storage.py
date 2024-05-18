import enum
import logging

import boto3
from boto3.exceptions import Boto3Error

from config import settings

logger = logging.getLogger(__name__)


class Buckets(enum.Enum):
    avatars = settings.BUCKET_NAME_AVATARS
    back_pads = settings.BUCKET_NAME_BACK_PADS


class CloudMediaStorageAdapter:

    """Класс для работы с S3 хранилищем"""

    _access_key = settings.SELECTEL_S3_ACCESS_KEY
    _secret_key = settings.SELECTEL_S3_SECRET_KEY
    _avatars_link = settings.AVATARS_LINK
    _back_pads_link = settings.BACK_PADS_LINK
    _s3 = boto3.client("s3", endpoint_url="https://s3.storage.selcloud.ru",
                       region_name="ru-1",
                       aws_access_key_id=_access_key, aws_secret_access_key=_secret_key)

    @classmethod
    def get_media_prefix(cls, key: str, avatar: bool = False, back_pad: bool = False) -> str:
        if avatar:
            return f"{cls._avatars_link}/{key}"
        if back_pad:
            return f"{cls._back_pads_link}/{key}"

    @classmethod
    def get_default_avatar(cls):
        return f"{cls._avatars_link}/default-avatar-dark.png"

    @classmethod
    def get_default_back_pad(cls):
        return f"{cls._back_pads_link}/default-back-pad-dark.png"

    @classmethod
    def delete_avatar(cls, link: str):
        key = link.replace(f"{cls._avatars_link}/", "")
        if key == "default-avatar-dark.png":
            return
        try:
            cls._s3.delete_object(
                Bucket=Buckets.avatars.value,
                Key=key
            )
        except Boto3Error as e:
            logger.exception(e)

    @classmethod
    def delete_back_pad(cls, link: str):
        key = link.replace(f"{cls._back_pads_link}/", "")
        if key == "default-back-pad-dark.png":
            return
        try:
            cls._s3.delete_object(
                Bucket=Buckets.back_pads.value,
                Key=key
            )
        except Boto3Error as e:
            logger.exception(e)


class AvatarsUploader(CloudMediaStorageAdapter):
    __bucket = settings.BUCKET_NAME_AVATARS

    @classmethod
    def upload_avatar(cls, file_: bytes, file_name: str):
        try:
            cls._s3.put_object(Bucket=cls.__bucket, Key=file_name, Body=file_)
        except Boto3Error as e:
            logger.exception(e)


class BackPadsUploader(CloudMediaStorageAdapter):
    __bucket = settings.BUCKET_NAME_BACK_PADS

    @classmethod
    def upload_back_pads(cls, file_: bytes, file_name: str):
        try:
            cls._s3.put_object(Bucket=cls.__bucket, Key=file_name, Body=file_)
        except Boto3Error as e:
            logger.exception(e)


