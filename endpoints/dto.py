import datetime
import enum
import uuid

from pydantic import BaseModel, Field, EmailStr


class BaseView(BaseModel):

    class Config:
        from_attributes = True


class GenderType(str, enum.Enum):
    male = "m"
    female = "f"


class UserCreateModel(BaseModel):
    username: str = Field(
        "username",
        min_length=4,
        pattern=r"^[a-zA-Z_.0-9]+$"
    )
    password: str = Field(
        "password",
        min_length=4,
        pattern=r"^[a-zA-Z_.0-9&^#!]+$"
    )
    email: EmailStr = Field(
        min_length=5
    )
    firstName: str = Field(
        "John",
        min_length=2,
        pattern=r"^[а-яёЁА-Яa-zA-Z\-]+$"
    )
    lastName: str = Field(
        "Doe",
        min_length=2,
        pattern=r"^[а-яёЁА-Яa-zA-Z\-]+$"
    )
    gender: GenderType = Field(
        "m"
    )
    dateOfBirth: datetime.date
    city: str = Field(
        "Ростов-на-Дону",
        min_length=2
    )
    description: str
    firebaseToken: str = Field(
        "firebase",
        min_length=6
    )


class City(BaseView):
    name: str


class UserProfile(BaseView):
    firstName: str
    lastName: str
    age: int
    city: City
    description: str


class Media(BaseView):
    id: int
    mediaUrl: str
    created_at: datetime.datetime


class UsersAvatars(Media):
    pass


class UsersBackPads(Media):
    pass


class UsersAccountStatistic(BaseView):
    totalEvents: int = 0
    totalFriends: int = 0


class UserView(BaseView):
    id: uuid.UUID
    username: str
    profile: UserProfile
    usersAvatars: list[UsersAvatars]
    usersBackPad: UsersBackPads
    accountStatistic: UsersAccountStatistic


class UpdateUsersView(BaseModel):
    username: str | None = None
    firstName: str = None
    lastName: str = None
    city: str = None
    description: str = None


class TokenData(BaseModel):
    id: str
    username: str
    city: int
    categories: list


class EmailSenderData(BaseModel):
    email: str
    target: str
    username: str = None
    verification_code: str


class FirebaseToken(BaseModel):
    target: str
    firebaseToken: str
    username: str
    userId: str
    mediaUrl: str | None = None


class AppendDevice(BaseModel):
    token: str


class UpdateAvatar(BaseModel):
    userId: str
    newMediaUrl: str
    target: str

