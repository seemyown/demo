from typing import Annotated

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import status, HTTPException, Depends
from jose import jwt, JWTError

from config import settings
from endpoints.dto import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class Hasher:
    @staticmethod
    def verify_password(plain_password: str, hasher_password: str) -> bool:
        return pwd_context.verify(plain_password, hasher_password)

    @staticmethod
    def get_hash_password(password: str) -> str:
        return pwd_context.hash(password)


class Authenticator:
    __secret_key = settings.SECRET_KEY
    __algorithm = settings.ALGORITHM
    __expire_time = settings.EXPIRE_TIME

    @classmethod
    def get_user_by_token(cls, token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exceptions = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                cls.__secret_key,
                algorithms=[cls.__algorithm]
            )
            return TokenData.model_dump(payload)
        except JWTError:
            raise credentials_exceptions
