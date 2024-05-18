import datetime
import uuid
from typing import Annotated
from uuid import UUID

import pandas as pd
import sqlalchemy.orm
from sqlalchemy import String, ForeignKey, Table, MetaData, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
import enum

from database.connector import engine, async_session

intpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
uuidpk = Annotated[UUID, mapped_column(primary_key=True, default=uuid.uuid4)]
created_at = Annotated[datetime.datetime, mapped_column(default=datetime.datetime.utcnow)]
updated_at = Annotated[datetime.datetime, mapped_column(default=datetime.datetime.utcnow,
                                                        onupdate=datetime.datetime.utcnow)]
str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    type_annotation_map = {str_256: String(200)}


class FederalDistricts(Base):
    """Таблица федеральных округов"""
    __tablename__ = "federal_districts"

    id: Mapped[intpk]
    name: Mapped[str]

    regions: Mapped[list["Regions"]] = relationship(
        back_populates="district"
    )
    cities: Mapped[list["Cities"]] = relationship(
        back_populates="federal_district"
    )


class Regions(Base):
    """Таблица регионов"""
    __tablename__ = "regions"

    id: Mapped[intpk]
    name: Mapped[str]
    federal_district_id: Mapped[int] = mapped_column(ForeignKey("federal_districts.id",
                                                                ondelete="CASCADE"))

    district: Mapped["FederalDistricts"] = relationship(
        back_populates="regions"
    )
    cities: Mapped[list["Cities"]] = relationship(
        back_populates="region"
    )


class Cities(Base):
    """Таблица городов"""
    __tablename__ = "cities"

    id: Mapped[intpk]
    name: Mapped[str]
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id",
                                                      ondelete="CASCADE"))
    federal_district_id: Mapped[int] = mapped_column(ForeignKey("federal_districts.id",
                                                                ondelete="CASCADE"))

    region: Mapped["Regions"] = relationship(
        back_populates="cities"
    )

    federal_district: Mapped["FederalDistricts"] = relationship(
        back_populates="cities",
        lazy="joined"
    )

    user_city: Mapped["UsersProfiles"] = relationship(
        back_populates="city"
    )


class Categories(Base):
    """Таблица категорий"""
    __tablename__ = "categories"

    id: Mapped[intpk]
    categoryName: Mapped[str]

    user_categories: Mapped["UsersFavouritesCategories"] = relationship(
        back_populates="categories"
    )


class UsersAccounts(Base):
    """Таблица аккаунтов пользователей"""
    __tablename__ = "users_accounts"

    id: Mapped[uuidpk]
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str]
    isOpenAccount: Mapped[bool] = mapped_column(default=True)
    primeStatus: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[created_at]

    profile: Mapped["UsersProfiles"] = relationship(
        back_populates="account",
        lazy="joined"
    )

    usersAvatars: Mapped[list["UsersAvatars"]] = relationship(
        back_populates="account",
        lazy="joined",
        order_by="UsersAvatars.created_at.desc()"
    )

    usersBackPad: Mapped["UsersBackPads"] = relationship(
        back_populates="account",
        lazy="joined"
    )

    categories: Mapped[list["UsersFavouritesCategories"]] = relationship(
        back_populates="account",
        lazy="joined"
    )

    accountStatistic: Mapped["AccountStatistic"] = relationship(
        back_populates="account",
        lazy="joined"
    )


class Gender(str, enum.Enum):
    male = "m"
    female = "f"


class UsersProfiles(Base):
    """Таблица профилей пользователей"""
    __tablename__ = "users_profiles"

    id: Mapped[intpk]
    accountId: Mapped[UUID] = mapped_column(ForeignKey("users_accounts.id", ondelete="CASCADE"))
    firstName: Mapped[str]
    lastName: Mapped[str]
    description: Mapped[str]
    gender: Mapped[Gender]
    dateOfBirth: Mapped[datetime.date]
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))

    account: Mapped["UsersAccounts"] = relationship(
        back_populates="profile"
    )

    city: Mapped["Cities"] = relationship(
        back_populates="user_city",
        lazy="joined"
    )

    @property
    def age(self):
        if self.dateOfBirth:
            today = datetime.date.today()
            age = today.year - self.dateOfBirth.year - (
                        (today.month, today.day) < (self.dateOfBirth.month, self.dateOfBirth.day))
            return age
        else:
            return None


class UsersFavouritesCategories(Base):
    """Таблица категорий пользователей"""
    __tablename__ = "users_favourites_categories"

    accountId: Mapped[UUID] = mapped_column(ForeignKey("users_accounts.id", ondelete="CASCADE"),
                                            primary_key=True)
    categoryId: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"),
                                            primary_key=True)

    account: Mapped["UsersAccounts"] = relationship(
        back_populates="categories"
    )

    categories: Mapped[list["Categories"]] = relationship(
        back_populates="user_categories",
        lazy="joined"
    )


class Media(object):
    id: Mapped[intpk]
    mediaUrl: Mapped[str]
    created_at: Mapped[created_at]


class UsersAvatars(Media, Base):
    """Таблица аватаров пользователей"""
    __tablename__ = "users_avatars"

    accountId: Mapped[UUID] = mapped_column(ForeignKey("users_accounts.id", ondelete="CASCADE"))

    account: Mapped["UsersAccounts"] = relationship(
        back_populates="usersAvatars"
    )


class UsersBackPads(Media, Base):
    """Таблица подложек профилей пользователей"""
    __tablename__ = "users_back_pads"

    accountId: Mapped[UUID] = mapped_column(ForeignKey("users_accounts.id", ondelete="CASCADE"))

    account: Mapped["UsersAccounts"] = relationship(
        back_populates="usersBackPad"
    )


class AccountStatistic(Base):
    """Таблица статистики аккаунтов"""
    __tablename__ = "account_statistics"

    id: Mapped[intpk]
    accountId: Mapped[UUID] = mapped_column(ForeignKey("users_accounts.id", ondelete="CASCADE"))
    totalEvents: Mapped[int]
    totalFriends: Mapped[int]

    account: Mapped["UsersAccounts"] = relationship(
        back_populates="accountStatistic"
    )


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    data = pd.read_sql("select count(*) from federal_districts", engine)
    if data.empty:
        fed_dists = pd.read_csv(
            "./source/federal_districts.csv", low_memory=False
        ).to_dict("records")
        regions = pd.read_csv(
            "./source/regions.csv", low_memory=False
        ).to_dict("records")
        cities = pd.read_csv(
            "./source/cities.csv", low_memory=False
        ).to_dict("records")

        districts_tables = []
        for fed_dist in fed_dists:
            districts_tables.append(FederalDistricts(**fed_dist))
        regions_tables = []
        for region in regions:
            regions_tables.append(Regions(**region))
        cities_tables = []
        for city in cities:
            cities_tables.append(Cities(**city))

        async with async_session() as session:
            session.add_all(districts_tables)
            await session.flush()
            session.add_all(regions_tables)
            await session.flush()
            session.add_all(cities_tables)
            await session.commit()





