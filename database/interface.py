from sqlalchemy import select, update, delete

from database.connector import async_session
from database.models import *
from endpoints.dto import UserCreateModel
from helpers.cloud_storage import CloudMediaStorageAdapter
from helpers.security import Hasher


class DatabaseInterface:
    @classmethod
    async def create_user(cls, body: UserCreateModel):
        async with async_session() as session:
            city_id = await session.execute(
                select(Cities.id).where(Cities.name == body.city)
            )
            city_id = city_id.scalar()
            user_account = UsersAccounts(
                username=body.username,
                email=body.email,
                password=Hasher.get_hash_password(body.password),
            )
            session.add(user_account)
            await session.flush()
            _id = user_account.id
            default_avatar = CloudMediaStorageAdapter.get_default_avatar()
            user_profile = UsersProfiles(
                accountId=_id,
                firstName=body.firstName,
                lastName=body.lastName,
                gender=body.gender.value,
                dateOfBirth=body.dateOfBirth,
                city_id=city_id,
                description=body.description
            )
            user_avatar = UsersAvatars(
                accountId=_id,
                mediaUrl=default_avatar
            )
            user_back_pad = UsersBackPads(
                accountId=_id,
                mediaUrl=CloudMediaStorageAdapter.get_default_back_pad()
            )
            account_statistic = AccountStatistic(
                accountId=_id,
                totalEvents=0,
                totalFriends=0
            )
            session.add_all(
                [
                    user_profile,
                    user_avatar,
                    user_back_pad,
                    account_statistic
                ]
            )
            await session.commit()
            return _id, default_avatar

    @classmethod
    async def get_user_by_id(cls, _id):
        async with async_session() as session:
            user = select(UsersAccounts).filter(UsersAccounts.id == _id)
            user = await session.execute(user)
            user = user.unique().scalars().all()
            return user[0]

    @classmethod
    async def update_user_profile(cls, _id, values_to_update, flag):
        async with async_session() as session:
            if flag:
                city = await session.execute(
                    select(Cities.id).filter(Cities.name == values_to_update.get("city"))
                )
                city = city.scalar()
                values_to_update["city_id"] = city
                del values_to_update["city"]
            del flag
            statement = (
                update(UsersProfiles)
                .values(**values_to_update)
                .where(UsersProfiles.accountId == _id)
            )
            await session.execute(statement)
            await session.commit()

    @classmethod
    async def delete_user(cls, _id):
        async with async_session() as session:
            statement = delete(UsersAccounts).filter(UsersAccounts.id == _id)
            await session.execute(statement)
            await session.commit()

    @classmethod
    async def add_new_avatar(cls, file_name, _id):
        async with async_session() as session:
            media_url = CloudMediaStorageAdapter.get_media_prefix(file_name, avatar=True)
            new_avatar = UsersAvatars(
                accountId=_id,
                mediaUrl=media_url
            )
            session.add(new_avatar)
            await session.commit()
            return media_url

    @classmethod
    async def delete_avatar(cls, avatar_id, org_id):
        async with async_session() as session:
            statement = delete(UsersAvatars).filter(
                UsersAvatars.id == avatar_id,
                UsersAvatars.accountId == org_id
            ).returning(UsersAvatars.mediaUrl)
            link = await session.execute(statement)
            link = link.scalar()
            await session.execute(statement)
            query = (
                select(UsersAvatars.mediaUrl).filter(UsersAvatars.accountId == org_id)
                .order_by(UsersAvatars.created_at.desc())
            )
            new_link = await session.execute(query)
            new_link = new_link.scalars().first()
            try:
                CloudMediaStorageAdapter.delete_avatar(link)
            except IndexError:
                pass
            finally:
                await session.commit()
            return new_link

    @classmethod
    async def update_back_pad(cls, file_name, _id):
        async with async_session() as session:
            old_link = (
                select(UsersBackPads.mediaUrl)
                .filter(UsersBackPads.accountId == _id)
            )
            old_link = await session.execute(old_link)
            old_link = old_link.scalar()
            CloudMediaStorageAdapter.delete_back_pad(old_link)
            media_url = CloudMediaStorageAdapter.get_media_prefix(file_name, back_pad=True)
            new_back_pad = (
                update(UsersBackPads)
                .filter(UsersBackPads.accountId == _id)
                .values(mediaUrl=media_url)
            )
            await session.execute(new_back_pad)
            await session.commit()
            return media_url

    @classmethod
    async def drop_user(cls, _id):
        async with async_session() as session:
            await session.execute(
                delete(UsersAccounts).filter(UsersAccounts.id == _id)
            )
            await session.commit()

    @classmethod
    async def check_username(cls, username):
        async with async_session() as session:
            username_is_existed = (select(UsersAccounts.id)
                                   .filter(UsersAccounts.username == username))
            username_is_existed = await session.execute(username_is_existed)
            username_is_existed = username_is_existed.scalar()
            if username_is_existed:
                return False
            else:
                return True

    @classmethod
    async def update_statistic(cls, user_id, field, increase):
        async with async_session() as session:
            if field == "events":
                current_value = (select(
                    AccountStatistic.totalEvents)
                    .filter(AccountStatistic.accountId == user_id)
                )
                current_value = await session.execute(current_value)
                current_value = current_value.scalar()
                if increase:
                    await session.execute(
                        update(AccountStatistic).values(
                            totalEvents=current_value + 1
                        ).filter(AccountStatistic.accountId == user_id)
                    )
                else:
                    await session.execute(
                        update(AccountStatistic).values(
                            totalEvents=current_value - 1
                        ).filter(AccountStatistic.accountId == user_id)
                    )
            elif field == "friends":
                current_value = (
                    select(AccountStatistic.totalFriends)
                    .filter(AccountStatistic.accountId == user_id)
                )
                current_value = await session.execute(current_value)
                current_value = current_value.scalar()
                if increase:
                    await session.execute(
                        update(AccountStatistic).values(
                            totalFriends=current_value + 1
                        ).filter(AccountStatistic.accountId == user_id)
                    )
                else:
                    await session.execute(
                        update(AccountStatistic).values(
                            totalFriends=current_value - 1
                        ).filter(AccountStatistic.accountId == user_id)
                    )
            await session.commit()
