from data.info import database

import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = sq.Column(sq.Integer, primary_key=True)
    sex = sq.Column(sq.Integer, nullable=False)
    age_from = sq.Column(sq.Integer, nullable=False)
    age_to = sq.Column(sq.Integer, nullable=False)
    city = sq.Column(sq.Integer, nullable=False)
    status = sq.Column(sq.Integer, nullable=False)


class Search(Base):
    __tablename__ = 'search'
    user_id = sq.Column(sq.Integer, nullable=False,)
    vk_id = sq.Column(sq.Integer, nullable=False)
    showed = sq.Column(sq.Boolean, default=False)

    __table_args__ = (
    sq.PrimaryKeyConstraint(user_id, vk_id),
    sq.ForeignKeyConstraint(['user_id'], ['users.id'])
    )


class Likes(Base):
    __tablename__ = 'likes'
    user_id = sq.Column(sq.Integer, nullable=False,)
    vk_id = sq.Column(sq.Integer, nullable=False)

    __table_args__ = (
    sq.PrimaryKeyConstraint(user_id, vk_id),
    sq.ForeignKeyConstraint(['user_id'], ['users.id'])
    )


class Blacklist(Base):
    __tablename__ = 'blacklist'
    user_id = sq.Column(sq.Integer, nullable=False,)
    vk_id = sq.Column(sq.Integer, nullable=False)

    __table_args__ = (
    sq.PrimaryKeyConstraint(user_id, vk_id),
    sq.ForeignKeyConstraint(['user_id'], ['users.id'])
    )


def create_connect():

    engine_path = f"postgresql+psycopg2://{database['owner']}:" \
                  f"{database['pass']}@localhost:5432/" \
                  f"{database['name']}"

    driver = sq.create_engine(engine_path)
    session = Session(bind=driver)
    return session, driver


def create_table():
    driver = create_connect()[1]
    Base.metadata.create_all(driver)


if __name__ == '__main__':
    create_table()
