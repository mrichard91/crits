from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import os
import json
import sqlite3
import requests
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.scalars import JSON

app = FastAPI(title="CRITs Next API")

DB_PATH = os.environ.get("DATABASE_PATH", "/data/users.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT,
        preferences TEXT,
        permissions TEXT
    )
    """
)
conn.commit()


class User(BaseModel):
    id: str
    email: str
    preferences: Dict[str, str] = {}
    permissions: List[str] = []


def get_user(uid: str) -> User | None:
    cur.execute(
        "SELECT id, email, preferences, permissions FROM users WHERE id=?",
        (uid,),
    )
    row = cur.fetchone()
    if row:
        return User(
            id=row[0],
            email=row[1],
            preferences=json.loads(row[2] or "{}"),
            permissions=json.loads(row[3] or "[]"),
        )
    return None


def save_user(user: User) -> None:
    cur.execute(
        """
        INSERT OR REPLACE INTO users (id, email, preferences, permissions)
        VALUES (?, ?, ?, ?)
        """,
        (
            user.id,
            user.email,
            json.dumps(user.preferences),
            json.dumps(user.permissions),
        ),
    )
    conn.commit()


GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")


@app.post("/auth/github")
async def auth_github(code: str):
    try:
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise ValueError("No access token returned")
        user_res = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_res.raise_for_status()
        user_json = user_res.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid GitHub code")

    uid = str(user_json.get("id"))
    email = user_json.get("email") or ""
    user = get_user(uid)
    if not user:
        user = User(id=uid, email=email)
    save_user(user)
    return user


@strawberry.type
class UserType:
    id: str
    email: str
    preferences: JSON
    permissions: List[str]


def list_users() -> List[UserType]:
    cur.execute("SELECT id, email, preferences, permissions FROM users")
    rows = cur.fetchall()
    return [
        UserType(
            id=row[0],
            email=row[1],
            preferences=json.loads(row[2] or "{}"),
            permissions=json.loads(row[3] or "[]"),
        )
        for row in rows
    ]


def mutate_preferences(id: str, preferences: JSON) -> UserType:
    cur.execute(
        "UPDATE users SET preferences=? WHERE id=?",
        (json.dumps(preferences), id),
    )
    conn.commit()
    user = get_user(id)
    if not user:
        raise ValueError("User not found")
    return UserType(
        id=user.id,
        email=user.email,
        preferences=user.preferences,
        permissions=user.permissions,
    )


def mutate_permissions(id: str, permissions: List[str]) -> UserType:
    cur.execute(
        "UPDATE users SET permissions=? WHERE id=?",
        (json.dumps(permissions), id),
    )
    conn.commit()
    user = get_user(id)
    if not user:
        raise ValueError("User not found")
    return UserType(
        id=user.id,
        email=user.email,
        preferences=user.preferences,
        permissions=user.permissions,
    )


@strawberry.type
class Query:
    hello: str = "Hello, CRITs Next!"
    users: List[UserType] = strawberry.field(resolver=list_users)


@strawberry.type
class Mutation:
    update_preferences: UserType = strawberry.field(resolver=mutate_preferences)
    update_permissions: UserType = strawberry.field(resolver=mutate_permissions)


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def read_root():
    return {"message": "Welcome to CRITs Next"}

