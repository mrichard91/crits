from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Query:
    hello: str = "Hello, CRITs Next!"

schema = strawberry.Schema(query=Query)

graphql_app = GraphQLRouter(schema)

app = FastAPI(title="CRITs Next API")
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def read_root():
    return {"message": "Welcome to CRITs Next"}

