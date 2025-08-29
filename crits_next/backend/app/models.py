from typing import Optional, List, Dict

from sqlmodel import SQLModel, Field, create_engine, Session
from sqlalchemy import Column, JSON


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    name: Optional[str] = None
    preferences: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_admin: bool = False


database_url = "sqlite:///./users.db"
engine = create_engine(database_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
