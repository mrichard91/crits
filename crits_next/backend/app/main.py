from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.scalars import JSON

app = FastAPI(title="CRITs Next API")

class User(BaseModel):
    id: str
    email: str
    preferences: Dict[str, str] = {}
    permissions: List[str] = []


users_db: Dict[str, User] = {}


@app.post("/auth/google")
async def auth_google(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    uid = idinfo["sub"]
    email = idinfo.get("email", "")
    user = users_db.get(uid)
    if not user:
        user = User(id=uid, email=email)
        users_db[uid] = user
    return user


@strawberry.type
class UserType:
    id: str
    email: str
    preferences: JSON
    permissions: List[str]


def list_users() -> List[UserType]:
    return [UserType(id=u.id, email=u.email, preferences=u.preferences, permissions=u.permissions) for u in users_db.values()]


def mutate_preferences(id: str, preferences: JSON) -> UserType:
    user = users_db.get(id)
    if not user:
        raise ValueError("User not found")
    user.preferences = preferences
    return UserType(id=user.id, email=user.email, preferences=user.preferences, permissions=user.permissions)


def mutate_permissions(id: str, permissions: List[str]) -> UserType:
    user = users_db.get(id)
    if not user:
        raise ValueError("User not found")
    user.permissions = permissions
    return UserType(id=user.id, email=user.email, preferences=user.preferences, permissions=user.permissions)


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

