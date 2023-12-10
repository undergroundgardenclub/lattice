from pydash import to_list
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from env import env_database_app_url


# BASE SETUP
Base = declarative_base()
class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer(), primary_key=True)


# SESSIONS
# --- engine/bind
_sa_engine = create_async_engine(env_database_app_url())
# --- session creator
sa_sessionmaker = async_sessionmaker(_sa_engine, expire_on_commit=False)


# HELPERS
# --- http helpers for sending json
def serialize(one_or_many_models, serialize_relationships=[]):
    # --- if list
    if hasattr(one_or_many_models, '__iter__') and isinstance(one_or_many_models, str) == False:
        return list(map(lambda model: model.serialize(serialize_relationships), to_list(one_or_many_models)))
    # --- if single
    return one_or_many_models.serialize(serialize_relationships)
