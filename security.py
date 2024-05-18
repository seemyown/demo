from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class TokenData(BaseModel):
    id: str
    username: str
    city: int
    categories: list


class Authenticator:
    __secret_key = settings.SECRET_KEY
    __algorithm = settings.ALGORITHM
    __expire_time = settings.EXPIRE_TIME

    @classmethod
    async def get_user_by_token(cls, token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exceptions = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token, cls.__secret_key, algorithms=[cls.__algorithm]
            )
            return TokenData.parse_obj(payload)
        except JWTError:
            raise credentials_exceptions
