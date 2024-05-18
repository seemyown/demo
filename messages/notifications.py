from pydantic import BaseModel


class NotificationMessage(BaseModel):
    userId: str


class DropUser(NotificationMessage):
    target: str = "drop_user"
