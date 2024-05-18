from passlib.context import CryptContext

context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hasher:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        return context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str):
        return context.hash(password)