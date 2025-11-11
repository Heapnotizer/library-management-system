from typing import Union
from contextlib import asynccontextmanager
from api.db.session import init_db
from fastapi import FastAPI
from api.v1.books.routing import router as books_router
from api.v1.authors.routing import router as authors_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # before app startup up
    init_db()
    yield
    # clean up

app = FastAPI(lifespan=lifespan)
app.include_router(books_router, prefix="/api/v1/books")
app.include_router(authors_router, prefix="/api/v1/authors")

@app.get("/health")
def read_health():
    return {"status": "ok"}