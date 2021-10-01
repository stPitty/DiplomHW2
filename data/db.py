from info import database

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
    search_list = sq.Column(sq.String, default='[]')
    black_list = sq.Column(sq.String, default='[]')
    likes_list = sq.Column(sq.String, default='[]')


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
