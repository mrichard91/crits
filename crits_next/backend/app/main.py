import os
from typing import List

import strawberry
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from strawberry.fastapi import GraphQLRouter
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from sqlmodel import Session, select

from .models import User, create_db_and_tables, get_session

@strawberry.type
class Query:
    hello: str = "Hello, CRITs Next!"

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI(title="CRITs Next API")
app.include_router(graphql_app, prefix="/graphql")

# Session management for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "change-me"))

# Configure OAuth for Google
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Initialize the database
create_db_and_tables()


@app.get("/")
async def read_root():
    return {"message": "Welcome to CRITs Next"}


@app.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, session: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo") or {}
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not available")

    statement = select(User).where(User.email == email)
    user = session.exec(statement).one_or_none()
    if not user:
        user = User(
            email=email,
            name=user_info.get("name"),
            preferences={},
            permissions=[],
            is_admin=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse("/")


def _get_current_user(request: Request, session: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@app.get("/users/me", response_model=User)
def users_me(request: Request, session: Session = Depends(get_session)):
    return _get_current_user(request, session)


@app.get("/users", response_model=List[User])
def list_users(request: Request, session: Session = Depends(get_session)):
    current = _get_current_user(request, session)
    if not current.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return session.exec(select(User)).all()


@app.patch("/users/{user_id}", response_model=User)
def update_user(
    user_id: int,
    data: dict,
    request: Request,
    session: Session = Depends(get_session),
):
    current = _get_current_user(request, session)
    if not current.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "preferences" in data:
        user.preferences = data["preferences"]
    if "permissions" in data:
        user.permissions = data["permissions"]

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

